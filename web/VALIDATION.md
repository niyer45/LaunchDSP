# LaunchDSP Web validation

Validated on 2026-10-13 with Node.js 24.15.0, the existing SciPy environment, and an isolated headless Chrome browser on macOS.

## Numerical and file checks

- A calibrated 125 Hz sine with 1 g RMS integrates to 1 g² and peaks at 125 Hz.
- Welch output agrees with SciPy for segment sizes 16, 127, 1000, 4095, and 4096, spanning power-of-two and arbitrary-length FFTs and all three detrending modes. The largest absolute difference divided by the reference peak is **8.35e-14**.
- Even-length Nyquist bins are not doubled; short selections use their exact available sample count.
- Spectrogram power and frame-center times agree with SciPy. Float32 display values above −120 dB agree within 1e-4 dB.
- CSV quoting and comma/tab/semicolon/whitespace parsing were exercised. Compressed MAT import was exercised against the supplied 150,000- and 230,000-sample, four-column files.
- Non-finite acceleration, duplicate/reversed time, and sample gaps are rejected.
- A two-recording .DSP engine round-trip preserves every Float64 sample exactly, plus settings, titles, selections, and views.
- Unsupported session versions, bad encoded buffers, duplicate IDs, out-of-range selections, and invalid overlap settings are rejected.

## Browser checks

- Direct `file://` launch succeeds with background-worker analysis and **zero network requests or page errors**.
- Example data, mouse interval selection, exact interval input, scroll zoom, Home, PSD nearest-point hover, spectral setting changes, sidebar search, and recording switching were exercised.
- Multichannel CSV and compressed MAT were imported through the column-mapping dialogs.
- Spectrogram results remain available when a new selection arrives during an in-flight analysis.
- All eight PNG/SVG combinations (four plot scopes × two formats) download successfully, with titles; PSD CSV includes original bins and metadata.
- A six-recording workspace was saved, the browser page reloaded, and the .DSP file reopened. Active recording, titles, units, settings, selections, views, sample counts, endpoint values, and all recomputed PSD bins matched exactly. Sample-by-sample losslessness is separately verified by the engine test.
- A malformed .DSP import leaves the existing six-recording workspace intact.
- Layouts at 1440 × 1080 and 1024 × 768 have no horizontal overflow. Screenshots were inspected; log tick spacing and spectrogram row aggregation were corrected after review.

Browser print/PDF uses the native print dialog and has not been automated. Other browser engines and Windows/Linux laptops have not been directly tested. Testing uses synthetic data, not user-provided flight telemetry. No claim of unlimited dataset size is made.

The dependency-free engine tests can be run from a repository checkout with Node.js 18 or newer:

```sh
node web/tests/numerical.cjs
```

The live browser workflow can also be checked manually using **Load example flight**, selecting 169–180 s, exporting plots, saving a .DSP run, and reopening it in a fresh tab.
