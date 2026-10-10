# Blue Star Smart AC for Home Assistant (HACS Integration)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A native Home Assistant custom integration for **Blue Star Smart ACs** (reverse-engineered from the official `com.bluestarindia.bluesmart` Android application).

No external bridges, Python daemons, or separate MQTT servers required — everything runs natively inside Home Assistant with full real-time cloud push telemetry!

---

## 🌟 Key Features

- **Native UI Setup**: Add directly from **Settings > Devices & Services > Add Integration** — just enter your Blue Star mobile number/email and password.
- **Sub-Second Bi-Directional Cloud Push**: Uses direct AWS IoT Core MQTT WebSockets streaming. Any change made via the physical IR remote or Blue Star app reflects in Home Assistant in `< 0.8s`.
- **Full Climate Control**:
  - HVAC Modes: `cool`, `dry`, `fan_only`, `auto`, `off`.
  - Target temperature control with 1°C precision (`16°C` – `30°C`).
  - Fan speeds: `low`, `medium`, `high`, `turbo`, `auto`.
  - **Vertical Louver Swing**: Both full **`auto`** continuous oscillation (top-to-bottom) and 5 step-by-step fixed angles (`1` to `5`), plus `off`.
- **Selects**:
  - **Eco Capacity Mode**: Dropdown selector for 5-in-1 / 6-in-1 convertible capacity tiers (`Off (Default)`, `110% (Super Cool)`, `100%`, `80%`, `60%`, `40%`).
- **Sensors**:
  - Current Room Temperature (from AC ambient thermistor).
  - Target Temperature.
  - Total Compressor Run Hours.
  - WiFi RSSI Signal Strength.
  - **Diagnostic Error Code**: Real-time hardware/sensor fault diagnostics (e.g. `None`, `E1`, `EC`).
  - **Eco Capacity Level**: Active capacity tier indicator.
- **Switches**:
  - **Comfort Sleep Mode Switch**: Automatically adjusts cooling temperature curve through the night for optimal sleep comfort and energy savings.
  - **Self Clean Mode Switch**: Runs an automated coil cleaning and moisture removal cycle to eliminate dust and mold.
  - **Horizontal Swing Switch**: Toggle continuous left-right motorized oscillation.
  - **Eco Mode Switch**: Quick on/off toggle for Eco mode.
  - **LED Display Toggle**: Turn indoor unit front panel temperature display ON/OFF.
  - **Turbo Mode Switch**: Instant powerful cooling boost.
  - **Buzzer Beep Toggle**: Enable or mute remote confirmation beeps.
- **Auto Multi-Unit Discovery**: Automatically registers all ACs tied to your Blue Star account.

---

## 📦 Installation via HACS

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant.
2. In Home Assistant, open **HACS** > **Integrations**.
3. Click the three dots in the top right corner > **Custom repositories**.
4. Paste this repository URL:
   ```text
   https://github.com/ArjunVRa/bluestar_smartac
   ```
5. Select Category: **Integration** and click **Add**.
6. Find **Blue Star Smart AC** and click **Download**.
7. **Restart Home Assistant**.

---

## ⚙️ Configuration

1. In Home Assistant, go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **Blue Star Smart AC**.
3. Enter your account details:
   - **Phone Number or Email**: e.g., `9176425917` (without country code if Indian mobile).
   - **Password**: Your Blue Star Smart app password.
   - **Account is an Email**: Check only if your account login ID is an email address.
4. Click **Submit**. Your AC units will be detected automatically and organized by device and area!

---

## 📋 Architecture & Reverse-Engineering Details

This integration directly interfaces with Blue Star's AWS IoT Core infrastructure:
1. Authenticates against `https://api-smart.bluestarindia.com/auth/login`.
2. Extracts temporary AWS IAM credentials (`AccessKey`, `SecretKey`) and AWS IoT endpoint (`a26381dl7mudo4-ats.iot.ap-south-1.amazonaws.com`).
3. Establishes a SigV4-signed WebSocket connection to AWS IoT Core MQTT.
4. Subscribes to `things/<thing_id>/state/reported` for instant telemetry.
5. Updates the AC state by writing to the AWS IoT Thing Shadow (`$aws/things/<thing_id>/shadow/update`) matching the exact payload and metadata format expected by the ESP32 firmware (`v0.5.7`).

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
