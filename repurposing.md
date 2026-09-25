# Retire or repurpose a BirdMic node

This is a one-time migration checklist for a capture Pi that is no longer
needed after its microphone function moves elsewhere. It is not part of a
generic display or server deployment.

There is no need to replace the SD card or uninstall every old package. The
important outcome is that the former capture stack is stopped, disabled, and
quiet after reboot, with enough configuration preserved for an intentional
rollback.

## 1. Inventory and preserve rollback state

Before changing anything, record:

- the active audio device and microphone/HAT;
- enabled `birdmic`, MediaMTX, and sound-card helper services;
- boot overlays and explicitly loaded sound modules;
- the RTSP URL and all downstream consumers;
- any local BirdNET database, clips, or configuration worth preserving.

Back up the relevant boot and module configuration under distinct names. Do
not overwrite those first-run backups on later deployments.

## 2. Move consumers before retiring the publisher

Confirm the replacement analyzer is healthy and producing current detections.
Move each consumer to the replacement stream or analyzer, then verify Home
Assistant, notifications, and any external upload independently.

Only one analyzer should publish to the production MQTT topic. A shadow or
comparison analyzer needs a separate test topic and must not upload duplicate
observations.

## 3. Stop the old capture runtime

On the old Pi, inspect the actual unit names before acting:

```bash
systemctl list-unit-files | grep -E 'birdmic|mediamtx|wm8960|soundcard'
systemctl status birdmic.service mediamtx.service
```

Stop and disable the units that belong to the retired capture path:

```bash
sudo systemctl disable --now birdmic.service
sudo systemctl disable --now mediamtx.service
```

If a vendor sound-card helper repeatedly starts or fails after the HAT is
removed, stop and mask that specific helper. Do not guess a unit name or mask
unrelated audio services.

Power the Pi off before physically removing a HAT. Review the HAT vendor's
installation changes and comment out only its boot overlays and explicit
module-load entries. Keep a backup and do not broadly remove kernel audio
support.

## 4. Reboot and verify the retired state

After reboot, verify the outcome rather than relying on the earlier commands:

```bash
systemctl is-active birdmic.service mediamtx.service
systemctl is-enabled birdmic.service mediamtx.service
systemctl --failed
ss -ltnp | grep ':8554'
```

The retired services should be inactive and not enabled, the RTSP port should
be closed, and there should be no repeating codec/probe errors for removed
hardware. Check the boot journal and loaded modules using the exact driver
names from the original HAT installation.

Installed packages, binaries, unit files, and logs may remain. Their presence
is harmless when nothing starts them and they do not interfere with the new
role.

## 5. Deploy the new role separately

Keep the reusable deployment for the Pi's new purpose focused on its desired
steady state. For an e-paper frame that normally means hostname, display buses,
the pinned display library, a client service, and health checks.

Do not make that reusable deployment disable BirdMic, MediaMTX, or a particular
sound HAT. Those actions are historical cleanup unique to a reused machine and
would be surprising or harmful on a fresh host.

## Rollback

A rollback is a deliberate operation, not an automatic service restart:

1. Power off and reinstall the microphone/HAT.
2. Review and restore the saved boot/module configuration.
3. Unmask and enable the correct sound-card helper if one was used.
4. Re-enable MediaMTX and BirdMic.
5. Verify capture and RTSP locally before moving any analyzer back.
6. Stop the replacement production publisher before restoring the old MQTT
   publisher.
