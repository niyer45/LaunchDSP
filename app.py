"""LaunchDSP: local desktop acceleration analysis."""
import sys
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PySide6 import QtCore, QtGui, QtWidgets as Q

_ANALYSIS_READY = False


def ensure_analysis():
    """Load numerical and plotting libraries only when a recording is opened."""
    global _ANALYSIS_READY, np, Figure, FigureCanvasQTAgg, NavigationToolbar2QT
    global SpanSelector, Recording, selected_psd, spectrogram_data, display_trace, PHASES
    if _ANALYSIS_READY:
        return
    import os
    cache=Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.CacheLocation))/'matplotlib'
    if getattr(sys,'frozen',False):
        import hashlib
        # A one-folder bundle has stable font paths; isolate moved/renamed builds.
        cache=cache/hashlib.sha256(str(Path(sys._MEIPASS).resolve()).encode()).hexdigest()[:12]
    if getattr(sys,'frozen',False) or 'MPLCONFIGDIR' not in os.environ:
        try:
            cache.mkdir(parents=True,exist_ok=True)
            os.environ['MPLCONFIGDIR']=str(cache)
        except OSError:
            pass  # Matplotlib falls back to its own writable cache selection.
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
    from matplotlib.widgets import SpanSelector
    from analysis import Recording, selected_psd, spectrogram_data, display_trace
    from synthetic import PHASES
    configure_plot_style()
    _ANALYSIS_READY=True


def read_tables(*args,**kwargs):
    from analysis import read_tables as read
    return read(*args,**kwargs)


def make_recording(*args,**kwargs):
    from analysis import make_recording as make
    return make(*args,**kwargs)

POOL = ThreadPoolExecutor(max_workers=2)

STYLE = """
QMainWindow, QWidget { background: #f5f7fb; color: #293950; font-family: 'Helvetica Neue'; font-size: 12px; }
QFrame#sidebar { background: #edf2f8; border: 0; }
QLabel { background: transparent; }
QLabel#brand { font-size: 23px; font-weight: 700; color: #233750; }
QLabel#section { color: #75869c; font-size: 10px; font-weight: 600; letter-spacing: 1px; }
QLabel#muted { color: #7b8ba0; }
QPushButton { background: #e9eef6; color: #405774; border: 1px solid transparent; border-radius: 16px; padding: 9px 16px; font-weight: 500; }
QPushButton:hover { background: #dee8f6; color: #285393; }
QPushButton:pressed { background: #cfddf1; }
QPushButton:focus { border: 1px solid #9fbbe5; }
QPushButton#primary { color: white; background: #5683cf; border: 1px solid transparent; font-weight: 600; }
QPushButton#primary:hover { background: #4776c3; }
QPushButton#primary:pressed { background: #3d67ad; }
QPushButton:disabled { color: #a1adbe; background: #edf0f5; }
QLineEdit, QComboBox, QDoubleSpinBox { background: #ffffff; border: 1px solid #e8edf5; border-radius: 12px; padding: 8px 12px; min-height: 18px; selection-background-color: #dbe7fa; selection-color: #294b7b; }
QLineEdit:hover, QComboBox:hover, QDoubleSpinBox:hover { border: 1px solid #d7e2f2; }
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus { border: 1px solid #9fbbe5; }
QComboBox { padding-right: 30px; }
QComboBox::drop-down { width: 0px; border: 0; }
QComboBox::down-arrow { image: none; width: 0px; height: 0px; }
QComboBox QAbstractItemView { background: white; border: 1px solid #e5ebf3; padding: 6px; selection-background-color: #e3ecfa; selection-color: #294b7b; outline: 0; }
QListWidget { background: transparent; border: 0; outline: 0; }
QListWidget::item { padding: 14px 12px; margin: 4px 0; border-radius: 13px; }
QListWidget::item:selected { background: #dde8f8; color: #305c9c; }
QListWidget::item:hover { background: #e4ecf7; }
QCheckBox { background: transparent; spacing: 9px; color: #637790; }
QToolBar { border: 0; background: #f5f7fb; spacing: 6px; padding: 3px 0; }
QToolButton { background: transparent; color: #617794; border: 1px solid transparent; border-radius: 12px; padding: 7px 12px; }
QToolButton:hover { background: #e5ecf6; color: #315d98; }
QToolButton:checked { background: #dce8fa; color: #315d98; }
QToolButton:disabled { color: #b2bdcb; }
QToolButton:focus { border: 1px solid #9fbbe5; }
QTableWidget { background: white; border: 1px solid #e5ebf3; border-radius: 10px; }
QToolTip { background: #263c59; color: white; border: 0; padding: 7px; }
"""


