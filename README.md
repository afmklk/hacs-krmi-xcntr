# Kermi X-Center Cloud API integration for Home Assistant
A custom integration to connect your Kermi X-Center heat pump to Home Assistant via the Kermi cloud platform (no Modbus or local HTTP API access required). Discover hundreds of datapoints, monitor system status, and control supported settings directly from Home Assistant.

![Screenshot](/screenshot.png)

## Features
- Cloud-based OAuth authentication
- Automatically discovers 100+ Kermi datapoints (including your personal favorites) and creates Home Assistant entities without manual configuration 
- Read/write support
- Configurable refresh interval

## Disclaimer
🚨 This custom component is an independent project and is not affiliated with Kermi GmbH. Any trademarks or product names mentioned are the property of their respective owners. You bear the sole risk of a possible loss of the manufacturer's warranty or any damage that may be caused by your use of this integration. Make sure you know what you are doing! 🚨

## Requirements
### Hardware Compatibility
This integration has been tested with:
- Kermi x-center control interface: x-center x40 (firmware version 1.5.110.260), x-center pro (firmware version 1.6.5.44)
- Kermi heat pumps: x-change dynamic, x-change dynamic pro

Other Kermi heat pump models with x-center interface module should also work.
### Remote Servicing via Kermi x-center Portal
Your Kermi x-center control interface must be connected to the internet and registered with the x-center portal to enable remote control. See https://www.kermi.com/en/de/products/heat-pumps/x-center-controller/ for details. To register, go to https://portal.kermi.com/xcenterui.  

## Installation

### Via [HACS](https://hacs.xyz/) (recommended)

1. Open HACS.
2. Open the three-dot menu.
3. Select **Custom repositories**.
4. Add this [custom repository](https://hacs.xyz/docs/faq/custom_repositories) URL: https://github.com/afmklk/hacs-krmi-xcntr 
5. Set category to **Integration**.
6. Install **Kermi X-Center**.
7. Restart Home Assistant.

### Manual
Copy `custom_components/kermi_xcenter` into your Home Assistant config directory.

## Configuration
1. Log into the x-center portal at https://portal.kermi.com/xcenterui/. After login, open the remote control interface for your x-center system (click on the green button) and copy your installation ID from the browser URL. Look for the alphanumeric ID directly after `/XCenterUI/RemoteControlNew/de/DE/` formatted `XXXXXXXX-XXX-XXXX-XXXX-XXXXXXXXXXXX` (this is **not** identical to the serial number of your device). Save your installation ID somewhere for easier reference. Log out from the X-Center portal.
   ![Installation ID](/installation_id.png)
2. In HA, go to **Settings → Devices & services**, click **Add Integration** and search for **Kermi X-Center**.
3. In the config flow, paste the installation ID you just copied.
4. Copy the resulting auth URL.
5. In a new browser window/tab, open **Developer tools → Network**.
6. Paste and open the auth URL.
7. Log in.
8. In Network search/filter for the `loginCallback` request. Double-click to inspect Headers and copy the **Referer** from the **Request Headers** section. It should look something like `https://portal.kermi.com/xcenterui/xcenter/auth/loginCallback?code=...&state=...&iss=https%3A%2F%2Fportal.kermi.com%2Fopenid`
   ![Auth](/auth.png)
9. Paste that URL back into the Callback Referer URL field in HA. If you get an "invalid_state" error, make sure you actually copied the callback's **Referer URL**, not the **Request URL**.
10. Done! 

Optional: By default, data from the Kermi cloud will be refreshed every 5 minutes. You can configure custom refresh intervals in the options flow (⚙️ icon).
