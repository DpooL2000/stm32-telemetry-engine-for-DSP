# STM32G431 Betaflight Signal Processing & Telemetry Engine

An ultra-low latency hardware testbed and real-time telemetry dashboard for evaluating digital signal processing (DSP) filter pipelines on an STM32G431 (ARM Cortex-M4F) microcontroller paired with an MPU6050 IMU on a single-axis motor arm setup.

## 🚀 Key Features

* **Hardware CORDIC Acceleration:** Utilizes the STM32G431 hardware CORDIC co-processor for single-cycle trigonometric calculations during bi-quad filter coefficient synthesis.
* **Betaflight Signal Chain:** Full C++ implementation of PT1, PT2 (cascaded), and Biquad Butterworth low-pass filters alongside a dynamic biquad notch filter.
* **44-Byte Packed Binary Telemetry:** Replaces slow ASCII serial output with a high-throughput binary struct locked by frame magic word (`0xDDBBCCAA`) over USB CDC at 1kHz.
* **PySide6 Reactive GUI:** Dark-themed Opera GX aesthetic interface for real-time serial parsing, attitude estimation (Roll/Pitch/Yaw), pipeline group delay (latency) prediction, and interactive parameter tuning.
* **Live Resonance Analysis (FFT):** Python-side Fast Fourier Transform engine running over rolling 1000-sample buffers to detect dominant vibration frequencies and mechanical harmonics.

## System Architecture

1. **Sensor Layer:** MPU6050 configured with hardware anti-aliasing DLPF (44Hz / 1kHz sample rate).
2. **Processing Layer:** STM32G431 running a deterministic 1kHz loop, reading raw IMU data over 400kHz I2C (`PB6`/`PB7` or `PB8`/`PB9`), executing filter math via FPU/CORDIC, and estimating attitude via a Complementary Filter.
3. **Visualization Layer:** Non-blocking multi-threaded PySide6 dashboard receiving 44-byte frames at 1kHz while pushing dynamic parameter updates at 4Hz.

## Requirements

* **Microcontroller:** STM32G431KB / STM32G431C8
* **Sensor:** MPU6050 Accelerometer/Gyroscope
* **Python Runtime:** 3.10+
* **Dependencies:** `pyside6`, `pyserial`, `numpy`, `matplotlib`

## Setup & Execution

### Firmware
Build and flash the STM32 project using PlatformIO or Arduino IDE with the STM32 Cores package enabled. Ensure Hardware FPU and CORDIC support are enabled.

### Desktop GUI
```bash
cd desktop_gui
pip install -r requirements.txt
python main.py
