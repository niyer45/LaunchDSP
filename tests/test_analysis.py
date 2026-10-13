import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest
from scipy.io import savemat
from analysis import make_recording, selected_psd, spectrogram_data, read_tables


def recording(y, fs=1000):
    return make_recording(pd.DataFrame({'time':np.arange(len(y))/fs,'acc':y}), 'time','acc',1,fs,'m/s²','test','test')


def test_psd_calibration_and_peak():
    t=np.arange(16000)/1000
    r=recording(9.80665*np.sqrt(2)*np.sin(2*np.pi*125*t))
    f,p,m=selected_psd(r,0,t[-1],1000)
    assert f[np.argmax(p)] == pytest.approx(125)
    assert np.sum(p)*(f[1]-f[0]) == pytest.approx(1,rel=.001)
    assert m['rms'] == pytest.approx(9.80665,rel=.001)


def test_selected_windows_are_different():
    t=np.arange(12000)/1000
    r=recording(9.80665*np.sin(2*np.pi*np.where(t<6,50,150)*t))
    f,p,_=selected_psd(r,0,5,1000); assert f[np.argmax(p)]==pytest.approx(50)
    f,p,_=selected_psd(r,7,11,1000); assert f[np.argmax(p)]==pytest.approx(150)


def test_spectrogram_units():
    r=recording(np.sqrt(2)*9.80665*np.sin(2*np.pi*100*np.arange(10000)/1000))
    f,t,db=spectrogram_data(r,1000,0)
    assert np.sum(10**(db[:,0]/10))*(f[1]-f[0]) == pytest.approx(1,rel=.001)


@pytest.mark.parametrize('kind',['nan','duplicate','gap','reverse'])
def test_reject_bad_samples(kind):
    t=np.arange(100)/1000; y=np.ones(100)
    if kind=='nan':y[5]=np.nan
    if kind=='duplicate':t[5]=t[4]
    if kind=='gap':t[50:]+=.01
    if kind=='reverse':t=t[::-1]
    with pytest.raises(ValueError):make_recording(pd.DataFrame({'t':t,'a':y}),'t','a',1,1000,'m/s²','','')


def test_short_window_rejected():
    r=recording(np.ones(100))
    with pytest.raises(ValueError):selected_psd(r,0,.003)


def test_csv_and_mat(tmp_path):
    table=pd.DataFrame({'time':np.arange(100)/1000,'acc':np.ones(100)})
    csv=tmp_path/'flight.csv'; table.to_csv(csv,index=False)
    mat=tmp_path/'flight.mat'; savemat(mat,{c:table[c].to_numpy() for c in table})
    for path in [csv,mat]:
        data=next(iter(read_tables(path).values()))
        r=make_recording(data,'time','acc',1,1,'m/s²',path,'flight')
        assert r.fs==pytest.approx(1000)


def test_no_time_column():
    r=make_recording(pd.DataFrame({'a':np.ones(100)}),None,'a',1,200,'g','','')
    assert r.time[-1]==pytest.approx(.495)


@pytest.mark.parametrize('n',[255,256,1024])
@pytest.mark.parametrize('detrend',['constant','linear',False])
def test_welch_against_independent_fft(n,detrend):
    rng=np.random.default_rng(3026); x=rng.normal(size=4096)+.002*np.arange(4096)
    r=recording(x*9.80665)
    f,p,_=selected_psd(r,r.time[0],r.time[-1],n,.5,detrend)
    w=.5-.5*np.cos(2*np.pi*np.arange(n)/n)
    step=n-int(n*.5); densities=[]
    for start in range(0,len(x)-n+1,step):
        segment=x[start:start+n].copy()
        if detrend=='constant':segment-=segment.mean()
        elif detrend=='linear':
            design=np.column_stack([np.arange(n),np.ones(n)])
            segment-=design@np.linalg.lstsq(design,segment,rcond=None)[0]
        density=np.abs(np.fft.rfft(segment*w))**2/(r.fs*np.sum(w*w))
        density[1:-1 if n%2==0 else None]*=2
        densities.append(density)
    np.testing.assert_allclose(p,np.mean(densities,axis=0),rtol=2e-11,atol=1e-13)


def test_nyquist_not_doubled():
    x=(-1.)**np.arange(16000)
    r=recording(x*9.80665)
    f,p,_=selected_psd(r,0,r.time[-1],1000,detrend=False)
    assert np.sum(p)*(f[1]-f[0])==pytest.approx(1,rel=1e-10)


def test_noise_variance_and_metadata():
    r=recording(np.random.default_rng(81).normal(size=200000)*9.80665)
    f,p,m=selected_psd(r,0,r.time[-1],4096)
    assert np.sum(p)*(f[1]-f[0])==pytest.approx(np.var(r.acceleration/9.80665),rel=.015)
    assert m['averages']==96
    assert m['enbw']==pytest.approx(1.5*r.fs/4096)
