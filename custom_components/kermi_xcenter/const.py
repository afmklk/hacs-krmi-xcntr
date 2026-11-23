from homeassistant.const import Platform

DOMAIN = "kermi_xcenter"

PLATFORMS = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]

AUTH_URL = "https://portal.kermi.com/openid/connect/authorize"
TOKEN_URL = "https://portal.kermi.com/openid/connect/token"
API_BASE = "https://portal.kermi.com/xcenterpro/api"
PORTALS = {
    "kermi": {
        "name": "Kermi",
        "host": "https://portal.kermi.com",
        "auth_url": "https://portal.kermi.com/openid/connect/authorize",
        "token_url": "https://portal.kermi.com/openid/connect/token",
        "api_base": "https://portal.kermi.com/xcenterpro/api",
        "client_id": "XCenterUI",
        "redirect_uri": "https://portal.kermi.com/xcenterui/xcenter/auth/loginCallback",
    },
    "heim_ag": {
        "name": "HEIM AG",
        "host": "https://kermi.heim-ag.ch",
        "auth_url": "https://kermi.heim-ag.ch/openid/connect/authorize",
        "token_url": "https://kermi.heim-ag.ch/openid/connect/token",
        "api_base": "https://kermi.heim-ag.ch/xcenterpro/api",
        "client_id": "XCenterUI",
        "redirect_uri": "https://kermi.heim-ag.ch/xcenterui/xcenter/auth/loginCallback",
    },
}
DEFAULT_PORTAL = "kermi"
DEFAULT_UPDATE_INTERVAL_MINUTES = 5
