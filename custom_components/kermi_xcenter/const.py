from homeassistant.const import Platform

DOMAIN = "kermi_xcenter"

PLATFORMS = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
]

AUTH_URL = "https://portal.kermi.com/openid/connect/authorize"
TOKEN_URL = "https://portal.kermi.com/openid/connect/token"
API_BASE = "https://portal.kermi.com/xcenterpro/api"