class SoftCombo(Q.QComboBox):
    """Rounded selector with a light, resolution-independent chevron."""
    def paintEvent(self, event):
        super().paintEvent(event)
        painter=QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen=QtGui.QPen(QtGui.QColor('#8b9bb0'),1.5)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        x,y=self.width()-19,self.height()/2
        path=QtGui.QPainterPath(); path.moveTo(x-3,y-1.5); path.lineTo(x,y+1.5); path.lineTo(x+3,y-1.5)
        painter.drawPath(path); painter.end()


class SoftSpin(Q.QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(Q.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setToolTip('Type a value, or use the up and down arrow keys.')



def configure_style(app):
    app.setStyle('Fusion')
    palette=QtGui.QPalette()
    for role,color in [('Window','#f5f7fb'),('WindowText','#203149'),('Base','#ffffff'),('Text','#203149'),('Button','#f5f7fb'),('ButtonText','#203149'),('Highlight','#2765cf'),('HighlightedText','#ffffff')]:
        palette.setColor(getattr(QtGui.QPalette.ColorRole,role),QtGui.QColor(color))
    app.setPalette(palette); app.setStyleSheet(STYLE)


def configure_plot_style():
    from matplotlib import rcParams
    rcParams.update({'font.family':'DejaVu Sans', 'font.size':9, 'axes.titlesize':10,
                     'axes.titleweight':'bold', 'axes.labelcolor':'#4a5e78',
                     'text.color':'#203149', 'xtick.color':'#63758c', 'ytick.color':'#63758c',
                     'axes.edgecolor':'#d6e0eb', 'axes.spines.top':False, 'axes.spines.right':False,
                     'grid.color':'#e3eaf2', 'axes.facecolor':'white', 'figure.facecolor':'#f5f7fb',
                     'savefig.facecolor':'white', 'axes.prop_cycle': __import__('cycler').cycler(color=['#2988cf'])})



def plot_psd(ax, frequency, density):
    # Logarithmic axes cannot display DC or nonpositive density. Keep raw data
    # unchanged so CSV exports still contain every computed bin.
    valid=(frequency>0)&(density>0)&np.isfinite(density)
    ax.set_xscale('log'); ax.set_yscale('log')
    if np.any(valid):
        ax.plot(frequency[valid],density[valid],linewidth=1)
    else:
        ax.text(.5,.5,'No positive spectral power to display',transform=ax.transAxes,
                ha='center',va='center',color='#8293a9')
    ax.grid(which='both',alpha=.2)


class Jobs:
    """Poll worker futures on the GUI thread; never mutate Qt from a worker."""
    def setup_jobs(self):
        self.jobs = []
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll_jobs)
        self.timer.start(80)

    def submit(self, fn, success, error):
        self.jobs.append((POOL.submit(fn), success, error))

    def poll_jobs(self):
        ready = [j for j in self.jobs if j[0].done()]
        self.jobs = [j for j in self.jobs if not j[0].done()]
        for future, success, error in ready:
            try:
                value = future.result()
            except Exception as exc:
                error(str(exc))
            else:
                success(value)


class ImportDialog(Q.QDialog):
    def __init__(self, path, tables, parent):
        super().__init__(parent)
        self.setWindowTitle('Map columns — ' + Path(path).name)
        self.resize(740, 540)
        self.path, self.tables = path, tables
        layout = Q.QVBoxLayout(self)
        layout.addWidget(Q.QLabel('Choose a sheet/table, time source, and one or more acceleration channels.'))
        form = Q.QFormLayout()
        self.sheet = SoftCombo(); self.sheet.addItems([str(k) for k in tables])
        self.time = SoftCombo()
        self.scale = SoftCombo(); self.scale.addItems(['Seconds', 'Milliseconds', 'Microseconds'])
        self.rate = SoftSpin(); self.rate.setRange(.000001, 1e9); self.rate.setDecimals(6); self.rate.setValue(1000)
        self.unit = SoftCombo(); self.unit.addItems(['m/s²', 'g', 'ft/s²'])
        for label, widget in [('Sheet / table', self.sheet), ('Time column', self.time), ('Time units', self.scale), ('Sample rate (Hz), if no time column', self.rate), ('Acceleration input units', self.unit)]:
            form.addRow(label, widget)
        layout.addLayout(form)
        self.channels = Q.QListWidget(); self.channels.setSelectionMode(Q.QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(Q.QLabel('Acceleration columns (click to select multiple):'))
        layout.addWidget(self.channels)
        self.preview = Q.QTableWidget(); self.preview.setEditTriggers(Q.QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.preview)
        self.message = Q.QLabel(); self.message.setWordWrap(True); layout.addWidget(self.message)
        buttons = Q.QDialogButtonBox(Q.QDialogButtonBox.StandardButton.Ok | Q.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
        self.sheet.currentIndexChanged.connect(self.populate)
        self.populate()

    def populate(self):
        self.table = list(self.tables.values())[self.sheet.currentIndex()]
        self.columns = list(self.table.columns)
        self.time.clear(); self.time.addItem('No time column — use sample rate')
        self.time.addItems([str(c) for c in self.columns])
        preferred = next((i for i, c in enumerate(self.columns) if str(c).lower() in ['time', 'time_s', 't', 'seconds', 'time_ms']), 0)
        self.time.setCurrentIndex(preferred + 1)
        self.channels.clear()
        for i, c in enumerate(self.columns):
            item = Q.QListWidgetItem(str(c)); self.channels.addItem(item)
            item.setSelected(i != preferred)
        self.preview.setRowCount(min(5, len(self.table))); self.preview.setColumnCount(len(self.columns))
        self.preview.setHorizontalHeaderLabels([str(c) for c in self.columns])
        for r in range(self.preview.rowCount()):
            for c in range(len(self.columns)):
                self.preview.setItem(r, c, Q.QTableWidgetItem(str(self.table.iloc[r, c])))

    def validate(self):
        selected = [self.channels.row(i) for i in self.channels.selectedItems()]
        tc = self.time.currentIndex() - 1
        if not selected or tc in selected:
            self.message.setText('Select at least one acceleration column, excluding the time column.')
            return
        self.mapping = (None if tc < 0 else self.columns[tc], [self.columns[i] for i in selected],
                        [1, .001, .000001][self.scale.currentIndex()], self.rate.value(), self.unit.currentText())
        self.accept()


class AnalysisWindow(Q.QMainWindow, Jobs):
    def __init__(self, rec):
        ensure_analysis()
        super().__init__()
        self.rec = rec; self.psd = None; self.spectral = None; self.generation = 0; self.psd_generation = 0
        self.setWindowTitle('LaunchDSP — ' + rec.name); self.resize(1180, 930)
        self.setup_jobs()
        root = Q.QWidget(); self.setCentralWidget(root); layout = Q.QVBoxLayout(root); layout.setContentsMargins(16,12,16,12); layout.setSpacing(10)
        title_row = Q.QHBoxLayout(); title_row.addWidget(Q.QLabel('RECORDING'))
        self.title_edit = Q.QLineEdit(rec.name); self.title_edit.setMinimumWidth(260); self.title_edit.editingFinished.connect(self.retitle)
        title_row.addWidget(self.title_edit); layout.addLayout(title_row)
        meta = Q.QLabel(f'{len(rec.time):,} samples   •   {rec.fs:,.0f} Hz   •   {rec.time[-1]-rec.time[0]:.1f} seconds   •   {rec.unit} → g²/Hz'); meta.setObjectName('muted'); layout.addWidget(meta)
        settings = Q.QHBoxLayout()
        self.segment = SoftCombo(); self.segment.addItems(['128','256','512','1024','2048','4096','8192','16384','32768']); self.segment.setCurrentText('4096')
        self.overlap = SoftCombo(); self.overlap.addItems(['0%', '50%', '75%']); self.overlap.setCurrentIndex(1)
        self.detrend = SoftCombo(); self.detrend.addItems(['Remove segment mean', 'Remove linear trend', 'None'])
        for label, widget in [('Segment',self.segment),('Overlap',self.overlap),('Detrend',self.detrend)]:
            settings.addWidget(Q.QLabel(label)); settings.addWidget(widget)
        apply = Q.QPushButton('Apply settings'); apply.clicked.connect(self.refresh); settings.addWidget(apply)
        layout.addLayout(settings)
        self.figure = Figure(figsize=(11,7), layout='constrained'); self.figure.set_constrained_layout_pads(w_pad=.16,h_pad=.16,wspace=.10,hspace=.10)
        self.canvas = FigureCanvasQTAgg(self.figure)
        grid = self.figure.add_gridspec(2,2,height_ratios=[1,1.12]); self.ax_time=self.figure.add_subplot(grid[0,:]); self.ax_spec=self.figure.add_subplot(grid[1,0]); self.ax_psd=self.figure.add_subplot(grid[1,1])
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        labels={'Home':'Home','Back':'Back','Forward':'Forward','Pan':'Pan','Zoom':'Zoom','Subplots':'Layout','Customize':'Style','Save':'Save'}
        for action in self.toolbar.actions():
            if not action.isSeparator():
                action.setIcon(QtGui.QIcon())
                action.setText(labels.get(action.text(),action.text()))
        self.toolbar._actions['home'].triggered.disconnect()
        self.toolbar._actions['home'].triggered.connect(self.home_view)
        self.toolbar._actions['home'].setToolTip('Restore the full time history; keep the PSD selection.')
        self.toolbar.setMinimumHeight(40)
        layout.addWidget(self.toolbar); layout.addWidget(self.canvas, 1)
        tx, ax = display_trace(rec.time, rec.acceleration)
        self.time_line, = self.ax_time.plot(tx, ax, linewidth=.55)
        if rec.source == 'Synthetic demo':
            for name, a, b in PHASES:
                self.ax_time.axvspan(a,b,color='#8bc7a2',alpha=.20,zorder=0)
                self.ax_time.text((a+b)/2,.94,name,transform=self.ax_time.get_xaxis_transform(),ha='center',va='top',fontsize=8,color='#326847')
        self.ax_time.set_xlabel('Time (s)'); self.ax_time.set_ylabel(f'Acceleration ({rec.unit})'); self.ax_time.grid(alpha=.2)
        self.selector = SpanSelector(self.ax_time, self.select, 'horizontal', useblit=True,
                                     interactive=True, drag_from_anywhere=True, props={'alpha':.2,'facecolor':'tab:blue'})
        self.ax_time.set_xlim(float(rec.time[0]),float(rec.time[-1]))
        self.home_ylim=self.ax_time.get_ylim()
        self.ax_time.callbacks.connect('xlim_changed',self.refresh_visible_trace)
        self.hover_annotation=None; self.hover_marker=None; self.hover_index=None
        self.canvas.mpl_connect('scroll_event',self.scroll_time)
        self.canvas.mpl_connect('motion_notify_event',self.hover_psd)
        self.canvas.mpl_connect('figure_leave_event',self.clear_hover)
        selection = Q.QHBoxLayout()
        self.start = SoftSpin(); self.end = SoftSpin()
        for widget, value, label in [(self.start, rec.time[0], 'Start (s)'), (self.end,rec.time[-1], 'End (s)')]:
            widget.setDecimals(8); widget.setRange(float(rec.time[0]), float(rec.time[-1])); widget.setValue(float(value))
            selection.addWidget(Q.QLabel(label)); selection.addWidget(widget)
        compute = Q.QPushButton('Calculate PSD'); compute.setObjectName('primary'); compute.clicked.connect(lambda: self.select(self.start.value(),self.end.value()))
        full = Q.QPushButton('Full recording'); full.clicked.connect(lambda: self.select(rec.time[0], rec.time[-1]))
        selection.addWidget(compute); selection.addWidget(full); layout.addLayout(selection)
        exports = Q.QHBoxLayout()
        self.export_kind = SoftCombo(); self.export_kind.addItems(['All plots','Time history','Spectrogram','PSD'])
        exports.addWidget(self.export_kind)
        export_plot = Q.QPushButton('Export plot…'); export_plot.clicked.connect(self.export_plot); exports.addWidget(export_plot)
        self.export_csv = Q.QPushButton('Export PSD CSV…'); self.export_csv.clicked.connect(self.export_data); self.export_csv.setEnabled(False); exports.addWidget(self.export_csv)
        exports.addStretch(); layout.addLayout(exports)
        self.status = Q.QLabel('Scroll over time history to zoom; Home restores the full view. Drag to select. Hover over PSD for exact values.'); self.status.setWordWrap(True); layout.addWidget(self.status)
        self.colorbar = None; self.retitle(); self.refresh()
        self.ax_psd.text(.5,.5,'Select a time interval above\nto calculate the PSD',transform=self.ax_psd.transAxes,ha='center',va='center',color='#8293a9',linespacing=1.8)

    def refresh_visible_trace(self,axes):
        left,right=sorted(axes.get_xlim())
        lo=max(0,int(np.searchsorted(self.rec.time,left))-1)
        hi=min(len(self.rec.time),int(np.searchsorted(self.rec.time,right))+1)
        t,y=display_trace(self.rec.time[lo:hi],self.rec.acceleration[lo:hi])
        self.time_line.set_data(t,y)

    def scroll_time(self,event):
        if event.inaxes is not self.ax_time or event.xdata is None or not event.step:
            return
        left,right=self.ax_time.get_xlim()
        full_left,full_right=float(self.rec.time[0]),float(self.rec.time[-1])
        full_width=full_right-full_left
        width=np.clip((right-left)*1.25**(-np.clip(event.step,-12,12)),16/self.rec.fs,full_width)
        fraction=np.clip((event.xdata-left)/(right-left),0,1)
        start=float(np.clip(event.xdata-fraction*width,full_left,full_right-width))
        self.ax_time.set_xlim(start,start+width)
        self.canvas.draw_idle()

    def home_view(self,*args):
        self.ax_time.set_xlim(float(self.rec.time[0]),float(self.rec.time[-1]))
        self.ax_time.set_ylim(self.home_ylim)
        self.canvas.draw_idle()

    def clear_hover(self,event=None):
        changed=False
        for artist in (self.hover_annotation,self.hover_marker):
            if artist is not None and artist.get_visible():
                artist.set_visible(False); changed=True
        self.hover_index=None
        if changed:self.canvas.draw_idle()

    def hover_psd(self,event):
        if event.inaxes is not self.ax_psd or self.psd is None or self.hover_annotation is None:
            self.clear_hover(); return
        f,p,_=self.psd
        valid=np.flatnonzero((f>0)&(p>0)&np.isfinite(p))
        if not len(valid):self.clear_hover(); return
        # Nearest displayed sample in screen pixels respects both log axes.
        points=self.ax_psd.transData.transform(np.column_stack([f[valid],p[valid]]))
        box=self.ax_psd.bbox
        visible=(points[:,0]>=box.x0)&(points[:,0]<=box.x1)&(points[:,1]>=box.y0)&(points[:,1]<=box.y1)
        valid=valid[visible];points=points[visible]
        if not len(valid):self.clear_hover();return
        i=int(valid[np.argmin(np.sum((points-[event.x,event.y])**2,axis=1))])
        self.hover_index=i
        self.hover_marker.set_data([f[i]],[p[i]]); self.hover_marker.set_visible(True)
        self.hover_annotation.xy=(f[i],p[i])
        self.hover_annotation.set_text(f'{f[i]:.6g} Hz\n{p[i]:.6g} g²/Hz')
        right=event.x>(box.x0+box.x1)/2; top=event.y>(box.y0+box.y1)/2
        self.hover_annotation.set_position((-12 if right else 12,-14 if top else 14))
        self.hover_annotation.set_ha('right' if right else 'left')
        self.hover_annotation.set_va('top' if top else 'bottom')
        self.hover_annotation.set_visible(True);self.canvas.draw_idle()

    def options(self):
        return int(self.segment.currentText()), [0,.5,.75][self.overlap.currentIndex()], ['constant','linear',False][self.detrend.currentIndex()]

    def retitle(self):
        title = self.title_edit.text().strip() or self.rec.name
        self.ax_time.set_title(title + '  /  Time history',loc='left')
        self.ax_spec.set_title('Spectrogram',loc='left')
        suffix = '' if self.psd is None else f" ({self.psd[2]['start']:.6g}–{self.psd[2]['end']:.6g} s)"
        self.ax_psd.set_xscale('log'); self.ax_psd.set_yscale('log')
        self.ax_psd.set_title('Power spectral density' + suffix,loc='left')
        self.ax_spec.set_title(''); self.ax_psd.set_title('')
        self.canvas.draw_idle()

    def refresh(self):
        self.generation += 1; generation = self.generation
        options = self.options(); self.current_options = options
        self.spectral = None
        if self.colorbar is not None:
            self.colorbar.remove(); self.colorbar = None
        self.ax_spec.clear(); self.ax_spec.set_title('Calculating spectrogram…'); self.canvas.draw_idle()
        self.submit(lambda: spectrogram_data(self.rec, *options),
                    lambda result: self.show_spectrogram(result) if generation == self.generation else None,
                    lambda error: self.status.setText(error) if generation == self.generation else None)
        if self.psd is not None or self.psd_generation > 0:
            self.select(self.start.value(), self.end.value())
        else:
            self.ax_psd.set_xlabel('Frequency (Hz)'); self.ax_psd.set_ylabel('PSD (g²/Hz)')
            self.retitle()

    def show_spectrogram(self, result):
        self.spectral = result
        f,t,p = result
        mesh = self.ax_spec.pcolormesh(t,f,p,shading='auto',cmap='viridis',vmin=float(np.max(p))-80,vmax=float(np.max(p)),rasterized=True)
        self.colorbar = self.figure.colorbar(mesh, ax=self.ax_spec, pad=.015)
        self.colorbar.set_label('dB re 1 g²/Hz')
        self.ax_spec.set_xlabel('Time (s)'); self.ax_spec.set_ylabel('Frequency (Hz)'); self.retitle()

    def select(self, a, b):
        a, b = sorted((max(float(a),self.rec.time[0]),min(float(b),self.rec.time[-1])))
        self.start.setValue(a); self.end.setValue(b); self.selector.extents = (a,b)
        self.psd_generation += 1; generation = self.psd_generation
        options = self.current_options
        self.clear_hover(); self.hover_annotation=None; self.hover_marker=None
        self.psd = None; self.export_csv.setEnabled(False); self.ax_psd.clear(); self.ax_psd.set_title('Calculating PSD…'); self.canvas.draw_idle()
        self.status.setText('Calculating selected-window PSD…')
        self.submit(lambda: selected_psd(self.rec,a,b,*options),
                    lambda result: self.show_psd(result,options) if generation == self.psd_generation else None,
                    lambda error: self.psd_error(error) if generation == self.psd_generation else None)

    def psd_error(self, error):
        self.status.setText(error); self.ax_psd.set_xlabel('Frequency (Hz)'); self.ax_psd.set_ylabel('PSD (g²/Hz)'); self.retitle()

    def show_psd(self, result, options):
        self.psd = result; self.psd_options = options; f,p,meta = result
        self.ax_psd.clear(); plot_psd(self.ax_psd,f,p)
        self.ax_psd.set_xlabel('Frequency (Hz)'); self.ax_psd.set_ylabel('PSD (g²/Hz)'); self.ax_psd.grid(which='both',alpha=.2)
        self.hover_marker,=self.ax_psd.plot([],[],'o',markersize=5,color='#4776c3',visible=False,zorder=8)
        self.hover_annotation=self.ax_psd.annotate('',xy=(1,1),xytext=(12,14),textcoords='offset points',
            bbox={'boxstyle':'round,pad=.5','fc':'#eef3fc','ec':'#b9ccea','alpha':.97},
            fontsize=9,visible=False,zorder=9)
        self.export_csv.setEnabled(True); self.retitle()
        self.status.setText(f"{meta['samples']:,} samples | Fs {self.rec.fs:.6g} Hz | Δf {meta['df']:.6g} Hz | {meta['averages']} averages | Hann ENBW {meta['enbw']:.4g} Hz | Raw window RMS {meta['rms']:.6g} {self.rec.unit}. Welch PSD. Longer segments resolve closer tones; shorter selections isolate transient events.")

    def export_plot(self):
        self.clear_hover()
        kind = self.export_kind.currentText()
        if kind in ['PSD','All plots'] and self.psd is None:
            Q.QMessageBox.information(self,'Select an interval','Calculate a valid PSD before exporting this view.'); return
        if kind in ['Spectrogram','All plots'] and self.spectral is None:
            Q.QMessageBox.information(self,'Spectrogram pending','Wait for the spectrogram to finish.'); return
        path, _ = Q.QFileDialog.getSaveFileName(self,'Export plot',kind.replace(' ','_')+'.png','PNG (*.png);;PDF (*.pdf);;SVG (*.svg)')
        if not path: return
        try:
            if kind == 'All plots':
                self.figure.savefig(path,dpi=200)
            else:
                fig = Figure(figsize=(10,5),layout='constrained'); ax = fig.subplots()
                if kind == 'Time history':
                    t,y=display_trace(self.rec.time,self.rec.acceleration); ax.plot(t,y,linewidth=.65)
                    ax.set(xlabel='Time (s)',ylabel=f'Acceleration ({self.rec.unit})',title=self.ax_time.get_title(loc='left'))
                    if self.psd: ax.axvspan(self.psd[2]['start'],self.psd[2]['end'],alpha=.2)
                elif kind == 'Spectrogram':
                    f,t,p=self.spectral; mesh=ax.pcolormesh(t,f,p,shading='auto',cmap='viridis',vmin=float(np.max(p))-80,vmax=float(np.max(p)),rasterized=True)
                    fig.colorbar(mesh,ax=ax,label='dB re 1 g²/Hz')
                    ax.set(xlabel='Time (s)',ylabel='Frequency (Hz)',title=self.title_edit.text()+' — Spectrogram')
                else:
                    f,p,_=self.psd; plot_psd(ax,f,p)
                    ax.set(xlabel='Frequency (Hz)',ylabel='PSD (g²/Hz)',title=self.title_edit.text()+' — '+self.ax_psd.get_title(loc='left'))
                fig.savefig(path,dpi=200)
            self.status.setText('Saved ' + path)
        except Exception as exc: Q.QMessageBox.warning(self,'Export failed',str(exc))

    def export_data(self):
        if self.psd is None: return
        path,_=Q.QFileDialog.getSaveFileName(self,'Export PSD data','psd.csv','CSV (*.csv)')
        if not path: return
        try:
            f,p,m=self.psd
            with open(path,'w',newline='',encoding='utf-8') as stream:
                writer=csv.writer(stream)
                writer.writerow(['frequency_Hz','PSD_g^2_per_Hz','start_s','end_s','sample_rate_Hz','segment_samples','overlap_fraction','detrend','source','channel'])
                for freq,power in zip(f,p): writer.writerow([freq,power,m['start'],m['end'],self.rec.fs,m['segment'],self.psd_options[1],self.psd_options[2],self.rec.source,self.rec.name])
            self.status.setText('Saved '+path)
        except Exception as exc: Q.QMessageBox.warning(self,'Export failed',str(exc))


class Library(Q.QMainWindow, Jobs):
    def __init__(self):
        super().__init__(); self.setup_jobs(); self.windows=[]; self.records=[]; self.queue=[]
        self.setWindowTitle('LaunchDSP'); self.resize(1440,900); self.setMinimumSize(1140,720)
        root=Q.QWidget(); self.setCentralWidget(root); layout=Q.QHBoxLayout(root); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        side=Q.QFrame(); side.setObjectName('sidebar'); side.setFixedWidth(272)
        sidebar=Q.QVBoxLayout(side); sidebar.setContentsMargins(20,24,20,20); sidebar.setSpacing(12)
        heading=Q.QLabel('LaunchDSP'); heading.setObjectName('brand'); sidebar.addWidget(heading)
        subtitle=Q.QLabel('VIBRATION ANALYSIS'); subtitle.setObjectName('section'); sidebar.addWidget(subtitle); sidebar.addSpacing(14)
        self.import_button=Q.QPushButton('+  Import recordings'); self.import_button.setObjectName('primary'); self.import_button.clicked.connect(self.import_files); sidebar.addWidget(self.import_button)
        self.header=Q.QCheckBox('CSV has column headers'); self.header.setChecked(True); sidebar.addWidget(self.header)
        defaults=Q.QLabel('CSV / MAT  •  seconds  •  m/s²\nChoose columns and units on import.'); defaults.setObjectName('muted'); defaults.setWordWrap(True); sidebar.addWidget(defaults)
        self.demo_button=Q.QPushButton('Load synthetic flights'); self.demo_button.clicked.connect(self.demo); sidebar.addWidget(self.demo_button)
        sidebar.addSpacing(12); self.count=Q.QLabel('RECORDINGS  /  0'); self.count.setObjectName('section'); sidebar.addWidget(self.count)
        self.search=Q.QLineEdit(); self.search.setPlaceholderText('Filter recordings…'); self.search.textChanged.connect(self.filter_records); sidebar.addWidget(self.search)
        self.file_list=Q.QListWidget(); self.file_list.currentRowChanged.connect(self.open_recording); sidebar.addWidget(self.file_list,1)
        self.status=Q.QLabel('Local analysis. Your recordings stay on this computer.'); self.status.setObjectName('muted'); self.status.setWordWrap(True); sidebar.addWidget(self.status)
        layout.addWidget(side)
        self.stack=Q.QStackedWidget(); layout.addWidget(self.stack,1)
        empty=Q.QWidget(); el=Q.QVBoxLayout(empty); el.setContentsMargins(25,25,25,25)
        title=Q.QLabel('Your flight analysis workspace'); title.setStyleSheet('font-size: 22px; font-weight: 600'); el.addWidget(title)
        el.addWidget(Q.QLabel('Import a recording or load synthetic flights to get started.'))
        placeholders=Q.QGridLayout(); placeholders.setSpacing(18)
        for row,col,span,name,hint in [(0,0,2,'Time history','Acceleration versus time · scroll to zoom · drag to select'),(1,0,1,'Spectrogram','Frequency content over the flight'),(1,1,1,'Power spectral density','Frequency content of your selection')]:
            card=Q.QFrame();card.setObjectName('chartPlaceholder')
            card.setStyleSheet('QFrame#chartPlaceholder { background: white; border: 1px solid #e8edf5; border-radius: 16px; }')
            box=Q.QVBoxLayout(card);box.setContentsMargins(22,20,22,20)
            label=Q.QLabel(name);label.setStyleSheet('font-size: 14px; font-weight: 600;');box.addWidget(label)
            body=Q.QLabel(hint);body.setObjectName('muted');body.setWordWrap(True);body.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            box.addWidget(body,1);placeholders.addWidget(card,row,col,1,span)
        placeholders.setRowStretch(0,1);placeholders.setRowStretch(1,1)
        placeholders.setColumnStretch(0,1);placeholders.setColumnStretch(1,1)
        el.addLayout(placeholders,1); self.stack.addWidget(empty)

    def filter_records(self,text):
        for i in range(self.file_list.count()):
            self.file_list.item(i).setHidden(text.lower() not in self.records[i].name.lower())

    def import_files(self):
        paths,_=Q.QFileDialog.getOpenFileNames(self,'Import acceleration histories','','Data (*.csv *.txt *.tsv *.xlsx *.mat);;All files (*)')
        if not paths: return
        self.queue=list(paths); self.import_header=self.header.isChecked(); self.import_button.setEnabled(False); self.next_import()

    def next_import(self):
        if not self.queue:
            self.import_button.setEnabled(True); self.status.setText(f'{len(self.records)} recordings loaded. Click a row to analyze.'); return
        path=self.queue.pop(0); self.status.setText('Reading '+Path(path).name+'…')
        self.submit(lambda:read_tables(path,self.import_header),lambda tables:self.map_file(path,tables),lambda error:self.import_error(path,error))

    def import_error(self,path,error):
        Q.QMessageBox.warning(self,'Could not import '+Path(path).name,error); self.next_import()

    def map_file(self,path,tables):
        dialog=ImportDialog(path,tables,self)
        if dialog.exec() != Q.QDialog.DialogCode.Accepted:
            self.next_import(); return
        tc,channels,scale,rate,unit=dialog.mapping; table=dialog.table
        def build():
            return [make_recording(table,tc,c,scale,rate,unit,path,Path(path).stem+' / '+str(c)) for c in channels]
        self.submit(build,self.import_complete,lambda error:self.import_error(path,error))

    def import_complete(self,records):
        for rec in records:self.add_recording(rec)
        self.next_import()

    def add_recording(self,rec):
        self.records.append(rec)
        item=Q.QListWidgetItem(f'{rec.name}\n{rec.fs:,.0f} Hz  ·  {rec.time[-1]-rec.time[0]:.0f} s  ·  {rec.unit}')
        item.setToolTip(rec.source); self.file_list.addItem(item)
        self.count.setText(f'RECORDINGS  /  {len(self.records)}'); self.filter_records(self.search.text())
        if len(self.records)==1:self.file_list.setCurrentRow(0)

    def open_recording(self,row):
        if row<0:return
        rec=self.records[row]
        for window in self.windows:
            if window.rec is rec:
                self.stack.setCurrentWidget(window); return
        window=AnalysisWindow(rec); window.setWindowFlags(QtCore.Qt.WindowType.Widget)
        self.windows.append(window); self.stack.addWidget(window); self.stack.setCurrentWidget(window)

    def demo(self):
        self.demo_button.setEnabled(False); self.status.setText('Generating three synthetic launch flights…')
        def generate():
            from synthetic import generate_flight
            from analysis import Recording
            records=[]
            for i in range(3):
                data=generate_flight(i)
                records.append(Recording(f'Synthetic flight {i+1:02d} / Z',data['time_s'],data['accel_z_m_s2'],'m/s²','Synthetic demo',1000.))
            return records
        def loaded(records):
            for rec in records:self.add_recording(rec)
            self.status.setText('Synthetic data · lift-off 0–10 s, transonic 35–52 s, max q 62–72 s. Select a phase to compare PSDs.')
        self.submit(generate,loaded,self.demo_error)

    def demo_error(self,error):
        self.demo_button.setEnabled(True); self.status.setText(error)

    def closeEvent(self,event):
        for window in self.windows:window.close()
        super().closeEvent(event)


def main():
    app=Q.QApplication(sys.argv); app.setApplicationName('LaunchDSP'); configure_style(app)
    window=Library(); window.show()
    code=app.exec(); POOL.shutdown(wait=False,cancel_futures=True); sys.exit(code)


if __name__=='__main__':main()
