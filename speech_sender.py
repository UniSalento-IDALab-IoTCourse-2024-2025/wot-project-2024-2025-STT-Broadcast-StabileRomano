import sounddevice as sd
import numpy as np
import websockets
import json
import speech_recognition as sr
import wave
import io
from typing import Optional
import sys
import signal
import asyncio

connessione_attiva = None

REF_PRESSURE = 2e-5
MIN_DB = 30.0
DEFAULT_FS = 44100

# Stato condiviso
filtro_attivo = False
soglia_rumore = 85.0

async def gestisci_connessione(websocket, path=None):
    global filtro_attivo, soglia_rumore, connessione_attiva
    
    print("Connessione WebSocket stabilita")
    connessione_attiva = websocket
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if 'soglia' in data:
                    soglia_rumore = float(data['soglia'])
                    print(f"Soglia aggiornata: {soglia_rumore} dB")
                
                if 'filtroAttivo' in data:
                    filtro_attivo = bool(data['filtroAttivo'])
                    print(f"Filtro {'attivato' if filtro_attivo else 'disattivato'}")

            except json.JSONDecodeError:
                print("Messaggio non valido ricevuto:", message)

    except websockets.exceptions.ConnectionClosed:
        print("Connessione chiusa dal client")
    finally:
        filtro_attivo = False
        connessione_attiva = None
        print("Client disconnesso")

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
    

async def invia_notifica_WS(rumore: float, soglia_rumore: float):
    """Invia una notifica via WebSocket quando il rumore supera la soglia"""
    global connessione_attiva
    
    if not connessione_attiva:
        return
        
    messaggio = {
        "tipo": "notifica",
        "rumore": float(rumore),
        "soglia": float(soglia_rumore)
    }
    
    try:
        await connessione_attiva.send(json.dumps(messaggio))
        print("Notifica inviata con successo")
    except Exception as e:
        print(f"Errore nell'invio della notifica: {str(e)}")

def acquisisci_audio_e_spl(durata: float = 1.0, fs: int = DEFAULT_FS) -> tuple[float, np.ndarray]:
    """
    Registra audio per una durata specifica e calcola il livello di pressione sonora (SPL).
    Restituisce una tupla: (spl_db, audio_numpy)
    """
    try:
        # Registra l'audio
        audio = sd.rec(int(durata * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()

        audio_data = audio.flatten()

        trim_samples = int(0.1 * fs)
        audio_trimmed = (
            audio_data[trim_samples:-trim_samples]
            if len(audio_data) > 2 * trim_samples
            else audio_data
        )

        # Calcolo SPL (dB(A))
        rms = np.sqrt(np.mean(np.square(audio_trimmed)))
        spl = 20 * np.log10(max(rms, 1e-10) / REF_PRESSURE)
        spl = round(max(spl, MIN_DB), 1)

        return audio_data, spl  # ritorna anche l'audio completo, non solo quello "trimmed"
    
    except Exception as e:
        print(f"Errore durante l'acquisizione audio: {str(e)}")
        return MIN_DB, np.zeros(int(durata * fs))

async def stt_da_registrazione(audio_data: np.ndarray, fs: int = DEFAULT_FS) -> Optional[str]:
    """
    Estrae testo parlato dall'audio (già registrato) usando speech_recognition.
    Modificato per processare solo una volta l'audio ricevuto.
    """
    global filtro_attivo

    if not filtro_attivo:
        return None

    try:
        wav_io = io.BytesIO()
        
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(fs)
            
            # Converti float32 [-1, 1] in PCM 16-bit
            audio_pcm = (audio_data * 32767).astype(np.int16)
            wav_file.writeframes(audio_pcm.tobytes())
        
        wav_io.seek(0)
        
        # Inizializza il recognizer
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)  # Legge tutto il file audio
            
            try:
                testo = recognizer.recognize_google(audio, language='it-IT')
                print("Testo riconosciuto:", testo)
                return testo
                
            except sr.UnknownValueError:
                print("Non sono riuscito a capire l'audio")
            except sr.RequestError as e:
                print(f"Errore nel servizio di riconoscimento vocale: {e}")
                
    except Exception as e:
        print(f"Errore durante STT con speech_recognition: {str(e)}")

    return None

async def monitora_livello_ambientale(fs: int = DEFAULT_FS, intervallo: int = 0.8):
    """Monitoraggio con invio notifiche"""
    global filtro_attivo, soglia_rumore
    
    print("Avvio monitoraggio rumore ambientale...")
    
    while True:
        try:
            audio, rumore = acquisisci_audio_e_spl(durata=7, fs=fs)
            print(f"Rumore attuale: {rumore} dB(A) | Soglia: {soglia_rumore} dB")
            
            if rumore >= soglia_rumore:
                print("Soglia superata! Invio notifica...")
                await invia_notifica_WS(rumore, soglia_rumore)
                
            if filtro_attivo:
                testo = await stt_da_registrazione(audio)
                if testo:
                    print(f"Hai detto: {testo}")
               
        except Exception as e:
            print(f"Errore monitoraggio: {str(e)}")
            await asyncio.sleep(5)
            continue
            
        await asyncio.sleep(intervallo)
    
async def shutdown(signal, loop, websocket_server):
    """Pulizia delle risorse e shutdown ordinato"""
    print(f"Ricevuto segnale {signal.name}, shutdown in corso...")
    
    # Chiudi il server WebSocket
    if websocket_server:
        websocket_server.close()
        await websocket_server.wait_closed()
    
    # Cancella tutti i task in esecuzione
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    # Aspetta che i task vengano cancellati
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main():
    """Avvio server e monitoraggio"""
    loop = asyncio.get_running_loop()
    
    # Configura i gestori di segnale
    signals = (signal.SIGTERM, signal.SIGINT)
    websocket_server = None
    
    try:
        for s in signals:
            loop.add_signal_handler(
                s,
                lambda s=s: asyncio.create_task(shutdown(s, loop, websocket_server)))
    except NotImplementedError:
        # Windows non supporta add_signal_handler
        for s in signals:
            signal.signal(s, lambda s, _: asyncio.create_task(shutdown(s, loop, websocket_server)))
    
    print("Avvio server WebSocket su ws://0.0.0.0:8765")

    try:
        async with websockets.serve(gestisci_connessione, "0.0.0.0", 8765) as server:
            websocket_server = server
            await monitora_livello_ambientale()
            await asyncio.Future()  # Mantiene il server attivo
    except asyncio.CancelledError:
        print("Operazioni annullate durante lo shutdown")
    finally:
        print("Programma terminato correttamente")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nRicevuto Ctrl+C, shutdown completato")
        sys.exit(0)