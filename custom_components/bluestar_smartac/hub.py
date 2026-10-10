"""Blue Star Cloud API and AWS IoT Core Client."""
import base64
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from awscrt import io, mqtt as aws_crt_mqtt, auth
from awsiot import mqtt_connection_builder
import boto3
import requests

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class BlueStarHub:
    """Manages Blue Star Cloud Authentication and Real-Time AWS IoT MQTT Streaming."""

    def __init__(self, auth_id: str, password: str, is_email: bool = False) -> None:
        self.auth_id = auth_id
        self.password = password
        self.is_email = is_email

        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.user_name: Optional[str] = None
        self.user_id: Optional[str] = None

        self.aws_endpoint: Optional[str] = None
        self.aws_access_key: Optional[str] = None
        self.aws_secret_key: Optional[str] = None

        self.boto3_iot = None
        self.aws_mqtt_conn = None

        self.devices: Dict[str, Dict[str, Any]] = {}
        self.cached_states: Dict[str, Dict[str, Any]] = {}
        self.listeners: List[Callable[[str], None]] = []

    def _headers(self) -> Dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "com.bluestarindia.bluesmart",
            "X-APP-VER": "v5.1.2-183",
            "X-OS-NAME": "Android",
            "X-OS-VER": "14-34",
        }
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
            h["X-APP-SESSION"] = self.access_token
        return h

    def login(self) -> bool:
        """Authenticate with Blue Star Cloud and extract temporary AWS IoT credentials."""
        _LOGGER.info("Authenticating with Blue Star Cloud for %s", self.auth_id)
        url = f"{API_BASE}/auth/login"
        payload = {
            "auth_id": self.auth_id,
            "auth_type": 0 if self.is_email else 1,
            "password": self.password,
        }
        try:
            resp = self.session.post(url, json=payload, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data.get("session")
            user = data.get("user", {})
            self.user_name = user.get("name", "User")
            self.user_id = user.get("user_id")

            mi_b64 = data.get("mi", "") or user.get("mi", "")
            if mi_b64:
                parts = base64.b64decode(mi_b64).decode("utf-8").split("::")
                if len(parts) >= 3:
                    self.aws_endpoint = parts[0]
                    self.aws_access_key = parts[1]
                    self.aws_secret_key = parts[2]
                    _LOGGER.info("AWS IoT Core Endpoint: %s", self.aws_endpoint)

                    self.boto3_iot = boto3.client(
                        "iot-data",
                        region_name="ap-south-1",
                        endpoint_url=f"https://{self.aws_endpoint}",
                        aws_access_key_id=self.aws_access_key,
                        aws_secret_access_key=self.aws_secret_key,
                    )
            return True
        except Exception as err:
            _LOGGER.error("Blue Star Cloud authentication failed: %s", err)
            return False

    def fetch_devices(self) -> bool:
        """Retrieve all registered AC units and initial state."""
        url = f"{API_BASE}/things"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=15)
            if resp.status_code in (401, 403):
                if self.login():
                    resp = self.session.get(url, headers=self._headers(), timeout=15)
                else:
                    return False
            resp.raise_for_status()
            data = resp.json()
            things = data.get("things", [])
            states = data.get("states", {})

            for thing in things:
                tid = thing.get("thing_id")
                if tid:
                    self.devices[tid] = thing
                    st = states.get(tid, {})
                    is_connected = st.get("connected", True)
                    reported = st.get("reported", {})
                    if tid not in self.cached_states:
                        self.cached_states[tid] = {"connected": is_connected, "state": {}}
                    self.cached_states[tid]["connected"] = is_connected
                    self.cached_states[tid]["state"].update(reported)
                    self._notify_listeners(tid)
            return True
        except Exception as err:
            _LOGGER.error("Failed to fetch devices: %s", err)
            return False

    def init_aws_mqtt(self) -> bool:
        """Connect directly to AWS IoT Core MQTT WebSockets stream for real-time telemetry."""
        if not self.aws_endpoint or not self.aws_access_key or not self.aws_secret_key:
            return False

        try:
            credentials_provider = auth.AwsCredentialsProvider.new_static(
                self.aws_access_key, self.aws_secret_key
            )
            event_loop_group = io.EventLoopGroup(1)
            host_resolver = io.DefaultHostResolver(event_loop_group)
            client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

            self.aws_mqtt_conn = mqtt_connection_builder.websockets_with_default_aws_signing(
                endpoint=self.aws_endpoint,
                region="ap-south-1",
                credentials_provider=credentials_provider,
                client_bootstrap=client_bootstrap,
                client_id=f"ha_bluestar_{int(time.time())}",
                clean_session=True,
                keep_alive_secs=60,
            )

            connect_future = self.aws_mqtt_conn.connect()
            connect_future.result(timeout=15)
            _LOGGER.info("Connected to AWS IoT Core MQTT successfully")

            for tid in self.devices:
                self._subscribe_device(tid)
            return True
        except Exception as err:
            _LOGGER.error("AWS IoT Core MQTT connection failed: %s", err)
            return False

    def _subscribe_device(self, thing_id: str) -> None:
        if not self.aws_mqtt_conn:
            return
        topic = f"things/{thing_id}/state/reported"

        def on_telemetry(topic, payload, dup=False, qos=0, retain=False, **kwargs):
            try:
                msg = json.loads(payload.decode("utf-8"))
                tid = msg.get("udid", thing_id)
                if tid not in self.cached_states:
                    self.cached_states[tid] = {"connected": True, "state": {}}
                self.cached_states[tid]["connected"] = True
                self.cached_states[tid]["state"].update(msg)
                self._notify_listeners(tid)
            except Exception as ex:
                _LOGGER.error("Error processing live telemetry: %s", ex)

        self.aws_mqtt_conn.subscribe(topic, aws_crt_mqtt.QoS.AT_LEAST_ONCE, on_telemetry)

    def register_listener(self, callback: Callable[[str], None]) -> None:
        """Register a callback for entity state updates."""
        self.listeners.append(callback)

    def _notify_listeners(self, thing_id: str) -> None:
        for listener in self.listeners:
            try:
                listener(thing_id)
            except Exception as ex:
                _LOGGER.error("Listener error: %s", ex)

    def send_command(self, thing_id: str, updates: Dict[str, Any]) -> None:
        """Send state actuation to AWS IoT Core shadow with exact firmware required metadata."""
        now_ts = int(time.time() * 1000)
        desired = dict(updates)
        desired["src"] = "anmq"
        desired["ts"] = now_ts

        _LOGGER.info("Dispatching command to %s: %s", thing_id, desired)
        payload = json.dumps({"state": {"desired": desired}})
        try:
            if self.boto3_iot:
                self.boto3_iot.update_thing_shadow(
                    thingName=thing_id,
                    payload=payload
                )
                _LOGGER.info("Command sent via boto3 to %s successfully", thing_id)
            elif self.aws_mqtt_conn:
                self.aws_mqtt_conn.publish(
                    topic=f"$aws/things/{thing_id}/shadow/update",
                    payload=payload,
                    qos=aws_crt_mqtt.QoS.AT_LEAST_ONCE
                )
                _LOGGER.info("Command published via AWS MQTT to %s", thing_id)
            else:
                _LOGGER.warning("No AWS IoT client available to send command to %s", thing_id)
        except Exception as err:
            _LOGGER.error("Failed to send command to %s: %s", thing_id, err)

        # Optimistic local update
        if thing_id in self.cached_states:
            cached_updates = dict(updates)
            if "mode" in cached_updates and isinstance(cached_updates["mode"], dict):
                m_dict = cached_updates.pop("mode")
                cached_updates["mode"] = m_dict.get("value")
                if "stemp" in m_dict:
                    cached_updates["stemp"] = m_dict["stemp"]
                if "fspd" in m_dict:
                    cached_updates["fspd"] = m_dict["fspd"]
            cached_updates.pop("lcmd", None)
            self.cached_states[thing_id]["state"].update(cached_updates)
            self._notify_listeners(thing_id)
