import logging
import re
from urllib.parse import urljoin
from .wellknown import WELLKNOWN_PREFIXES

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class KermiApi:
    def __init__(self, session, token_store, installation_id):
        self.session = session
        self.token_store = token_store
        self.installation_id = installation_id

    async def _headers(self):
        token = await self.token_store.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        }

    async def get_wellknown_datapoints_js(self):
        candidate_pages = [
            "https://portal.kermi.com/XCenterUI/remotecontrolnew/de/DE",
            #"https://portal.kermi.com/XCenterUI/remotecontrol/de/DE",
        ]

        script_urls = []

        for page_url in candidate_pages:
            try:
                html = await self._get_text_unauthenticated(page_url)
            except Exception:
                _LOGGER.debug(
                    "Failed loading Kermi page for JS discovery: %s",
                    page_url,
                )
                continue

            script_urls.extend(
                _extract_generated_script_urls(page_url, html)
            )

        script_urls.extend(
            [
                "https://portal.kermi.com/XCenterUI/remotecontrolnew/generated/wellknown-datapoints-BE2r4Sgi.js",
                "https://portal.kermi.com/XCenterUI/remotecontrol/generated/wellknown-datapoints-BE2r4Sgi.js",
            ]
        )

        seen = set()
        script_urls = [
            url for url in script_urls
            if not (url in seen or seen.add(url))
        ]

        best_text = ""
        best_url = None
        best_score = 0

        for url in script_urls:
            try:
                text = await self._get_text_unauthenticated(url)
            except Exception:
                _LOGGER.debug("Failed loading Kermi JS candidate: %s", url)
                continue

            score = _score_wellknown_js(text)

            _LOGGER.debug(
                "Kermi JS candidate %s score=%s",
                url,
                score,
            )

            if score > best_score:
                best_score = score
                best_text = text
                best_url = url

        if best_text:
            _LOGGER.info(
                "Kermi well-known datapoints JS discovered: %s score=%s",
                best_url,
                best_score,
            )
            return best_text

        _LOGGER.warning(
            "No dynamic Kermi well-known datapoints JS found; using static fallback only"
        )
        return ""

    async def _get_text_unauthenticated(self, url):
        async with self.session.get(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml,text/javascript,*/*",
                "User-Agent": "Mozilla/5.0",
            },
        ) as r:
            text = await r.text()

            _LOGGER.debug(
                "Kermi unauthenticated GET %s -> %s body=%s",
                url,
                r.status,
                _safe_log_body(text),
            )

            r.raise_for_status()
            return text

    async def _post(self, url, payload=None):
        if payload is None:
            payload = {}

        for attempt in range(2):
            async with self.session.post(
                url,
                headers=await self._headers(),
                json=payload,
            ) as r:
                text = await r.text()

                _LOGGER.debug(
                    "Kermi API POST %s -> %s body=%s",
                    url,
                    r.status,
                    _safe_log_body(text),
                )

                if r.status == 401 and attempt == 0:
                    await self.token_store.refresh(force=True)
                    continue

                if r.status >= 400:
                    _LOGGER.warning(
                        "Kermi API POST failed: %s -> %s",
                        url,
                        r.status,
                    )

                r.raise_for_status()

                try:
                    return await r.json()
                except Exception:
                    return text

    async def get_favorites(self, installation_id):
        return await self._post(
            f"{API_BASE}/Favorite/GetFavorites/{installation_id}",
            {"WithDetails": True, "OnlyHomeScreen": False},
        )

    async def _get(self, url):
        for attempt in range(2):
            async with self.session.get(
                url,
                headers=await self._headers(),
            ) as r:
                text = await r.text()

                _LOGGER.debug(
                    "Kermi API GET %s -> %s body=%s",
                    url,
                    r.status,
                    _safe_log_body(text),
                )

                if r.status == 401 and attempt == 0:
                    await self.token_store.refresh(force=True)
                    continue

                if r.status >= 400:
                    _LOGGER.warning(
                        "Kermi API GET failed: %s -> %s",
                        url,
                        r.status,
                    )

                r.raise_for_status()

                try:
                    return await r.json()
                except Exception:
                    return text

    async def get_heatpump_devices(self, installation_id):
        return await self._post(
            f"{API_BASE}/Device/GetDevicesByType/{installation_id}",
            {
                "DeviceType": 2,
                "WithDetails": False,
            },
        )

    async def get_configs(
        self,
        installation_id,
        device_type,
        device_version,
        config_ids,
    ):
        return await self._post(
            f"{API_BASE}/Datapoint/GetConfigs/{installation_id}",
            {
                "DeviceType": device_type,
                "DeviceVersion": device_version,
                "DatapointConfigIds": config_ids,
                "IgnoreNotExisting": True,
            },
        )

    async def read_values(self, installation_id, datapoints):
        return await self._post(
            f"{API_BASE}/Datapoint/ReadValues/{installation_id}",
            {
                "DatapointValues": [
                    {
                        "$type": dp["type"],
                        "DatapointConfigId": dp["config_id"],
                        "DeviceId": dp["device_id"],
                    }
                    for dp in datapoints
                ]
            },
        )

    async def write_value(self, installation_id, datapoint, value):
        return await self._post(
            f"{API_BASE}/Datapoint/WriteValues/{installation_id}",
            {
                "DatapointValues": [
                    {
                        "$type": datapoint["type"],
                        "DatapointConfigId": datapoint["config_id"],
                        "DeviceId": datapoint["device_id"],
                        "Flags": 0,
                        "Value": value,
                    }
                ]
            },
        )


def _extract_generated_script_urls(base_url, html):
    urls = []

    for match in re.findall(
        r'''(?:src|href)=["']([^"']+\.js)["']''',
        html or "",
    ):
        full_url = urljoin(base_url, match)

        if "/generated/" in full_url:
            urls.append(full_url)

    for match in re.findall(
        r'''["']([^"']*/generated/[^"']+\.js)["']''',
        html or "",
    ):
        urls.append(urljoin(base_url, match))

    return urls


def _score_wellknown_js(text):
    if not text:
        return 0

    score = 0
    lower = text.lower()

    if "wellknown" in lower:
        score += 10

    if "datapointconfigid" in lower:
        score += 10

    for marker in WELLKNOWN_PREFIXES:
        if marker in text:
            score += 15

    score += min(
        len(
            re.findall(
                r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                text,
            )
        ),
        200,
    )

    return score


def _safe_log_body(text):
    if not text:
        return ""

    text = str(text)

    for marker in (
        "access_token",
        "refresh_token",
        "id_token",
        "authorization",
    ):
        if marker.lower() in text.lower():
            return "<redacted token response>"

    return text[:1000]