import re

HEATPUMP_WELLKNOWN_IDS = {
    "HP_AktuelleMotorleistungKW": "3576624b-1af4-4406-8e8b-12500acd4840",
    "HP_FanAktuelleLeistung": "7605e769-5bcf-4e37-97e4-e1cded35dc54",
    "HP_Aussentemperatur_gemittelt": "7b712484-4c0e-4b8d-9425-25f9f7072777",
    "HP_AuslasstempLadekreis": "6576ccc5-048a-482e-ac0d-ef4dc0de16c4",
    "HP_EinlasstempLadekreis": "6ca1372b-894d-4f27-add3-257fff9905c1",
    "HP_HeatpumpState": "41258683-9b38-4065-80d2-34c9a7e6ec2c",
    "HP_TWETempIst": "83a34595-924a-421e-b9c1-44c2a49f97ad",
    "HP_FixwertHK3": "f3712586-33f3-41e6-9b11-20f1e7a1a363",
    "HP_HeatOutput": "1d86a071-53bc-4ab1-b705-1e9c7c104d02",
    "HPxyz_Mk3OperationMode": "d5bf0ed9-d35a-4676-907b-4028ba43b6f1",
    "ManualSaisonMK3": "c1b82599-8e87-4cc2-83db-48da3cd53adf",
    "ControlKermiMK3": "bad65805-1d09-42d5-b00d-0abce6019bef",
    "HP_HeizwasserBetriebsartHK3": "5f344208-662b-44a9-a349-9020297413f3",
    "GlobalAlarmFlag": "13ac9828-9ceb-418c-a084-2ac24a5e7866",
    "SoftwareVersion": "89ef4512-8b6d-4919-a8cb-7de72cbfb002",
    "System_SoftwareUpdateState": "61afe142-5709-47f3-9624-511f6c96ec00",
    "LocalTime": "90b485ce-abed-4a56-a7b2-bd0727c7fbed",
    "Location": "1432f73c-cc13-463f-a0c7-a03f4b18729a",
    "Sunrise": "3dd5e57b-2832-4903-b007-e55f6e681c8d",
    "Sunset": "81fff749-56a1-4f83-8022-a6140058a616",
    "HP_Aussentemperatur_Saison": "e0ed80e9-ec5a-4c5e-941e-f4430448cb27",
    "HP_StatusPumpeMK3": "fb8b77a4-0a1b-4e43-8b2c-ec0dda15cd9b",
    "SummerModeHk3": "e381826f-59bc-4874-8bb9-a92d782b390c",
}


WELLKNOWN_PREFIXES = (
    "HP_",
    "HPxyz_",
    "EcoODU_",
    "EcoIDU_",
    "ControlKermi",
    "ManualSaison",
    "SummerMode",
    "EnergyMode",
    "MK3Name",
    "Heatpump",
    "System_",
    "GlobalAlarmFlag",
    "SoftwareVersion",
    "LocalTime",
    "Location",
    "Sunrise",
    "Sunset",
)


def extract_wellknown_ids(js_text):
    ids = {}

    patterns = (
        r"([A-Za-z0-9_]+):\s*`([0-9a-fA-F-]{36})`",
        r"([A-Za-z0-9_]+):\s*['\"]([0-9a-fA-F-]{36})['\"]",
        r"['\"]([A-Za-z0-9_]+)['\"]\s*:\s*['\"]([0-9a-fA-F-]{36})['\"]",
    )

    for pattern in patterns:
        for name, config_id in re.findall(pattern, js_text or ""):
            if _is_relevant_wellknown_name(name):
                ids[name] = config_id.lower()

    return ids


def _is_relevant_wellknown_name(name):
    return str(name).startswith(WELLKNOWN_PREFIXES)