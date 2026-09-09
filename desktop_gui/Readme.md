# GX Telemetry Engine (Desktop GUI)

A real-time, multi-threaded PySide6 dashboard designed to interface with the STM32G431 DSP testbed. This application provides live attitude visualization, interactive filter tuning, and real-time Fast Fourier Transform (FFT) analysis to detect and eliminate mechanical resonance.

https://github.com/user-attachments/assets/3c3b6ea9-1714-42ee-948a-6c1bfa7ee5dc

## Key Features

* **Real-Time FFT Analysis:** Processes rolling 1000-sample buffers to calculate and identify the top 3 resonant frequencies on the X, Y, and Z axes, allowing for surgical dynamic notch placement.
* **Non-Blocking Serial Architecture:** Utilizes a dedicated background thread (`SerialLink`) to ingest 44-byte packed binary telemetry frames at 1kHz over USB CDC without freezing the UI.
* **Deterministic Parameter Sync:** A 4Hz background `QTimer` pushes filter coefficients and toggle states back to the STM32, ensuring the hardware pipeline matches the GUI state without saturating the bus.
* **Mathematical Latency Prediction:** Calculates and displays the theoretical group delay (in milliseconds) introduced by the cascaded IIR filter chain (PT1, PT2, Biquad).
* **Hardware-Accelerated Plotting:** Uses `matplotlib` with a custom dark theme mapped to a PySide6 canvas for smooth ~30 FPS time-domain and frequency-domain rendering.

## Module Architecture

To maintain a clean and scalable codebase, the application is divided into specific sub-modules:

* `main.py`: The entry point. Handles the UI layout, timer initialization, and main thread execution.
* `core/serial_worker.py`: Manages the `pyserial` connection, binary un-packing (`<IIfffffffff`), and data queueing on a separate daemon thread.
* `core/dsp.py`: Contains independent mathematical functions for peak finding and signal analysis.
* `ui/styles.py`: Defines the overarching QSS stylesheets and Matplotlib dark theme parameters.
* `ui/title_bar.py`: A custom frameless window implementation with drag-to-move functionality.

## Installation & Setup

1. **Install Python:** Ensure you have Python 3.10 or higher installed.
2. **Install Dependencies:** Navigate to this directory in your terminal and install the required packages:
   ```bash
   pip install -r requirements.txt
