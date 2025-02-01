"""Constants for the Meltem integration."""

DOMAIN = "meltem"

# API Constants
API_HOST = "https://api.connect2myhome.eu"
API_KEY = "Xi18ypOBNZKnR30ENI4BSFeZ55E2wlhmT9czcKUV0cIjawCZJXMcu0ROd0GuoTSW"
API_AUTH_ENDPOINT = "/v1/user/auth"
API_DATA_ENDPOINT = "/v1/data"
API_BRIDGES_ENDPOINT = "/v1/bridge/list"
API_BRIDGE_DEVICES_ENDPOINT = "/v1/bridge/devices"
API_LIVE_DATA_ENDPOINT = "/v1/device/data/live"
API_SET_DATA_ENDPOINT = "/v1/device/data/set"
USER_AGENT = "meltem/113 CFNetwork/1568.300.101 Darwin/24.2.0"

# Config
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SESSION_ID = "session_id"
CONF_BRIDGES = "bridges"

# Device Types
DEVICE_TYPE_BRIDGE = "bridge"
DEVICE_TYPE_VENTILATION = "ventilation"

# Update intervals
DEFAULT_UPDATE_INTERVAL = 2  # seconds

# Ventilation Control
VENTILATION_REGISTER = 41120  # Register used to set the ventilation level
VENTILATION_STATUS_REGISTER = 41101  # Register that shows the current ventilation level
VENTILATION_SPEED_REGISTER = 41113  # Register that shows the current manual speed
VENTILATION_MANUAL_REGISTER = 41133  # Register used to set manual speed

VENTILATION_LEVELS = {
    "off": [1, 0] + [0] * 11,
    "low": [3, 228] + [0] * 11,
    "medium": [3, 229] + [0] * 11,
    "high": [3, 230] + [0] * 11,
    "manual": [3, 112] + [0] * 11,  # Manual mode
}

# Value mapping for ventilation levels
VENTILATION_VALUE_MAP = {
    0: "off",
    228: "low",
    229: "medium",
    230: "high",
    112: "manual",  # Status code for manual mode
}

# Manual ventilation speed mapping (percentage to register value)
VENTILATION_MANUAL_MIN = 10  # Minimum percentage
VENTILATION_MANUAL_MAX = 100  # Maximum percentage
VENTILATION_MANUAL_VALUES = {
    10: 4521,
    60: 25001,
    100: 41385,
}

def calculate_manual_value(percentage: int) -> int:
    """Calculate the register value for a given percentage."""
    if percentage < VENTILATION_MANUAL_MIN:
        return VENTILATION_MANUAL_VALUES[VENTILATION_MANUAL_MIN]
    if percentage > VENTILATION_MANUAL_MAX:
        return VENTILATION_MANUAL_VALUES[VENTILATION_MANUAL_MAX]

    # Find the closest reference points
    points = sorted(VENTILATION_MANUAL_VALUES.items())
    for i in range(len(points) - 1):
        p1, v1 = points[i]
        p2, v2 = points[i + 1]
        if p1 <= percentage <= p2:
            # Linear interpolation
            ratio = (percentage - p1) / (p2 - p1)
            return int(v1 + ratio * (v2 - v1))

    return VENTILATION_MANUAL_VALUES[VENTILATION_MANUAL_MAX]

# Conversion factors
VOC_PPM_TO_UGM3_FACTOR = 1962.0  # Based on isobutylene at 20°C and 1 atm

def convert_voc_ppm_to_ugm3(ppm: float) -> float:
    """Convert VOC from ppm to µg/m³."""
    return ppm * VOC_PPM_TO_UGM3_FACTOR

