"""Generate illustrative local structural vibration, not trajectory acceleration."""
from pathlib import Path
import json
import numpy as np
from scipy import signal
from scipy.io import savemat
from matplotlib.figure import Figure

G=9.80665
FS=1000
EVENTS=[('Lift-off',0),('Throttle down',45),('Max q',62),('Throttle recovery',75),
        ('Ship ignition',158),('Stage separation',160),('Injected Raptor failure',167)]


def generate():
    rng=np.random.default_rng(9302026)
    t=np.arange(-20*FS,210*FS,dtype=float)/FS
    def ramp(a,b):
        u=np.clip((t-a)/(b-a),0,1)
        return u*u*(3-2*u)
    # Illustrative control schedule: reduced thrust command through max q.
    throttle=1-.40*ramp(43,48)+.40*ramp(73,80)
    active=ramp(-3,0)
    booster=1-ramp(155,158)
    ship=ramp(158,160)
    failed=ramp(167,167.3)
    aero=.20*np.exp(-.5*((t-62)/12)**2)
    level=.02+active*booster*(.48*throttle+aero)+.20*ship+.08*failed
    data={'time_s':t}
    for axis,scale in [('x',.48),('y',.65),('z',1.)]:
        noise=signal.sosfiltfilt(signal.butter(4,[6,340],fs=FS,btype='bandpass',output='sos'),rng.normal(size=t.size))
        noise/=np.std(noise)
        y=level*noise
        y+=active*booster*.18*throttle*np.sin(2*np.pi*80*t)
        y+=ship*(1-.45*failed)*.17*np.sin(2*np.pi*180*t)
        def pulse(center,width,peak):
            envelope=np.exp(-.5*((t-center)/width)**2)
            raw=envelope*(noise+.4*np.sin(2*np.pi*52*t))
            return raw*peak/np.max(np.abs(raw))
        y+=pulse(1.3,1.0,7.7)
        # Small, normal transients bracket the throttle bucket.
        y+=pulse(45,.45,.65)+pulse(75,.55,.85)
        y+=pulse(158.12,.25,5.5)
        y+=pulse(160.10,.14,2.25)
        # Hypothetical fault: abrupt shock, decaying ringing, changed spectrum.
        u=np.maximum(t-167,0)
        onset=t>=167
        y+=pulse(167.18,.11,6.7)
        y+=onset*1.15*np.exp(-u/1.1)*np.sin(2*np.pi*43*u)
        y+=failed*.32*np.sin(2*np.pi*115*t)
        data[f'accel_{axis}_m_s2']=G*scale*y
    return data,throttle


