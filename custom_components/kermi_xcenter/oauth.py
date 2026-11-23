import base64
import hashlib
import secrets
import urllib.parse

from .const import DEFAULT_PORTAL, PORTALS


class KermiOAuth:
    # Preserve the original public constants for callers that relied on them.
    CLIENT_ID = PORTALS[DEFAULT_PORTAL]["client_id"]
    REDIRECT_URI = PORTALS[DEFAULT_PORTAL]["redirect_uri"]

    SCOPES = [
        "openid",
        "email",
        "profile",
        "offline_access",
        "kermi.xcenter",
        "kermi.webcrm",
    ]

    def __init__(self, portal=DEFAULT_PORTAL):
        self.portal = PORTALS.get(portal, PORTALS[DEFAULT_PORTAL])

    def generate_pkce(self):
        verifier = secrets.token_hex(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()

        return verifier, challenge

    def build_auth_url(self, state, challenge):
        return (
            f"{self.portal['auth_url']}?"
            + urllib.parse.urlencode(
                {
                    "client_id": self.portal["client_id"],
                    "redirect_uri": self.portal["redirect_uri"],
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
