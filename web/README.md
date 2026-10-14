# LaunchDSP Web

A self-contained HTML workspace for flight acceleration analysis on a laptop. No Python, MATLAB, installation, server, CDN, or network connection is required. Files are read and processed locally in the browser.

## Open the app

Download **LaunchDSP.html** and open it in a current laptop browser such as Chrome, Edge, Firefox, or Safari. If it opens in a text editor, right-click the file and choose **Open With** your browser. On GitHub, use **Download raw file** rather than saving the repository's file-view page. You can also serve the same file from a static web server.

The app was tested in Chrome on macOS at 1440 × 1080 and 1024 × 768. Windows/Linux and other browser engines have not been directly tested. Compressed MAT import requires the browser's `DecompressionStream` API; the app explains when that is unavailable. CSV import and .DSP sessions do not require that API.

## Analyze a run

1. Choose **Import data files** to select multiple CSV, TSV, text, or MAT files. For headerless CSV, uncheck **CSV files have headers** in Import options first.
2. Map each file's time column and select acceleration channels. Input defaults are seconds and m/s². Without a time column, enter a sample rate. Each acceleration channel becomes a recording in the sidebar.
3. Select a recording. Its full-recording spectrogram appears beside the PSD panel, beneath the acceleration time history.
4. Drag across the time history or enter exact start/end times and choose **Update PSD**. **Full recording** calculates the PSD for the entire recording. The selection must include at least 16 samples.
5. Scroll over the time history to zoom around the pointer. Choose **Pan** to drag the view; Shift-drag also pans. **Home**, or a double-click in the time history, restores the full view while retaining the PSD selection.
6. Hover over the log–log PSD to inspect the closest computed point in screen coordinates. The readout is not interpolated.
7. Set the plot title, FFT segment, overlap, and detrending as needed. Choose **Apply settings** to recalculate. Settings and selections belong to each recording.

**Load example flight** generates a reproducible Starship-style vibration signal from prelift-off through separated flight: liftoff, normal throttling around max q, ship ignition, separation, and an illustrative engine-failure transient. It is synthetic local structural vibration, not measured Starship telemetry or a validated physical failure model. Select **169–180 s** to inspect the injected 115 Hz oscillation.

## Save and reopen .DSP runs

Set a run name and choose **Save run .DSP**. Keep the downloaded file for later reuse or transfer it to another laptop. Choose **Open .DSP run** to restore it.

A .DSP file contains the complete recording library, original time and acceleration samples, source filenames, units, per-recording plot titles, FFT settings, selected intervals, zoom views, and the active recording. PSD and spectrogram arrays are recalculated from the saved data after reopening. Samples are stored as lossless base64-encoded little-endian Float64 buffers inside versioned JSON, with format `LaunchDSP/session`, version `1`.

Opening a run replaces the current workspace. Unsaved work prompts before replacement. The entire incoming run is validated first; an invalid file leaves the current run intact. Save before closing: no browser database or automatic persistent storage is used. Existing files are never overwritten in place; a new export is downloaded.

This .DSP format belongs to **LaunchDSP Web**. The existing Python/Mac desktop build does not yet import it. The .DSP file embeds the full data, so its size grows with the number and length of recordings. Data and analysis must fit available browser memory.

## Export results

- **Export plots:** download time history, spectrogram, PSD, or the entire workspace as PNG or SVG. Titles and axis units are included. SVG traces remain vectors; the spectrogram is an embedded raster.
- **PSD CSV:** original frequency/density bins, including DC, plus selected-interval and analysis metadata.
- **Print / PDF:** use the browser's print dialog to print or save the analysis workspace as PDF.

## Import and numerical conventions

Time is in seconds. Real acceleration channels may be in m/s², g, or ft/s². At least 16 finite samples are required. Time must strictly increase, with sample intervals within 1% of their median. Missing values, duplicates, reversed timestamps, and gaps are rejected rather than silently interpolated.

CSV supports comma, tab, semicolon, and whitespace separation; quoted delimiter fields are handled. Numeric acceleration/time columns are required. MAT import supports top-level real numeric vectors and dense two-dimensional matrices in MATLAB Level 5 files (including compressed v7). Select the appropriate table; matrices use samples in rows. Nested structs, sparse or complex arrays, MAT v4, and MAT v7.3/HDF5 require conversion to CSV or supported MAT. XLSX is not supported in this browser build.

PSD uses a one-sided Welch density estimate with a periodic Hann window and configurable overlap/detrending. Input is converted to g with **1 g = 9.80665 m/s²**. Frequency is in Hz and density in g²/Hz. Short selections cap the FFT segment to the selected sample count; an exact arbitrary-length FFT preserves the frequency grid. Default settings are 4096 samples, 50% overlap, and per-segment mean removal. Frequency spacing is Fs/N and Hann ENBW is 1.5 Fs/N. More segment samples sharpen narrow tones, at the cost of fewer averages and coarser time resolution.

The spectrogram uses the same density normalization and settings over the whole recording, displayed as dB relative to 1 g²/Hz across an 80 dB color range. At most 1600 regularly sampled time slices are computed for display. Dense frequency rows use the maximum per displayed row to preserve visible narrow tones. These display choices do not alter the selected-window PSD, which uses all original samples. Time-history rendering uses a min/max envelope when needed. RMS is computed from original input samples and includes their mean. Log PSD plots omit DC/nonpositive bins; PSD CSV retains all bins without a display floor or peak boosting.

Numerical analysis, file parsing, and .DSP encoding run in a Web Worker where supported. If workers cannot be created, local processing falls back to the main browser thread. This build contains no third-party runtime dependencies or external requests.
