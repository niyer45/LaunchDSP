# Synthetic flight test data

Three reproducible, illustrative acceleration histories inspired by the reference image. Each file includes time in seconds and X/Y/Z acceleration in m/s². The CSV and MAT files are equivalent copies; import one format per flight to avoid duplicates.

- Sample rate: 1,000 Hz; 150,000 samples per axis.
- Time span: −8 to 141.999 seconds.
- Lift-off burst: approximately 0–10 seconds.
- Transonic burst: approximately 35–52 seconds.
- Max-q burst: approximately 62–72 seconds.
- Quiet late-flight segment: try 100–120 seconds.

In the app, import files, map `time_s` to time, and select any `accel_*_m_s2` channels. Leave time units as seconds and acceleration units as m/s². PSD output is g²/Hz.

Compare a 0–10 s PSD with a 100–110 s PSD to see the amplitude difference. Transonic and max-q intervals have different tones and noise amplitudes. Seeds and event windows are recorded in metadata.json.

These are synthetic random vibration signals, not digitized measurements or a validated physical flight model. Flight-phase timings are illustrative. The reference uses g; the stored acceleration is multiplied by 9.80665 to provide m/s² as requested.
