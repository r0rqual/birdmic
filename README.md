# BirdMic

BirdMic is a portable guide to a self-hosted bird-detection pipeline. A small
Raspberry Pi, camera, or other microphone source publishes audio to BirdNET-Go
or BirdNET-Pi; detections can then flow to Home Assistant, dashboards, and
dedicated displays. The project also covers optional regional rarity alerts.

This repository is a portable guide and set of helper scripts. Supply your own network names, addresses, coordinates, notification targets, and eBird region.

## What this project adds

The main customization here is a regional, season-aware rarity alert for Home
Assistant. BirdNET confidence estimates whether the classifier heard a
species; it does not say whether that bird is unusual where you live this week.
BirdMic combines the detected eBird species code with your regional eBird bar
chart, applies confidence and taxonomy safety gates, and notifies only below a
frequency threshold you choose.

The repository also records portable configuration patterns for capture,
BirdNET-Go/BirdNET-Pi, detection history, HABirdDashboard, ESPHome, and an
optional e-paper display. Those projects remain independently maintained; the
integration and rarity policy are the value added here.

## Architecture

```mermaid
flowchart LR
    Mic[Microphone, camera, or capture Pi] -->|Local or RTSP audio| BirdNET[BirdNET-Go or BirdNET-Pi]
    BirdNET -->|MQTT detections| HA[Home Assistant]
    BirdNET -->|Read-only API or database| Frame[Optional e-paper frame]
    HA --> Display[Dashboard or ESPHome display]
    HA --> Alerts[Optional rare-bird notifications]
```

## What you need

- A supported USB, analog, camera, or I2S microphone source
- Optional: a Raspberry Pi capture node (a Pi Zero 2 W works well)
- Home Assistant, plus its Mosquitto MQTT broker add-on
- BirdNET-Go or a BirdNET-Pi installation that can consume your audio source
- Optional: a browser, ESPHome, or e-paper display and an eBird account for
  regional rarity alerts

## Start here

1. Follow [the setup guide](bird-notifier.md) to publish an audio stream and
   connect a BirdNET analyzer to Home Assistant.
2. Build the [regional rarity alert](regional-rarity-alerts.md) for your eBird
   region.
3. Copy/adapt [`examples/home-assistant.yaml`](examples/home-assistant.yaml) into your Home Assistant configuration.
4. Choose a browser, Home Assistant, ESPHome, or e-paper presentation from
   [the display guide](display-options.md).

## Repository layout

- [`bird-notifier.md`](bird-notifier.md) — end-to-end setup, display ideas, and troubleshooting
- [`regional-rarity-alerts.md`](regional-rarity-alerts.md) — the regional data pipeline, safety policy, deployment, and testing
- [`display-options.md`](display-options.md) — HABirdDashboard and dedicated e-paper display patterns
- [`examples/home-assistant.yaml`](examples/home-assistant.yaml) — Home Assistant configuration starting point
- [`examples/rare-bird-alert.yaml`](examples/rare-bird-alert.yaml) — portable Home Assistant rarity package
- [`examples/habird-dashboard.yaml`](examples/habird-dashboard.yaml) — artwork-focused Home Assistant Bird Card view
- [`scripts/parse_ebird_barchart.py`](scripts/parse_ebird_barchart.py) — turns an eBird bar-chart export into weekly frequency JSON
- [`scripts/check_rare_bird.py`](scripts/check_rare_bird.py) — looks up one species' frequency for a date
