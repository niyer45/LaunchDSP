# Validation

Tested on this Mac with Python 3.13.5 and the dependency versions in `requirements-tested.txt`.

- Native packaged macOS app launched successfully; its recording-library window and import controls were verified through the accessibility tree.
- 10 numerical/import tests passed.
- A synthetic 125 Hz acceleration signal with RMS 9.80665 m/s² produced integrated PSD power of 1 g², within 0.1% tolerance.
- Selection-specific tests recovered different 50 Hz and 150 Hz components from separate time intervals.
- Spectrogram density normalization passed the equivalent power check.
- Missing samples, duplicate timestamps, reversed timestamps, gaps, and undersized selections were rejected.
- CSV and MAT import mappings were exercised.
- Offscreen Qt/Matplotlib UI checks exercised mouse press/drag/release, PSD refresh, settings refresh, stale-result clearing, and CSV export.
- All four plot-export modes succeeded in PNG, PDF, and SVG (12 exports).
- The analysis-window screenshot was visually inspected for titles, units, controls, and plot layout.

No actual flight database files have been supplied yet. Validation uses synthetic acceleration signals and generated CSV/MAT files. Nested MATLAB structs and MAT v7.3 files are not supported by this version.

## Sidebar redesign and synthetic flights

- Sidebar recording selection, filtering, and preservation of the active analysis view passed GUI checks.
- Mouse drag selection, spectral settings, invalid selection handling, all 12 plot-export combinations, and PSD CSV export passed again after the redesign.
- All three generated CSV/MAT pairs matched within 1e-8. Every channel has 150,000 samples at 1,000 Hz.
- The first 10 seconds after lift-off produced approximately 94–102 times the PSD-integrated power of a quiet 100–110 s interval in the vertical channels.
- Vertical acceleration peaks were 11.28 g, 7.50 g, and 8.25 g for the three synthetic flights.
- The modern workspace and all three synthetic envelopes were visually inspected.

## Softer controls

Rounded buttons, custom dropdown chevrons, arrow-key numeric inputs, and a text-only plot toolbar were visually inspected. The existing GUI smoke checks passed for selection, settings, file switching, filtering, and plot/data exports.

## Zoom, hover, and PSD audit

21 numerical/import tests passed, including independent FFT/Welch agreement for three segment lengths and all detrending modes, Nyquist scaling, calibrated sine power, and broadband noise variance. GUI checks passed scroll zoom, Home restoration without changing selection, PSD point readout, file switching, and all export modes.

## Faster startup

Confirmed the empty workspace renders without importing NumPy, SciPy, pandas, or Matplotlib. The full existing UI smoke checks passed after loading analysis lazily, including demo generation, selection, scroll zoom, Home, PSD hover, settings, file switching, and exports. Source-level startup timings are recorded in `startup-benchmark.json`.
