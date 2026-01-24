
import sounddevice as sd
import soundfile as sf
import numpy as np
from PIL import Image, ImageDraw
import threading
import tempfile
import os
from pathlib import Path
from typing import Optional, List, Dict

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []
        self.fs = 44100
        self.stream = None
        self.output_file = None

    def get_devices(self) -> List[Dict]:
        """Devuelve una lista de dispositivos de entrada disponibles."""
        devices = []
        try:
            full_list = sd.query_devices()
            for i, dev in enumerate(full_list):
                if dev['max_input_channels'] > 0:
                    devices.append({"id": i, "name": dev['name']})
        except Exception as e:
            print(f"Error querying devices: {e}")
        return devices

    def start_recording(self, device_id: Optional[int] = None):
        """Inicia la grabación en un hilo separado."""
        if self.recording:
            return

        self.recording = True
        self.frames = []
        
        # Crear archivo temporal
        self.output_file = tempfile.mktemp(prefix="voicevault_rec_", suffix=".wav")

        def callback(indata, frames, time, status):
            if status:
                print(status)
            if self.recording:
                self.frames.append(indata.copy())

        def record_thread():
            try:
                with sd.InputStream(samplerate=self.fs, device=device_id, channels=1, callback=callback):
                    while self.recording:
                        sd.sleep(100)
            except Exception as e:
                print(f"Error recording: {e}")
                self.recording = False

        self.thread = threading.Thread(target=record_thread)
        self.thread.start()

    def stop_recording(self) -> Optional[str]:
        """Detiene la grabación y devuelve la ruta del archivo grabado."""
        if not self.recording:
            return None

        self.recording = False
        self.thread.join()
        
        try:
            if not self.frames:
                return None
                
            recording_data = np.concatenate(self.frames)
            sf.write(self.output_file, recording_data, self.fs)
            return self.output_file
        except Exception as e:
            print(f"Error saving recording: {e}")
            return None


def generate_waveform(audio_path: str, output_path: str, width: int = 600, height: int = 150, color=(197, 160, 89)):
    """Genera una imagen de onda de sonido (waveform) a partir de un archivo de audio."""
    try:
        # Leer audio
        data, samplerate = sf.read(audio_path)
        
        # Si es estéreo, convertir a mono promediando
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Normalizar
        # Tomar muestras representativas para no procesar todo (downsampling)
        # Queremos 'width' barras
        num_bars = width // 3 # 3px por barra (2 barra + 1 espacio)
        if num_bars < 10: num_bars = 10
        
        step = len(data) // num_bars
        if step < 1: step = 1
        
        # Obtener valores absolutos para la amplitud
        amplitudes = []
        for i in range(0, len(data), step):
            chunk = data[i:i+step]
            if len(chunk) > 0:
                # Usar el valor máximo (pico) o la media del chunk
                val = np.abs(chunk).mean() 
                amplitudes.append(val)
        
        # Normalizar alturas al tamaño de imagen
        if not amplitudes: return False
        
        max_amp = max(amplitudes)
        if max_amp == 0: max_amp = 1
        
        amplitudes = [int((a / max_amp) * (height * 0.9)) for a in amplitudes]

        # Crear imagen
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Dibujar barras (centradas verticalmente)
        bar_width = 2
        spacing = 1
        x = 0
        
        center_y = height // 2
        
        for amp in amplitudes:
            if x >= width: break
            
            # Dibujar línea vertical centrada
            y1 = center_y - (amp // 2)
            y2 = center_y + (amp // 2)
            
            # Mínimo 2px de altura
            if y2 - y1 < 2:
                y1 = center_y - 1
                y2 = center_y + 1
            
            draw.rectangle([x, y1, x + bar_width, y2], fill=color)
            x += bar_width + spacing
            
        img.save(output_path, "PNG")
        return True

    except Exception as e:
        print(f"Error generando waveform: {e}")
        return False
