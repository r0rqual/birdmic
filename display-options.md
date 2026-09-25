# Bird display options

The detector, renderer, and physical display are separate concerns. Keeping
those boundaries explicit lets one BirdNET installation serve Home Assistant,
a normal browser, and a low-power e-paper frame without adding another MQTT
publisher.

## Home Assistant Bird Card

[HABirdDashboard](https://github.com/adamoberley/HABirdDashboard) provides a
Bird Card with collage, statistics, atlas, recordings, and species details. It
can read BirdNET-Go's API directly and use Home Assistant history as a
fallback.

Install it through HACS as a custom Dashboard repository:

1. In HACS, open **Custom repositories**.
2. Add `https://github.com/adamoberley/HABirdDashboard` as type **Dashboard**.
3. Download Bird Card and reload the browser when prompted.
4. Create a panel view and add the card with the visual editor, or adapt
   [`examples/habird-dashboard.yaml`](examples/habird-dashboard.yaml).

For a dedicated wall view, start with an artwork-focused 24-hour collage and
leave the card's view selector enabled for statistics and atlas access. Verify
the browser can reach the configured BirdNET-Go URL. If direct API access is
blocked by routing, mixed-content, or CORS policy, use the Home Assistant data
source and accept its shorter history and lack of audio clips.

Pin a reviewed card version in any repository-managed deployment. Let HACS own
the downloaded JavaScript; keep only your dashboard definition, expected
version, and drift check in your own repository. Do not edit Home Assistant's
`.storage` files directly.

## Dedicated e-paper frame

[Featherframe](https://github.com/wr/featherframe) demonstrates a useful split:
a server near BirdNET reads detections and renders panel-sized artwork, while a
small client only fetches and displays finished frames. Its stock firmware
targets particular ESP32/e-paper hardware, but the same boundary works for a
Raspberry Pi attached to another panel.

A minimal latest-bird frame should:

- read BirdNET through a renderer or narrow adapter, never by writing to its
  database;
- request an image sized and rotated for the physical panel;
- use an ETag or equivalent revision so unchanged content does not refresh;
- replace the screen only when a newer qualifying detection is available;
- keep the last successful image through network, renderer, and client
  restarts;
- avoid queueing every detection while the slow e-paper panel is refreshing;
- store no MQTT, Home Assistant, or analyzer credentials when a read-only LAN
  endpoint can do the job.

Bring up the panel separately from the client service: attach it with power
off, enable only the required buses, verify the detected model and resolution,
then complete several full test refreshes. Decide USB versus battery operation
after measuring real refresh time and idle draw.

Projects worth evaluating before writing a custom renderer include:

- [Featherframe](https://github.com/wr/featherframe) for server/client image
  transport and e-paper behavior.
- [HABirdDashboard](https://github.com/adamoberley/HABirdDashboard) and its
  upstream [AvianVisitors](https://github.com/Twarner491/AvianVisitors) for
  collage, taxonomy, and artwork techniques.
- [belkins-birdnet](https://github.com/Belkins/belkins-birdnet) for another
  standalone illustrated BirdNET presentation.

Treat custom artwork as its own pipeline. Keep source scans, generation
prompts, cleanup, masks, attribution, and license decisions separate from the
runtime display deployment. Confirm the rights for every source or generated
asset before publishing it; a private personal collection is not automatically
appropriate for redistribution.