def main():
    folder=Path(__file__).resolve().parent
    data,throttle=generate(); t=data['time_s']; z=data['accel_z_m_s2']/G
    stem='starship_style_ascent_fault'
    np.savetxt(folder/(stem+'.csv'),np.column_stack(list(data.values())),delimiter=',',header=','.join(data),comments='',fmt='%.9f')
    savemat(folder/(stem+'.mat'),data,do_compression=True)
    (folder/'events.csv').write_text('event,time_s\n'+''.join(f'{name},{at}\n' for name,at in EVENTS))
    metadata={'synthetic':True,'seed':9302026,'sample_rate_hz':FS,'samples_per_axis':len(t),
        'start_s':float(t[0]),'end_s':float(t[-1]),'acceleration_units':'m/s^2','signal_type':'Zero-centered local structural vibration; no rigid-body acceleration or gravity baseline.',
        'events':[{'name':name,'time_s':at} for name,at in EVENTS],
        'throttle_bucket':{'ramp_down_s':[43,48],'relative_level':.60,'recovery_s':[73,80]},
        'fault':'Illustrative injected engine-failure shock plus 43 Hz decaying ringing and 115 Hz residual oscillation; not a measured Raptor signature.',
        'disclaimer':'All event times and amplitudes are scenario assumptions. Not an actual Starship flight reconstruction or validated vehicle response.'}
    (folder/'metadata.json').write_text(json.dumps(metadata,indent=2))
    # Draw a min/max envelope, preserving every visible extremum.
    def plot_trace(ax,left,right):
        sel=(t>=left)&(t<=right); tx=t[sel]; y=z[sel]
        edges=np.linspace(0,len(tx),min(5000,len(tx)//2)+1,dtype=int)
        indices=[]
        for a,b in zip(edges[:-1],edges[1:]):
            if b>a:indices.extend(sorted([a+int(np.argmin(y[a:b])),a+int(np.argmax(y[a:b]))]))
        ax.plot(tx[indices],y[indices],color='#2584bb',lw=.55)
        ax.set_xlim(left,right);ax.set_xlabel('Time relative to lift-off (s)');ax.set_ylabel('Vibration acceleration (g)')
        ax.grid(alpha=.16);ax.spines[['top','right']].set_visible(False)
    fig=Figure(figsize=(15,9),layout='constrained')
    grid=fig.add_gridspec(2,2,height_ratios=[1.2,1])
    full=fig.add_subplot(grid[0,:]);q=fig.add_subplot(grid[1,0]);stage=fig.add_subplot(grid[1,1])
    plot_trace(full,-20,210);full.set_ylim(-11,11)
    full.set_title('Full recording · prelift-off through early separated flight',loc='left',weight='bold')
    full.axvspan(-20,0,color='#9aabc0',alpha=.12);full.axvspan(43,80,color='#72baa7',alpha=.16)
    full.axvspan(158,162,color='#b7a0dc',alpha=.19);full.axvspan(167,210,color='#e4a587',alpha=.10)
    for name,at,ypos in [('Lift-off',0,9),('Throttle bucket / max q',62,9),('Hot staging',159,9),('Injected failure',167,-9)]:
        full.annotate(name,xy=(at,0),xytext=(at,ypos),ha='center',fontsize=10,arrowprops={'arrowstyle':'-','color':'#718196'},color='#33485e')
    plot_trace(q,32,88);q.set_ylim(-3.8,3.8);q.set_title('Normal throttle-down and recovery around max q',loc='left',weight='bold')
    q.axvspan(43,80,color='#72baa7',alpha=.13)
    for name,at in EVENTS[1:4]:
        q.axvline(at,color='#638d82',lw=.8,ls='--');q.text(at,3.4,name,ha='center',fontsize=9)
    # Indicate schedule on a separate inset, never mix throttle with acceleration units.
    inset=q.inset_axes([.06,.07,.88,.15]);inset.plot(t,throttle,color='#397764',lw=1.8);inset.set_xlim(32,88);inset.set_ylim(.5,1.1);inset.set_yticks([.6,1]);inset.set_yticklabels(['60%','100%'],fontsize=7);inset.set_xticks([]);inset.set_title('Illustrative relative throttle command',fontsize=8,pad=2);inset.spines[['top','right','bottom']].set_visible(False)
    plot_trace(stage,153,179);stage.set_ylim(-9,9);stage.set_title('Hot staging and injected engine-failure event',loc='left',weight='bold')
    for name,at in EVENTS[4:]:
        stage.axvline(at,color='#b47e6d' if at==167 else '#8b80ac',lw=.8,ls='--')
        label=name.replace(' ','\n',1)
        stage.annotate(label,xy=(at,0),xytext=(at+(-1.5 if at==158 else 1 if at==160 else 1.6),7.2),ha='center',fontsize=9,arrowprops={'arrowstyle':'-','color':'#8b80ac'})
    fig.suptitle('STARSHIP-STYLE SYNTHETIC ACCELERATION\nIllustrative vibration test data — not measured telemetry | 1,000 Hz | preview in g; files in m/s²',fontsize=15,weight='bold')
    fig.savefig(folder/'preview.png',dpi=170)
    fig.savefig(folder/'preview.pdf')
    print(json.dumps({'samples':len(t),'z_peak_g':float(np.max(abs(z))),'events':EVENTS}))


if __name__=='__main__':main()
