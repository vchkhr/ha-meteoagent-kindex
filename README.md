# MeteoAgent K-index for Home Assistant

Home Assistant integration that provides K-index sensor from MeteoAgent. The K-index measures the intensity of geomagnetic disturbances and solar storms that can affect weather-sensitive people.

## Features

- Provides K-index value for today and tomorrow
- Updates every 30 minutes
- Shows values from 1 (low) to 9 (extreme) on the K-index scale
- Data sourced from MeteoAgent (meteoagent.com)

## Installation

### Using HACS (Recommended)

1. Open HACS
2. Click on "Integrations"
3. Click the "+ Explore & Download Repositories" button
4. Search for "MeteoAgent K-index"
5. Click "Download"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/meteoagent_kindex` folder into your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click the "+ ADD INTEGRATION" button
3. Search for "MeteoAgent K-index"
4. Click on it and follow the configuration flow

## Sensors

This integration provides two sensors:

- `sensor.k_index_today`: K-index value for the current day
- `sensor.k_index_tomorrow`: K-index value for tomorrow

Each sensor shows:

- Current K-index value (1-9)
- Unit of measurement: K
- State class: Measurement

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
