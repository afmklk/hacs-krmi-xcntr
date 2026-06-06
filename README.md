# Kermi X-Center Cloud API integration for Home Assistant
![Icon](/custom_components/kermi_xcenter/brand/icon.png)

A custom Home Assistant integration for Kermi X-Center heat pump systems that retreives data via cloud API (no Modbus or local HTTP API access required).

## Features
- Cloud API integration (OpenID Connect)
- Automatic datapoint discovery (including favorites)
- Read/write support
- 5-minute refresh interval

## Disclaimer
🚨 This custom component is an independent project and is not affiliated with Kermi. Any trademarks or product names mentioned are the property of their respective owners. You bear the sole risk of a possible loss of the manufacturer's warranty or any damage that may be caused by your use of this integration. Make sure you know what you are doing! 🚨

## Requirements
### Hardware Compatibility
This integration has been tested with:
- Kermi IFM: x-center 40 (control system), Firmware version 1.5.110.260
- Kermi Heat pump: x-change dynamic (air/water heat pump), Firmware version 6.3

Other Kermi heat pump models with x-center interface module should also work.
### Remote Servicing via x-center Portal
Your Kermi x-center must be connected to the internet and registered with the x-center portal to enable remote servicing. See https://www.kermi.com/en/de/products/heat-pumps/x-center-controller/ for details. To register, go to https://portal.kermi.com/xcenterui.  

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

1. In HACS, add this [custom repository](https://hacs.xyz/docs/faq/custom_repositories): https://github.com/afmklk/hacs-krmi-xcntr (Category: Integration)
2. Install and reboot HA.
3. Go to Settings > Devices & Services, click "+ Add Integration" and search for "Kermi X-Center"

### Manual
Copy `custom_components/kermi_xcenter` into your Home Assistant config directory.

## Configuration
1. Log into the X-Center portal for your system https://portal.kermi.com/xcenterui/. After login, copy your installation ID from the browser URL (look for the part directly after "portal.kermi.com/XCenterUI/RemoteControlNew/de/DE/" formatted XXXXXXXX-XXX-XXXX-XXXX-XXXXXXXXXXXX). Log out again.
2. In the HA config flow, paste the installation ID you just copied.
3. Copy the resulting auth URL from the `open_this_url` field in the config flow.
4. In a new browser window/tab, open developer tools > Network.
5. Paste and open the auth URL.
6. Log in.
7. In Network search/filter for the `loginCallback` request. Copy the full request URL (it should look something like https://portal.kermi.com/xcenterui/xcenter/auth/loginCallback?code=...).
8. Paste that URL back into the `authorization_response_url` field in HA. If you get an "invalid_state" error, make sure you actually copied the request URL, not any response or referrer URLs.
9. Done! The integration should auto-discover relevant datapoints for your device via the cloud API and set up corresponding entities.
