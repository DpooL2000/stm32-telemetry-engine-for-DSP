import matplotlib.pyplot as plt

MASTER_QSS = """
QWidget { background-color: transparent; color: #ffffff; }
QMainWindow { background-color: #0f0f13; }
QFrame#controlFrame { border: 1px solid #2a2a35; border-radius: 6px; background-color: #1a1a24; padding: 10px; margin-bottom: 5px; }
QLabel#sectionLabel { color: #fa1e4e; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
QLabel#dataReadout { color: #00ffcc; font-size: 16px; font-weight: bold; }
QSpinBox, QComboBox { background-color: #0f0f13; color: #00ffcc; border: 1px solid #2a2a35; padding: 4px; border-radius: 3px; }
QCheckBox::indicator { width: 36px; height: 18px; border-radius: 9px; border: 2px solid #2a2a35; background: #0f0f13; }
QCheckBox::indicator:checked { background: #ffaa00; border: 2px solid #ffaa00; }
QSlider::groove:horizontal { border: 1px solid #2a2a35; height: 8px; background: #0f0f13; border-radius: 4px; }
QSlider::handle:horizontal { background: #fa1e4e; border: 1px solid #fa1e4e; width: 14px; margin: -4px 0; border-radius: 7px; }
QLabel#mainTitle { color: #fa1e4e; font-family: 'Segoe UI', Arial, sans-serif; font-size: 16px; font-weight: bold; padding-left: 15px; letter-spacing: 2px;}
QPushButton#titleBtn, QPushButton#closeBtn { background-color: transparent; color: #fa1e4e; font-weight: bold; font-size: 16px; border: none; padding: 2px 15px; }
QPushButton#titleBtn:hover { background-color: rgba(250, 30, 78, 0.15); color: #ffffff; }
QPushButton#closeBtn:hover { background-color: #fa1e4e; color: #ffffff; }
"""

def setup_dark_plot():
    plt.style.use('dark_background')
    plt.rcParams.update({
        'figure.facecolor': '#0f0f13', 'axes.facecolor': '#0f0f13', 'axes.edgecolor': '#2a2a35',
        'text.color': '#ffffff', 'xtick.color': '#8a8a93', 'ytick.color': '#8a8a93',
        'grid.color': '#2a2a35', 'lines.color': '#fa1e4e'
    })
