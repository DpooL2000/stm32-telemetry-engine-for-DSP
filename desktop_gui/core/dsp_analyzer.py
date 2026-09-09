def get_top_peaks(fft_data, freqs, n=3):
    """Finds distinct local maxima in the FFT array"""
    peaks = []
    for i in range(5, len(fft_data) - 1):
        if fft_data[i] > fft_data[i - 1] and fft_data[i] > fft_data[i + 1]:
            if fft_data[i] > 0.5:  # Noise floor threshold
                peaks.append((freqs[i], fft_data[i]))
    peaks.sort(key=lambda x: x[1], reverse=True)

    if not peaks: return "--"
    return ", ".join([f"{p[0]:.0f}Hz" for p in peaks[:n]])
