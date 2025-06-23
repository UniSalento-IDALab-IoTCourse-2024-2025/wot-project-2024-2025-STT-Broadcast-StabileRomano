import sounddevice as sd
import numpy as np
REF_PRESSURE = 2e-5
MIN_DB = 30.0
DEFAULT_FS = 44100
soglia_rumore = 85.0

def misura_rumore_ambientale(durata: float = 5.0, fs: int = DEFAULT_FS) -> float:
    """Funzione di misurazione esistente"""
    try:
        audio = sd.rec(int(durata * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        audio_data = audio.flatten()
        trim_samples = int(0.1 * fs)
        audio_trimmed = audio_data[trim_samples:-trim_samples] if len(audio_data) > 2 * trim_samples else audio_data
        rms = np.sqrt(np.mean(np.square(audio_trimmed)))
        spl = 20 * np.log10(max(rms, 1e-10) / REF_PRESSURE)
        return round(max(spl, MIN_DB), 1)
    except Exception as e:
        print(f"Errore misurazione: {str(e)}")
        return MIN_DB
    
if __name__ == "__main__":
    rumore = misura_rumore_ambientale(durata=5)
    print(f"Rumore acquisito: {rumore}")