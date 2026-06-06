import base64
import hashlib
import secrets
import urllib.parse

from .const import AUTH_URL


class KermiOAuth:
    CLIENT_ID = "XCenterUI"
    REDIRECT_URI = "https://portal.kermi.com/xcenterui/xcenter/auth/loginCallback"

    SCOPES = [
        "openid",
        "email",
        "profile",
        "offline_access",
        "kermi.xcenter",
        "kermi.webcrm",
    ]

    def generate_pkce(self):
        verifier = secrets.token_hex(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()

        return verifier, challenge

    def build_auth_url(self, state, challenge):
        return (
            f"{AUTH_URL}?"
            + urllib.parse.urlencode(
                {
                    "client_id": self.CLIENT_ID,
                    "redirect_uri": self.REDIRECT_URI,
                    "response_type": "code",
                    "scope": " ".join(self.SCOPES),
                    "state": state,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "ui_locales": "de-DE",
                }
            )
        )

    def extract_code_and_state(self, callback_url):
        parsed = urllib.parse.urlparse(callback_url)
        query = urllib.parse.parse_qs(parsed.query)

        code = query.get("code", [None])[0]
        state = query.get("state", [None])[0]

        return code, state