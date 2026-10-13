"""Numerical analysis and import helpers, independent of the desktop UI."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import loadmat


@dataclass
class Recording:
    name: str
    time: np.ndarray
    acceleration: np.ndarray
    unit: str
    source: str
    fs: float


def read_tables(path, header=True):
    """Return named tables; MAT supports numeric vectors and 2D matrices."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {'.xlsx', '.xls'}:
        return pd.read_excel(path, sheet_name=None, header=0 if header else None)
    if suffix == '.mat':
        arrays = loadmat(path, squeeze_me=True)
        vectors = {k: v for k, v in arrays.items()
                   if not k.startswith('__') and isinstance(v, np.ndarray)
                   and v.ndim == 1 and np.issubdtype(v.dtype, np.number)}
        result = {}
        for length in sorted({len(v) for v in vectors.values()}):
            result[f'vectors ({length} samples)'] = pd.DataFrame(
                {k: v for k, v in vectors.items() if len(v) == length})
        for k, v in arrays.items():
            if not k.startswith('__') and isinstance(v, np.ndarray) and v.ndim == 2 and np.issubdtype(v.dtype, np.number):
                result[k] = pd.DataFrame(v)
        if not result:
            raise ValueError('No numeric vectors or matrices found. Export nested structures as CSV. MAT v7.3 is not supported.')
        return result
    return {'data': pd.read_csv(path, sep=None, engine='python', header=0 if header else None)}


def make_recording(table, time_column, acceleration_column, time_scale, fs, unit, source, name):
    if np.iscomplexobj(table[acceleration_column].to_numpy()):
        raise ValueError('Acceleration must be real-valued.')
    a = pd.to_numeric(table[acceleration_column], errors='raise').to_numpy(dtype=float)
    if time_column is None:
        if not np.isfinite(fs) or fs <= 0:
            raise ValueError('Enter a positive sample rate when no time column is selected.')
        t = np.arange(len(a), dtype=float) / fs
    else:
        t = pd.to_numeric(table[time_column], errors='raise').to_numpy(dtype=float) * time_scale
    if len(a) < 16 or not np.all(np.isfinite(a)) or not np.all(np.isfinite(t)):
        raise ValueError('At least 16 finite samples are required. Missing values must be resolved before import.')
    if np.iscomplexobj(table[acceleration_column].to_numpy()):
        raise ValueError('Acceleration must be real-valued.')
    steps = np.diff(t)
    if np.any(steps <= 0):
        raise ValueError('Time must increase strictly; duplicate or out-of-order timestamps were found.')
    dt = float(np.median(steps))
    if np.max(np.abs(steps - dt)) > max(dt * .01, np.finfo(float).eps * max(np.max(np.abs(t)), 1) * 8):
        raise ValueError('Sample intervals vary by more than 1%. Resample or repair gaps before spectral analysis.')
    return Recording(name, t, a, unit, str(source), 1 / dt)


def selected_psd(recording, start, end, segment=1024, overlap=.5, detrend='constant'):
    if not np.isfinite(start + end) or start >= end:
        raise ValueError('Selection start must be earlier than end.')
    lo, hi = np.searchsorted(recording.time, [start, end], side='left')
    hi = np.searchsorted(recording.time, end, side='right')
    raw = recording.acceleration[lo:hi]
    x = acceleration_in_g(recording)[lo:hi]
    if len(x) < 16:
        raise ValueError('Select at least 16 samples for a PSD.')
    n = min(int(segment), len(x))
    f, p = signal.welch(x, fs=recording.fs, window='hann', nperseg=n,
                        noverlap=int(n * overlap), detrend=detrend,
                        scaling='density')
    return f, p, {'start': float(recording.time[lo]), 'end': float(recording.time[hi - 1]),
                  'samples': len(x), 'segment': n, 'df': recording.fs / n,
                  'averages': 1 + (len(x)-n)//(n-int(n*overlap)),
                  'enbw': 1.5*recording.fs/n,
                  'rms': float(np.sqrt(np.mean(raw*raw)))}


def spectrogram_data(recording, segment=1024, overlap=.5, detrend='constant'):
    n = min(int(segment), len(recording.time))
    f, t, p = signal.spectrogram(acceleration_in_g(recording), fs=recording.fs,
                                window='hann', nperseg=n, noverlap=int(n*overlap),
                                detrend=detrend, scaling='density', mode='psd')
    # Bound display memory without changing spectral computations or PSD data.
    stride = max(1, int(np.ceil(len(t) / 1600)))
    return f, t[::stride] + recording.time[0], 10*np.log10(np.maximum(p[:, ::stride], np.finfo(float).tiny))


def display_trace(t, x, bins=6000):
    """Min/max envelope preserves visible transients when drawing long histories."""
    if len(t) <= 2*bins:
        return t, x
    edges = np.linspace(0, len(t), bins+1, dtype=int)
    idx = []
    for a, b in zip(edges[:-1], edges[1:]):
        idx.extend(sorted((a+int(np.argmin(x[a:b])), a+int(np.argmax(x[a:b])))))
    return t[idx], x[idx]


def acceleration_in_g(recording):
    factors = {'g': 1., 'm/s²': 1/9.80665, 'ft/s²': .3048/9.80665}
    if recording.unit not in factors:
        raise ValueError('Choose g, m/s², or ft/s² for calibrated spectral units.')
    return recording.acceleration * factors[recording.unit]
