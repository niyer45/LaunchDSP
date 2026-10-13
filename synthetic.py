"""Reproducible illustrative launch vibration; not a flight dynamics model."""
from pathlib import Path
import json
import numpy as np
from scipy import signal
from scipy.io import savemat

PHASES = [('Lift-off', 0, 10), ('Transonic', 35, 52), ('Max q', 62, 72)]


def generate_flight(index=0, fs=1000):
    rng = np.random.default_rng(2026 + index)
    t = np.arange(-8*fs, 142*fs, dtype=float) / fs
    shift = [-.3, 1.1, -.8][index % 3]
    lift = np.exp(-.5*((t-4-shift)/1.6)**2)
    trans = np.exp(-.5*((t-46-shift)/4.0)**2)
    maxq = np.exp(-.5*((t-67-shift)/5.0)**2)
    envelope = .15 + .11/(1+np.exp((t-80)/5)) + 2.3*lift + .95*trans + .65*maxq
    columns = {'time_s': t}
    for axis, scale in [('x', .62), ('y', .78), ('z', 1.)]:
        noise = signal.sosfiltfilt(signal.butter(4, [8, 350], btype='bandpass', fs=fs, output='sos'), rng.normal(size=len(t)))
        noise /= np.std(noise)
        tones = (.5*lift*np.sin(2*np.pi*38*t) + .4*trans*np.sin(2*np.pi*(85+index*3)*t)
                 + .3*maxq*np.sin(2*np.pi*145*t))
        chirp = .12*trans*signal.chirp(t+8, f0=35, t1=150, f1=220)
        columns[f'accel_{axis}_m_s2'] = 9.80665*scale*(envelope*noise + tones + chirp)
    return columns


def write_examples(folder):
    folder=Path(folder); folder.mkdir(parents=True, exist_ok=True)
    for index in range(3):
        data=generate_flight(index)
        stem=f'synthetic_flight_{index+1:02d}'
        np.savetxt(folder/(stem+'.csv'), np.column_stack(list(data.values())), delimiter=',',
                   header=','.join(data), comments='', fmt='%.8f')
        savemat(folder/(stem+'.mat'), data, do_compression=True)
    (folder/'metadata.json').write_text(json.dumps({'synthetic':True, 'sample_rate_hz':1000,
        'start_s':-8, 'end_s':141.999, 'samples_per_channel':150000, 'acceleration_units':'m/s^2',
        'seeds':[2026,2027,2028], 'event_windows_s':PHASES,
        'description':'Illustrative random vibration envelopes inspired by the supplied image; not digitized or measured flight data.'},indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('folder',nargs='?',default='sample_data')
    write_examples(parser.parse_args().folder)
