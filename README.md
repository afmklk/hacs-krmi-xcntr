# Kermi X-Center Cloud API integration for Home Assistant
![Icon](/custom_components/kermi_xcenter/brand/icon.png)

A custom Home Assistant integration for Kermi X-Center heat pump systems via cloud API (no Modbus or local HTTP API access required!).

## Features
- Cloud API integration (OpenID Connect)
- Automatic device/entity discovery
- Read/write support

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
You need:
- Installation ID
- Access Token
- Refresh Token
