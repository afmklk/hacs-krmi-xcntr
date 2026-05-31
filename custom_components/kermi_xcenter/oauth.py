import base64
import hashlib
import secrets
import urllib.parse

from .const import AUTH_URL


class KermiOAuth:
    CLIENT_ID = "XCenterUI"

    SCOPES = [
        "openid",
        "email",
        "profile",
        "offline_access",
        "kermi.xcenter",
        "kermi.webcrm",
    ]

    def generate_pkce(self):
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()

        return verifier, challenge

    def build_auth_url(self, redirect_uri, state, challenge):
        return (
            f"{AUTH_URL}?"
            + urllib.parse.urlencode(
                {
                    "client_id": self.CLIENT_ID,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": " ".join(self.SCOPES),
                    "state": state,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "ui_locales": "de-DE",
                }
            )
        )