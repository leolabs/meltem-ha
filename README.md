# Meltem Integration for Home Assistant

This is a custom integration for Home Assistant that allows you to control and monitor Meltem ventilation units through their cloud API.

## Features

- Control ventilation power (on/off)
- Set ventilation modes (Off, Low, Medium, High, Manual)
- Adjust manual ventilation speed (10-100%)
- Monitor various sensors:
  - Temperature sensors (Supply, Extract, Exhaust, Outdoor)
  - Humidity sensors (Supply, Extract, Exhaust, Outdoor)
  - Filter status and days until filter change
  - Operation mode and error status
  - Current ventilation speed

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance
2. Add this repository as a custom repository in HACS:
   - Click on HACS in the sidebar
   - Click on "Integrations"
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add the URL of this repository
   - Select "Integration" as the category
3. Click on "+ Explore & Download Repositories" in the bottom right
4. Search for "Meltem"
5. Click "Download"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Copy the `custom_components/meltem` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Settings -> Devices & Services
2. Click "+ Add Integration"
3. Search for "Meltem"
4. Enter your Meltem cloud credentials (username and password)

## Entities

The integration creates the following entities for each Meltem device:

### Controls

- `switch.<device>_power`: Turn the ventilation unit on/off
- `select.<device>_mode`: Select ventilation mode
- `number.<device>_speed`: Adjust manual ventilation speed (only active in manual mode)

### Sensors

- Temperature sensors (°C)
  - Supply Air
  - Extract Air
  - Exhaust Air
  - Outdoor Air
- Humidity sensors (%)
  - Supply Air
  - Extract Air
  - Exhaust Air
  - Outdoor Air
- Status sensors
  - Operation Mode
  - Error Status
  - Days Until Filter Change
  - Current Speed (%)

## Support

For bugs and feature requests, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
