# PSD audit and peak clarity

The PSD calculation passed verification; no power-normalization defect was found. The app uses a one-sided Welch power spectral density estimate with a periodic Hann window, per-segment detrending, and mean averaging. Acceleration is converted from m/s² to g **before** calculating power, producing g²/Hz. This matches the [SciPy Welch density definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html).

## Checks performed

- Independently implemented windowed FFT periodograms, one-sided bin scaling, normalization, and averaging agree with the app to numerical precision for odd/even segment sizes and constant, linear, and no detrending.
- A 125 Hz sine with RMS 9.80665 m/s² integrates to 1 g² and peaks at 125 Hz.
- A Nyquist-frequency signal integrates to the correct power without doubling the Nyquist bin.
- Integrated white-noise PSD agrees with time-domain variance within the test tolerance of 1.5%.
- All 21 numerical/import tests pass.

## What made peaks look weak

The old 1024-sample default used short segments. With a 1000 Hz sample rate, frequency bins are spaced 0.9766 Hz apart. The new **4096-sample UI default** reduces spacing to 0.2441 Hz. The Hann equivalent noise bandwidth is 1.5 bins (0.3662 Hz at the new default). Bin spacing is not the same as the ability to resolve any arbitrarily close pair of tones.

For the supplied Starship synthetic Z channel over **169–180 seconds**:

| Segment samples | Peak near 115 Hz | Peak density (g²/Hz) | Averages |
|---:|---:|---:|---:|
| 1024 | 115.2344 Hz | 0.03271 | 20 |
| 4096 | 114.9902 Hz | 0.13803 | 4 |

A larger density peak here comes from concentrating the narrow tone into a smaller bandwidth; it does not mean that the signal acquired more power. Longer segments also produce fewer averages, so the noise estimate is less smooth. The app now reports bin spacing, Hann bandwidth, and number of averages.

The synthetic failure introduces a 115 Hz tone. It is clearest when selecting the post-failure interval. Averaging the entire flight dilutes that event. Ignition, separation, and failure shocks have broadband energy, so a large time-history spike does not necessarily produce a single narrow PSD peak. These synthetic features are not validated signatures of actual vehicle events.

## Suggested use

Select a relatively steady interval to compare tones. Try 162–166 seconds before the injected failure and 169–180 seconds afterward. Use short event-focused intervals for the ignition and separation transients, accepting that their frequency resolution is limited by their duration. The segment setting is automatically capped at the selected sample count.

No peak amplification, smoothing, or power renormalization was added. Plots remain log–log, and raw PSD CSV exports retain all computed bins, including DC. The comparison plot shows only 50–220 Hz to make the known synthetic tone easier to inspect.
