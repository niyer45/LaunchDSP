# Starship-style synthetic ascent with injected failure

Illustrative acceleration histories for testing LaunchDSP. This is **local structural vibration about zero**, like the earlier reference plot; it is not trajectory acceleration, thrust-to-mass acceleration, or raw accelerometer specific force including a gravity baseline. No measured Starship telemetry is used.

## Import

Import either `starship_style_ascent_fault.csv` or its matching `.mat` file. Select `time_s` for time, any of the X/Y/Z acceleration columns, **seconds**, and **m/s²**. The Z channel shows the clearest event sequence. The app converts spectral units to g²/Hz. CSV and MAT contain equivalent data; you only need one format.

230,000 samples per axis at 1,000 Hz, from −20 to 209.999 seconds. Acceleration columns are `accel_x_m_s2`, `accel_y_m_s2`, and `accel_z_m_s2`. Event annotations are in a separate `events.csv`; do not import that file as an acceleration recording.

## Assumed scenario

| Event | Time from lift-off |
|---|---:|
| Quiet prelift-off, then short engine run-up | −20 to 0 s |
| Lift-off burst | 0 s, envelope peaks near 1.3 s |
| Normal throttle-down | 43–48 s; marker at 45 s |
| Max q within reduced-throttle interval | 62 s |
| Normal throttle recovery | 73–80 s; marker at 75 s |
| Ship ignition / hot-staging transient | 158 s |
| Smaller stage-separation transient | 160 s |
| Hypothetical Raptor failure, seven seconds after separation | 167 s |
| Post-failure separated flight | through 209.999 s |

Throttle reduces to a nominal relative command of 60% before max q and recovers afterward. This is an illustrative schedule, not a documented Starship throttle program. Small throttle-transition bursts are normal events in this scenario, not faults. Max q also adds broad aerodynamic vibration.

The injected failure has a brief shock, decaying 43 Hz ringing, an introduced 115 Hz oscillation, and a reduced 180 Hz engine-related tone. These are deliberately chosen test features, **not a diagnostic signature of a real Raptor failure**. The signal does not simulate vehicle breakup or assume a subsequent real-world flight outcome.

Useful PSD selections: 20–30 s (powered ascent), 55–65 s (throttle bucket), 85–95 s (recovered throttle), 157.5–159 s (ignition), 159.7–160.8 s (separation), 162–166 s (healthy separated flight), and 169–180 s (after injected fault). Use longer windows for finer frequency resolution.

The PNG/PDF preview uses g for readability; data files use m/s² with 1 g = 9.80665 m/s². All times, amplitudes, frequencies, and sensor responses are assumed. The three axes are independently generated random vibration with different scale factors, not a validated coupled structural model.

`generate.py` regenerates all data and plots using a fixed random seed. It requires numpy, scipy, and matplotlib, already used by the app.

General event-order context: [SpaceX Starship flight-test updates](https://new.spacex.com/updates) describes upper-stage ignition during hot staging. The exact timings and failure in this dataset are synthetic and are not attributed to that source.
