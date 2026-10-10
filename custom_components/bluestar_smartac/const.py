"""Constants for Blue Star Smart AC integration."""

DOMAIN = "bluestar_smartac"
API_BASE = "https://api-smart.bluestarindia.com"

CONF_AUTH_ID = "auth_id"
CONF_PASSWORD = "password"
CONF_IS_EMAIL = "is_email"

# Blue Star Modes -> Home Assistant HVACMode
# 0: Fan, 2: Cool, 3: Dry, 4: Auto
BS_TO_HA_MODE = {
    0: "fan_only",
    2: "cool",
    3: "dry",
    4: "auto",
}

HA_TO_BS_MODE = {
    "fan_only": (1, 0),
    "cool": (1, 2),
    "dry": (1, 3),
    "auto": (1, 4),
}

# Fan Speed Mappings: 2: Low, 3: Med, 4: High, 6: Turbo, 7: Auto
BS_TO_HA_FAN = {
    2: "low",
    3: "medium",
    4: "high",
    6: "turbo",
    7: "auto",
}

HA_TO_BS_FAN = {
    "low": 2,
    "medium": 3,
    "high": 4,
    "turbo": 6,
    "auto": 7,
}