# Register definitions
REGISTER_DEFINITIONS = {
    41016: {
        "name": "Error Status",
        "unit": None,
        "device_class": "problem",
        "state_class": None,
        "icon": "mdi:alert-circle",
        "value_map": {0: "OK", 1: "Error"},
        "entity_category": "diagnostic",
    },
    41018: {
        "name": "Frost Protection",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:snowflake-alert",
        "value_map": {0: "Inactive", 1: "Active"},
        "entity_category": "diagnostic",
    },
    41004: {
        "name": "Exhaust Air Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-minus",
        "suggested_display_precision": 1,
    },
    41002: {
        "name": "Outdoor Air Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "suggested_display_precision": 1,
    },
    41000: {
        "name": "Extract Air Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-high",
        "suggested_display_precision": 1,
    },
    41009: {
        "name": "Supply Air Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-low",
        "suggested_display_precision": 1,
    },
    41006: {
        "name": "Extract Air Humidity",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
        "icon": "mdi:water-percent",
        "suggested_display_precision": 0,
    },
    41011: {
        "name": "Supply Air Humidity",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
        "icon": "mdi:water-percent",
        "suggested_display_precision": 0,
    },
    41007: {
        "name": "Extract Air CO2",
        "unit": "ppm",
        "device_class": "carbon_dioxide",
        "state_class": "measurement",
        "icon": "mdi:molecule-co2",
        "suggested_display_precision": 0,
    },
    41013: {
        "name": "Supply Air VOC",
        "unit": "µg/m³",
        "device_class": "volatile_organic_compounds",
        "state_class": "measurement",
        "icon": "mdi:air-filter",
        "suggested_display_precision": 0,
    },
    41020: {
        "name": "Extract Air Flow",
        "unit": "m³/h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:arrow-up-circle",
        "suggested_display_precision": 0,
    },
    41021: {
        "name": "Supply Air Flow",
        "unit": "m³/h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:arrow-down-circle",
        "suggested_display_precision": 0,
    },
    41017: {
        "name": "Filter Change Required",
        "unit": None,
        "device_class": "problem",
        "state_class": None,
        "icon": "mdi:air-filter-horizontal",
        "value_map": {0: "No", 1: "Yes"},
        "entity_category": "diagnostic",
    },
    41027: {
        "name": "Days Until Filter Change",
        "unit": "d",
        "device_class": "duration",
        "state_class": "measurement",
        "icon": "mdi:calendar-clock",
        "entity_category": "diagnostic",
        "suggested_display_precision": 0,
    },
    41030: {
        "name": "Operating Hours",
        "unit": "h",
        "device_class": "duration",
        "state_class": "total_increasing",
        "icon": "mdi:clock-outline",
        "entity_category": "diagnostic",
        "suggested_display_precision": 0,
    },
    41032: {
        "name": "Fan Motors Operating Hours",
        "unit": "h",
        "device_class": "duration",
        "state_class": "total_increasing",
        "icon": "mdi:fan-clock",
        "entity_category": "diagnostic",
        "suggested_display_precision": 0,
    },
    41120: {
        "name": "Ventilation Level Control",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:fan-speed-3",
        "value_map": {0: "Off", 228: "Low", 229: "Medium", 230: "High"},
        "entity_registry_enabled_default": False,  # This is controlled via the select entity
    },
}

# Additional registers found in live data
ADDITIONAL_REGISTERS = {
    41100: {
        "name": "Operation Mode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:cog",
        "value_map": {1: "Normal", 3: "Manual"},
        "entity_category": "diagnostic",
    },
    41101: {
        "name": "Current Ventilation Mode",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:fan",
        "value_map": {0: "Off", 228: "Low", 229: "Medium", 230: "High", 112: "Manual"},
    },
    41102: {
        "name": "Unknown Register 41102",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:help",
        "entity_registry_enabled_default": False,
    },
    41103: {
        "name": "Unknown Register 41103",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:help",
        "entity_registry_enabled_default": False,
    },
    41104: {
        "name": "Unknown Register 41104",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:help",
        "entity_registry_enabled_default": False,
    },
    41106: {
        "name": "Unknown Register 41106",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:help",
        "entity_registry_enabled_default": False,
    },
    41113: {
        "name": "Current Ventilation Speed",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:fan-speed-3",
        "value_transform": lambda value: round(0 if value == 0 else (value * 100 / 41385)),
        "suggested_display_precision": 0,
    },
    41133: {
        "name": "Manual Speed Control",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:fan-speed-3",
        "entity_registry_enabled_default": False,  # This is only used internally
    },
}

# Error messages
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_UNKNOWN = "unknown"