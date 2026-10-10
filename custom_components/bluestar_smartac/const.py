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

# Vertical Swing Mappings:
# 0: Off / Fixed
# 1-5: Fixed Level Louver Angles L1-L5
# 6: Auto Continuous Swing (oscillates top to bottom and bottom to top)
SWING_OFF = "off"
SWING_AUTO = "auto"
SWING_LEVEL_1 = "1"
SWING_LEVEL_2 = "2"
SWING_LEVEL_3 = "3"
SWING_LEVEL_4 = "4"
SWING_LEVEL_5 = "5"

SWING_MODES = [SWING_OFF, SWING_AUTO, SWING_LEVEL_1, SWING_LEVEL_2, SWING_LEVEL_3, SWING_LEVEL_4, SWING_LEVEL_5]

BS_TO_HA_SWING = {
    0: SWING_OFF,
    6: SWING_AUTO,
    1: SWING_LEVEL_1,
    2: SWING_LEVEL_2,
    3: SWING_LEVEL_3,
    4: SWING_LEVEL_4,
    5: SWING_LEVEL_5,
}

HA_TO_BS_SWING = {
    SWING_OFF: 0,
    SWING_AUTO: 6,
    SWING_LEVEL_1: 1,
    SWING_LEVEL_2: 2,
    SWING_LEVEL_3: 3,
    SWING_LEVEL_4: 4,
    SWING_LEVEL_5: 5,
}

# Horizontal Swing (0: Off, 6: On)
SWING_HORIZONTAL_OFF = "off"
SWING_HORIZONTAL_ON = "on"
SWING_HORIZONTAL_MODES = [SWING_HORIZONTAL_OFF, SWING_HORIZONTAL_ON]

BS_TO_HA_SWING_H = {
    0: SWING_HORIZONTAL_OFF,
    6: SWING_HORIZONTAL_ON,
}

HA_TO_BS_SWING_H = {
    SWING_HORIZONTAL_OFF: 0,
    SWING_HORIZONTAL_ON: 6,
}

# 5-in-1 / 6-in-1 Convertible Eco Capacity Preset Modes:
# 0 = Off/Default, 1 = 100%, 2 = 80%, 3 = 60%, 4 = 40%, 5 = 110% (Hyper / Extra Cool)
ECO_OFF = "Off (Default)"
ECO_110 = "110% (Super Cool)"
ECO_100 = "100%"
ECO_80 = "80%"
ECO_60 = "60%"
ECO_40 = "40%"

ECO_OPTIONS = [ECO_OFF, ECO_110, ECO_100, ECO_80, ECO_60, ECO_40]

BS_TO_ECO = {
    0: ECO_OFF,
    1: ECO_100,
    2: ECO_80,
    3: ECO_60,
    4: ECO_40,
    5: ECO_110,
}

ECO_TO_BS = {
    ECO_OFF: 0,
    ECO_110: 5,
    ECO_100: 1,
    ECO_80: 2,
    ECO_60: 3,
    ECO_40: 4,
}

# Error code mappings
ERROR_CODES = {
    0: "None",
    1: "E1 - Indoor Room Sensor Failure",
    2: "E2 - Indoor Coil Sensor Failure",
    3: "E3 - Outdoor Coil Sensor Failure",
    4: "E4 - Outdoor Ambient Sensor Failure",
    5: "E5 - Indoor Fan Motor Error",
    6: "EC - Refrigerant Leakage Detected",
    7: "E6 - Communication Fault",
    8: "F1 - Inverter Module IPM Fault",
    9: "F2 - Compressor Overcurrent / Stall",
    10: "F3 - High Discharge Pipe Temp",
    11: "P1 - High Voltage Protection",
    12: "P2 - Low Voltage Protection",
}
