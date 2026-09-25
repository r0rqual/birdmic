# Regional and seasonal rarity alerts

BirdNET confidence and local rarity answer different questions. Confidence
estimates whether the classifier heard the named species. Rarity asks how often
observers report that species in a particular region at this time of year.
This integration requires both signals before notifying.

## Data flow

```text
eBird regional bar chart + eBird taxonomy
                  │
                  ▼
      parse_ebird_barchart.py
                  │  48 frequencies per species code
                  ▼
        region_frequencies.json
                  │
BirdNET detection ──▶ check_rare_bird.py ──▶ Home Assistant alert policy
```

The generated data maps stable eBird species codes to 48 occurrence
frequencies: four periods per month. Days 1–7, 8–14, and 15–21 use the first
three periods; the fourth covers the remainder of the month.

No regional table is bundled. Generate one for the place you actually monitor,
and keep its source date visible in your own repository or operations notes.

## 1. Download regional inputs

1. Open [eBird's bar-chart page](https://ebird.org/barchart), choose your
   region, and download the histogram data. An eBird login may be required.
2. Download the matching current eBird/Clements taxonomy CSV from the
   [Clements Checklist page](https://www.birds.cornell.edu/clementschecklist/download/).

The bar chart contains common names and seasonal frequencies. The taxonomy is
needed to map those names to the species codes produced by the detector.

## 2. Generate the lookup table

Run:

```bash
python3 scripts/parse_ebird_barchart.py \
  data/my-region-barchart.tsv \
  data/eBird-taxonomy.csv \
  data/my-region-frequencies.json
```

Review the species count and every unmatched-name warning. A few aggregate or
taxonomy-mismatch rows can be expected, but a large unmatched set usually
means the bar chart and taxonomy vintages or formats do not agree.

Validate the generated file and test representative codes:

```bash
python3 -m json.tool data/my-region-frequencies.json >/dev/null
python3 scripts/check_rare_bird.py <common-code> \
  data/my-region-frequencies.json 2026-06-15
python3 scripts/check_rare_bird.py <rare-code> \
  data/my-region-frequencies.json 2026-06-15
python3 scripts/check_rare_bird.py unknown \
  data/my-region-frequencies.json 2026-06-15
```

The unknown code must return `1.000000`: unknown is treated as common so it
cannot generate a false rare-bird alert. A missing or malformed JSON file must
instead return a nonzero status, making broken deployment data diagnosable.

## 3. Deploy to Home Assistant

Create `/config/birdmic/` and copy in:

- `scripts/check_rare_bird.py` as `check_rare_bird.py`;
- the generated table as `region_frequencies.json`.

Then adapt [`examples/rare-bird-alert.yaml`](examples/rare-bird-alert.yaml) as
a Home Assistant package, or merge its `input_boolean`, `command_line`, and
`automation` domains into your existing configuration. The example command
sensor reads the latest normalized species code directly from Home Assistant;
it does not need a temporary state file.

Run Home Assistant's configuration check before restarting. After restart,
enable `input_boolean.rare_bird_alerts_enabled` and manually update
`sensor.bird_rarity_check` once to verify the script path and data file.

## Alert policy and safety gates

The example alerts only when all of these are true:

1. Alerts are enabled.
2. The entity changed because of a new detection, not a restored startup
   state.
3. The species has an eBird-style alphanumeric code; non-bird model taxonomy
   IDs are rejected.
4. The normalized `rarity_eligible` attribute is not explicitly false.
5. Detection confidence is at least `0.70`.
6. The current regional frequency is below `0.05`.

Tune confidence and rarity separately. Raising confidence reduces classifier
false positives. Lowering the regional-frequency threshold makes the alert
more selective. eBird bar-chart frequency is checklist occurrence, not a
formal conservation status or a direct population estimate.

The lookup has two different safe outcomes:

- Unknown species code: return `1.0` successfully and do not alert.
- Broken, missing, or malformed data: exit nonzero so logs expose the failure;
  Home Assistant's command uses `|| echo 1.0` to suppress an alert.

That distinction prevents false alarms without making a broken annual refresh
invisible.

## Test the complete automation

Publish one known message to your test or production MQTT topic from Home
Assistant's MQTT tools:

```json
{
  "CommonName": "Example Bird",
  "ScientificName": "Example species",
  "Confidence": 0.85,
  "SpeciesCode": "example1"
}
```

Use a real code from your generated table instead of `example1`. Test:

- a common species above the threshold: no notification;
- a rare species below the threshold: one notification;
- confidence below `0.70`: no notification;
- an unknown or non-bird taxonomy code: no notification;
- an `unavailable` to restored-state transition: no replayed notification;
- a temporarily missing JSON file: no notification and a useful log error.

Keep test analyzers off the production MQTT topic, or stop the production
publisher briefly, so a simulated detection does not race with real traffic.

## Maintenance

Refresh the regional bar chart annually and update the taxonomy when eBird
publishes a new version. Regenerate the table, review unmatched names and the
species count, repeat the common/rare/unknown tests, then replace the deployed
JSON atomically.

Do not rely solely on an analyzer's missing or zero occurrence field as a
rarity decision. It may mean genuinely uncommon, outside model coverage, or
unavailable geomodel data. The explicit regional table keeps that policy
reviewable and testable.
