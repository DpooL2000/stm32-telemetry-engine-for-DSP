import sys
import collections
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QCheckBox,
                               QLabel, QHBoxLayout, QSpinBox, QComboBox, QFrame, QSplitter,
                               QSlider, QPushButton, QGridLayout)
from PySide6.QtCore import Qt, QTimer

# Internal Modules
from ui.styles import MASTER_QSS, setup_dark_plot
from ui.title_bar import CustomTitleBar
from core.serial_worker import SerialLink
from core.dsp_anlyzer import get_top_peaks

class BetaflightTuner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(1600, 850)
        self.setStyleSheet(MASTER_QSS)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(CustomTitleBar(self))

        splitter = QSplitter(Qt.Horizontal)

        # --- LEFT PANEL: BETAFLIGHT CONTROLS ---
        control_scroll = QWidget()
        ctrl_layout = QVBoxLayout(control_scroll)
        ctrl_layout.setAlignment(Qt.AlignTop)

        # 0. Compact Recalibration Header
        top_row = QHBoxLayout()
        top_row.addStretch()
        self.btn_cal = QPushButton("Recalibrate IMU")
        self.btn_cal.setFixedSize(140, 28)
        self.btn_cal.setStyleSheet("""
            QPushButton { background-color: #0f0f13; border: 1px solid #fa1e4e; 
                          color: #fa1e4e; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #fa1e4e; color: #ffffff; }
        """)
        self.btn_cal.clicked.connect(self.trigger_calibration)
        top_row.addWidget(self.btn_cal)
        ctrl_layout.addLayout(top_row)

        # 1. Live Attitude & FFT Peaks Display Frame
        data_frame = QFrame()
        data_frame.setObjectName("controlFrame")
        data_layout = QGridLayout(data_frame)

        data_layout.addWidget(self.make_lbl("Live Attitude (Angles)"), 0, 0, 1, 3)
        self.lbl_roll = QLabel("Roll: 0.0°")
        self.lbl_pitch = QLabel("Pitch: 0.0°")
        self.lbl_yaw = QLabel("Yaw: 0.0°")
        for i, lbl in enumerate([self.lbl_roll, self.lbl_pitch, self.lbl_yaw]):
            lbl.setStyleSheet("color: #00ffcc; font-size: 16px; font-weight: bold;")
            data_layout.addWidget(lbl, 1, i)

        data_layout.addWidget(self.make_lbl("Identified Resonance (Top 3 FFT Peaks)"), 2, 0, 1, 3)
        self.lbl_fft_x = QLabel("X: -- Hz")
        self.lbl_fft_y = QLabel("Y: -- Hz")
        self.lbl_fft_z = QLabel("Z: -- Hz")
        for i, lbl in enumerate([self.lbl_fft_x, self.lbl_fft_y, self.lbl_fft_z]):
            lbl.setStyleSheet("color: #ffaa00; font-size: 14px; font-weight: bold;")
            data_layout.addWidget(lbl, 3, i)

        ctrl_layout.addWidget(data_frame)

        # 2. Gyro Lowpass
        lp_frame = QFrame()
        lp_frame.setObjectName("controlFrame")
        lp_layout = QVBoxLayout(lp_frame)
        lp_layout.addWidget(self.make_lbl("Gyro Lowpass Filters"))

        lp1_row = QHBoxLayout()
        self.chk_lp1 = QCheckBox("Gyro Lowpass 1"); self.chk_lp1.setChecked(True)
        self.cb_lp1_mode = QComboBox(); self.cb_lp1_mode.addItems(["STATIC", "DYNAMIC"])
        self.sp_lp1_cut = QSpinBox(); self.sp_lp1_cut.setRange(0, 1000); self.sp_lp1_cut.setValue(125)
        self.cb_lp1_type = QComboBox(); self.cb_lp1_type.addItems(["PT1", "PT2", "BIQUAD"])
        lp1_row.addWidget(self.chk_lp1); lp1_row.addWidget(self.cb_lp1_mode)
        lp1_row.addWidget(self.sp_lp1_cut); lp1_row.addWidget(self.cb_lp1_type)
        lp_layout.addLayout(lp1_row)

        lp2_row = QHBoxLayout()
        self.chk_lp2 = QCheckBox("Gyro Lowpass 2"); self.chk_lp2.setChecked(True)
        self.sp_lp2_cut = QSpinBox(); self.sp_lp2_cut.setRange(0, 1000); self.sp_lp2_cut.setValue(250)
        self.cb_lp2_type = QComboBox(); self.cb_lp2_type.addItems(["PT1", "PT2", "BIQUAD"])
        lp2_row.addWidget(self.chk_lp2); lp2_row.addWidget(self.sp_lp2_cut); lp2_row.addWidget(self.cb_lp2_type)
        lp_layout.addLayout(lp2_row)
        ctrl_layout.addWidget(lp_frame)

        # 3. Dynamic Notch
        dn_frame = QFrame()
        dn_frame.setObjectName("controlFrame")
        dn_layout = QVBoxLayout(dn_frame)
        dn_layout.addWidget(self.make_lbl("Dynamic Notch Filter"))

        dn_row = QHBoxLayout()
        self.chk_dyn = QCheckBox("Dynamic Notch Filter"); self.chk_dyn.setChecked(True)
        self.sp_dn_cnt = QSpinBox(); self.sp_dn_cnt.setRange(1, 5); self.sp_dn_cnt.setValue(3)
        self.sp_dn_q = QSpinBox(); self.sp_dn_q.setRange(1, 1000); self.sp_dn_q.setValue(250)
        self.sp_dn_min = QSpinBox(); self.sp_dn_min.setRange(10, 500); self.sp_dn_min.setValue(60)
        self.sp_dn_max = QSpinBox(); self.sp_dn_max.setRange(100, 1000); self.sp_dn_max.setValue(350)

        dn_row.addWidget(self.chk_dyn); dn_row.addWidget(QLabel("Count")); dn_row.addWidget(self.sp_dn_cnt)
        dn_row.addWidget(QLabel("Q")); dn_row.addWidget(self.sp_dn_q)
        dn_row.addWidget(QLabel("Min Freq")); dn_row.addWidget(self.sp_dn_min)
        dn_row.addWidget(QLabel("Max Freq")); dn_row.addWidget(self.sp_dn_max)
        dn_layout.addLayout(dn_row)
        ctrl_layout.addWidget(dn_frame)

        # 4. Motor Control Slider
        motor_frame = QFrame()
        motor_frame.setObjectName("controlFrame")
        motor_layout = QVBoxLayout(motor_frame)
        motor_layout.addWidget(self.make_lbl("Motor Duty Cycle (µs)"))

        slider_row = QHBoxLayout()
        self.slider_motor = QSlider(Qt.Horizontal)
        self.slider_motor.setRange(1000, 2000)
        self.slider_motor.setValue(1000)
        self.lbl_motor = QLabel("1000 µs")
        self.lbl_motor.setStyleSheet("color: #00ffcc; font-weight: bold;")

        slider_row.addWidget(self.slider_motor)
        slider_row.addWidget(self.lbl_motor)
        motor_layout.addLayout(slider_row)
        ctrl_layout.addWidget(motor_frame)

        # 5. Latency Readout
        latency_frame = QFrame()
        latency_frame.setObjectName("controlFrame")
        latency_layout = QVBoxLayout(latency_frame)
        latency_layout.addWidget(self.make_lbl("Signal Pipeline Latency"))

        self.lbl_latency = QLabel("0.00 ms")
        self.lbl_latency.setStyleSheet("color: #ffaa00; font-size: 18px; font-weight: bold;")
        latency_layout.addWidget(self.lbl_latency)
        ctrl_layout.addWidget(latency_frame)

        # Hooks
        self.sp_lp1_cut.valueChanged.connect(self.send_parameters)
        self.sp_dn_q.valueChanged.connect(self.send_parameters)
        self.sp_dn_min.valueChanged.connect(self.send_parameters)
        self.sp_dn_max.valueChanged.connect(self.send_parameters)
        self.slider_motor.valueChanged.connect(self.update_motor_lbl)

        splitter.addWidget(control_scroll)

        # --- RIGHT PANEL: LIVE DYNAMIC PLOT ---
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        setup_dark_plot()

        self.fig, (self.ax_time, self.ax_fft) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [2, 1]})
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvas(self.fig)
        plot_layout.addWidget(self.canvas)
        splitter.addWidget(plot_widget)

        splitter.setSizes([350, 1250])
        main_layout.addWidget(splitter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # --- DATA HANDLING ---
        self.data_x = collections.deque(maxlen=1000)
        self.data_y = collections.deque(maxlen=1000)
        self.data_z = collections.deque(maxlen=1000)
        
        # Wrapped in a list so it can be passed by reference to the worker
        self.latest_angles = [0.0, 0.0, 0.0] 
        self.fft_counter = 0

        # Time Domain Setup
        self.line_x, = self.ax_time.plot([], [], color='#fa1e4e', label='Gyro X (deg/s)')
        self.line_y, = self.ax_time.plot([], [], color='#00ffcc', label='Gyro Y (deg/s)')
        self.line_z, = self.ax_time.plot([], [], color='#a020f0', label='Gyro Z (deg/s)')
        self.ax_time.legend(loc='upper right')

        # FFT Domain Setup
        self.line_fft_x, = self.ax_fft.plot([], [], color='#fa1e4e', alpha=0.7)
        self.line_fft_y, = self.ax_fft.plot([], [], color='#00ffcc', alpha=0.7)
        self.line_fft_z, = self.ax_fft.plot([], [], color='#a020f0', alpha=0.7)
        self.notch_line = self.ax_fft.axvline(x=0, color='#ffaa00', linestyle='--', linewidth=2, label='Notch Center')
        self.ax_fft.legend(loc='upper right')
        self.ax_fft.set_xlim(0, 300)
        self.ax_fft.set_ylim(0, 5)
        self.ax_fft.set_xlabel('Frequency (Hz)')

        self.cal_flag = 0

        # Boot Background Serial Worker
        self.com_link = SerialLink('COM16', 115200, self.data_x, self.data_y, self.data_z, self.latest_angles)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(33)

        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.send_parameters)
        self.sync_timer.start(250)

    def make_lbl(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("sectionLabel")
        return lbl

    def update_motor_lbl(self, val):
        self.lbl_motor.setText(f"{val} µs")
        self.send_parameters()

    def trigger_calibration(self):
        self.cal_flag = 1
        self.send_parameters()
        self.cal_flag = 0

    def send_parameters(self):
        lp1_en = 1 if self.chk_lp1.isChecked() else 0
        lp1_cut = self.sp_lp1_cut.value()
        lp1_type = self.cb_lp1_type.currentIndex()

        lp2_en = 1 if self.chk_lp2.isChecked() else 0
        lp2_cut = self.sp_lp2_cut.value()
        lp2_type = self.cb_lp2_type.currentIndex()

        notch_en = 1 if self.chk_dyn.isChecked() else 0
        notch_q = self.sp_dn_q.value()

        notch_min = self.sp_dn_min.value()
        notch_max = self.sp_dn_max.value()
        throttle = self.slider_motor.value()

        # Dynamic Latency Prediction
        total_delay_ms = 0.0
        if lp1_en and lp1_cut > 0:
            if lp1_type == 0: total_delay_ms += (1.0 / (2 * np.pi * lp1_cut)) * 1000
            elif lp1_type == 1: total_delay_ms += (2.0 / (2 * np.pi * lp1_cut)) * 1000
            elif lp1_type == 2: total_delay_ms += (1.414 / (2 * np.pi * lp1_cut)) * 1000
        if lp2_en and lp2_cut > 0:
            if lp2_type == 0: total_delay_ms += (1.0 / (2 * np.pi * lp2_cut)) * 1000
            elif lp2_type == 1: total_delay_ms += (2.0 / (2 * np.pi * lp2_cut)) * 1000
            elif lp2_type == 2: total_delay_ms += (1.414 / (2 * np.pi * lp2_cut)) * 1000

        if hasattr(self, 'lbl_latency'):
            self.lbl_latency.setText(f"{total_delay_ms:.2f} ms")

        cmd = f"{lp1_en},{lp1_cut},{lp1_type},{lp2_en},{lp2_cut},{lp2_type},{notch_en},{notch_q},{notch_min},{notch_max},{throttle},{self.cal_flag}\n"
        self.com_link.send_command(cmd)

    def update_plot(self):
        # 1. Update Live Attitude Readouts
        self.lbl_roll.setText(f"Roll: {self.latest_angles[0]:.1f}°")
        self.lbl_pitch.setText(f"Pitch: {self.latest_angles[1]:.1f}°")
        self.lbl_yaw.setText(f"Yaw: {self.latest_angles[2]:.1f}°")

        # 2. Update Time Domain Plot
        if len(self.data_x) < 2: return
        x_axis = np.arange(len(self.data_x))
        self.line_x.set_data(x_axis, self.data_x)
        self.line_y.set_data(x_axis, self.data_y)
        self.line_z.set_data(x_axis, self.data_z)

        self.ax_time.set_xlim(0, len(self.data_x))
        self.ax_time.relim()
        self.ax_time.autoscale_view(scalex=False, scaley=True)

        # 3. FFT Analysis & Plotting
        if len(self.data_x) == 1000:
            self.fft_counter += 1
            if self.fft_counter % 10 == 0:
                freqs = np.fft.rfftfreq(1000, d=0.001)

                fft_x = np.abs(np.fft.rfft(np.array(self.data_x) - np.mean(self.data_x))) / 1000.0
                fft_y = np.abs(np.fft.rfft(np.array(self.data_y) - np.mean(self.data_y))) / 1000.0
                fft_z = np.abs(np.fft.rfft(np.array(self.data_z) - np.mean(self.data_z))) / 1000.0

                self.line_fft_x.set_data(freqs, fft_x)
                self.line_fft_y.set_data(freqs, fft_y)
                self.line_fft_z.set_data(freqs, fft_z)

                max_amp = max(np.max(fft_x[5:]), np.max(fft_y[5:]), np.max(fft_z[5:]))
                self.ax_fft.set_ylim(0, max_amp * 1.2 if max_amp > 1 else 1)

                throttle_pct = (self.slider_motor.value() - 1000.0) / 1000.0
                current_notch = self.sp_dn_min.value() + throttle_pct * (self.sp_dn_max.value() - self.sp_dn_min.value())
                self.notch_line.set_xdata([current_notch, current_notch])

                self.lbl_fft_x.setText(f"X: {get_top_peaks(fft_x, freqs)}")
                self.lbl_fft_y.setText(f"Y: {get_top_peaks(fft_y, freqs)}")
                self.lbl_fft_z.setText(f"Z: {get_top_peaks(fft_z, freqs)}")

        self.canvas.draw_idle()

    def closeEvent(self, event):
        self.com_link.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BetaflightTuner()
    window.show()
    sys.exit(app.exec())
