# BirdMic setup guide

This guide describes one practical, self-hosted path from outdoor audio to
Home Assistant. BirdNET-Go is a good fit for new installations, while
BirdNET-Pi remains a valid option. Treat device names, paths, IP addresses,
audio devices, display layout, and notification services as examples to adapt.

## 1. Build the audio node

Use a Raspberry Pi with a microphone that ALSA exposes as a capture device. A Pi Zero 2 W and an I2S microphone HAT are a compact choice, but a USB microphone works as well.

Flash Raspberry Pi OS Lite, enable SSH, join your own network, then install the packages needed for capture and RTSP publishing:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg alsa-utils
arecord -l
```

For an I2S HAT, install the vendor-supported driver before continuing. Confirm that recording works locally before adding any streaming services:

```bash
arecord -D <capture-device> -f S16_LE -r 48000 -c 1 -d 5 /tmp/birdmic-test.wav
```

Replace `<capture-device>` with the ALSA device reported by `arecord -l` (for example, `hw:0,0`).

### Install MediaMTX

Download the current Linux ARM build of [MediaMTX](https://github.com/bluenviron/mediamtx/releases) for your Pi, install its binary and default configuration, and create this service as `/etc/systemd/system/mediamtx.service`:

```ini
[Unit]
Description=MediaMTX RTSP server
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/mediamtx /usr/local/etc/mediamtx.yml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Publish microphone audio

Create `/etc/systemd/system/birdmic.service`, substituting your capture device and stream name:

```ini
[Unit]
Description=BirdMic RTSP audio stream
After=mediamtx.service sound.target
Requires=mediamtx.service

[Service]
ExecStartPre=/bin/sleep 3
ExecStart=/usr/bin/ffmpeg -nostdin -f alsa -ac 1 -ar 48000 -i <capture-device> -c:a pcm_s16be -f rtsp rtsp://127.0.0.1:8554/<stream-name>
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable both services and test from another machine:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mediamtx birdmic
ffplay rtsp://<pi-host-or-ip>:8554/<stream-name>
```

Give the Pi a DHCP reservation or another stable address; avoid hard-coding a private address into files you intend to share.

## 2. Connect a BirdNET analyzer

### BirdNET-Go

[BirdNET-Go](https://github.com/tphakala/birdnet-go) can use a local audio
device or consume an RTSP stream such as the one above. Configure its source,
location, confidence policy, and MQTT integration in its web interface. It
also exposes a read-only API used by richer dashboards and renderers.

For Home Assistant OS or Supervised installations, one convenient route is
the BirdNET-Go app from
[alexbelgium's add-on repository](https://github.com/alexbelgium/hassio-addons).
Container and standalone installations can run BirdNET-Go beside Home
Assistant instead. Follow the upstream project for current installation and
configuration details.

When migrating from another analyzer, run only one publisher on the production
MQTT topic. Put a comparison analyzer on a separate test topic and disable
external uploads there to avoid duplicate observations.

### BirdNET-Pi

Install the Mosquitto broker add-on in Home Assistant, then install a BirdNET-Pi add-on or service that supports an RTSP input. Configure it with your own stream URL and location:

```yaml
RTSP_STREAM: "rtsp://<pi-host-or-ip>:8554/<stream-name>"
LATITUDE: <your-latitude>
LONGITUDE: <your-longitude>
CONFIDENCE: 0.7
MQTT_HOST: core-mosquitto
MQTT_PORT: 1883
MQTT_TOPIC: birdnet
```

The exact option names vary by BirdNET-Pi distribution. The important contract
for the example Home Assistant sensor is an MQTT JSON message with fields such
as `CommonName`, `ScientificName`, `Confidence`, and `SpeciesCode` on the topic
you choose. Adapt the sensor if your analyzer publishes a different schema.

## 3. Add Home Assistant entities

[`examples/home-assistant.yaml`](examples/home-assistant.yaml) contains an MQTT sensor for the `birdnet` topic and an optional SQLite query for recent unique species. Merge the snippets into an existing package or configuration file; Home Assistant configuration files cannot safely contain duplicate top-level `mqtt` or `sensor` keys.

Publish a known message from Developer Tools to test the sensor:

```yaml
action: mqtt.publish
data:
  topic: birdnet
  payload: >-
    {"CommonName":"Example Bird","ScientificName":"Example species",
    "Confidence":0.85,"SpeciesCode":"example1"}
```

## 4. Optional displays

For an artwork-oriented Home Assistant dashboard or a dedicated e-paper frame,
see [`display-options.md`](display-options.md). The dashboard can read
BirdNET-Go directly; a small display should receive an already-rendered image
instead of carrying analyzer or Home Assistant credentials.

### ESPHome display

Any ESPHome display can subscribe to the latest-detection sensor and show it. A useful small interface has two pages:

- An alert page with the latest common name, displayed briefly when the sensor changes.
- An idle page showing a handful of recent unique names from the history sensor.

For a touch display, make navigation and touch targets part of your own ESPHome configuration. Enable Home Assistant service calls only if the display needs to control Home Assistant; a read-only BirdMic display does not need that permission.

## 5. Optional regional rarity alerts

eBird's bar chart offers weekly occurrence frequencies for a region. The data is inherently regional, so this repository includes no pre-generated regional file.

1. In eBird, open the bar chart for your chosen region and download its histogram data.
2. Download the current eBird taxonomy CSV from the eBird/Clements taxonomy download page.
3. Generate a JSON table locally:

   ```bash
   python3 scripts/parse_ebird_barchart.py \
     data/my-region-barchart.tsv data/eBird-taxonomy.csv \
     data/my-region-frequencies.json
   ```

4. Copy the generated JSON into a private Home Assistant path such as `/config/birdmic/frequencies.json`.
5. In an automation triggered by the BirdNET sensor, pass its `SpeciesCode` to the helper:

   ```bash
   python3 /config/scripts/check_rare_bird.py <species-code> /config/birdmic/frequencies.json
   ```

The helper prints a number between `0.0` and `1.0`. Choose an alert threshold appropriate for your region (for example, `0.05`), require a minimum BirdNET confidence, then call notification services that exist in your installation. Missing or malformed data returns `1.0`, avoiding false rare-bird alerts.

eBird divides the year into 48 four-per-month periods. Refresh both the bar chart and taxonomy periodically, especially after an eBird taxonomy update.

## Troubleshooting

### No detections arrive in Home Assistant

Work along the pipeline:

1. Confirm the Pi is reachable and both `mediamtx` and `birdmic` services are active: `systemctl status mediamtx birdmic`.
2. Play the RTSP URL with `ffplay` or VLC from another host.
3. Check the BirdNET-Go or BirdNET-Pi logs for connection or audio-processing errors.
4. Use an MQTT client or Home Assistant's MQTT listener to confirm messages reach the configured topic.
5. Check the Home Assistant MQTT sensor's topic and JSON field names against an actual message.

### BirdNET-Pi stops after an interrupted stream

Some versions can get stuck on corrupted WAV files after a stream interruption. If the add-on log identifies malformed files in its temporary stream directory, stop/restart the add-on and clear only the affected temporary WAV queue according to that add-on's documentation. Recheck the RTSP stream first so the problem does not recur.

### Unreliable Wi-Fi

For an outdoor-adjacent microphone node, improve coverage or use Ethernet before increasing retry loops. A DHCP reservation keeps the stream URL stable without exposing your local addressing scheme in public documentation.
