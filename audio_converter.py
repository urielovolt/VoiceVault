"""
VoiceVault - Audio Converter Module
Validación de contenido real y conversión automática de formatos de audio no compatibles.

Seguridad: Valida contenido de archivos, no solo extensiones.
Type Safety: Type hints completos con pathlib.Path.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import os

# Audio libraries
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
    FFMPEG_AVAILABLE = which("ffmpeg") is not None or which("avconv") is not None
except ImportError:
    PYDUB_AVAILABLE = False
    FFMPEG_AVAILABLE = False

# Configure logging
logger = logging.getLogger("VoiceVault.AudioConverter")

# Formatos oficialmente soportados por VoiceVault (pygame mixer)
SUPPORTED_FORMATS = {".mp3", ".wav", ".ogg", ".flac"}

# Formatos convertibles conocidos (requiere ffmpeg)
CONVERTIBLE_FORMATS = {
    ".m4a", ".aac", ".wma", ".opus", ".aiff", ".aif", 
    ".ape", ".mpc", ".tta", ".webm", ".3gp"
}


class AudioFormat:
    """Información de formato de audio detectado."""
    def __init__(
        self, 
        extension: str,
        is_valid: bool,
        codec: Optional[str] = None,
        bitrate: Optional[int] = None,
        samplerate: Optional[int] = None,
        channels: Optional[int] = None,
        duration: Optional[float] = None
    ):
        self.extension = extension
        self.is_valid = is_valid
        self.codec = codec
        self.bitrate = bitrate
        self.samplerate = samplerate
        self.channels = channels
        self.duration = duration
    
    def __repr__(self) -> str:
        return (f"AudioFormat(ext={self.extension}, valid={self.is_valid}, "
                f"codec={self.codec}, sr={self.samplerate}Hz)")


def detect_audio_format(file_path: Path) -> Optional[AudioFormat]:
    """
    Detecta el formato de audio real del archivo, no solo la extensión.
    
    Args:
        file_path: Ruta al archivo de audio
        
    Returns:
        AudioFormat con información del archivo, o None si no es audio válido
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    
    ext = file_path.suffix.lower()
    
    # Intento 1: Usar mutagen para leer metadatos (más completo)
    if MUTAGEN_AVAILABLE:
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                logger.warning(f"Mutagen could not identify format: {file_path.name}")
                # Continuar con otros métodos
            else:
                # Extraer información
                info = audio_file.info if hasattr(audio_file, 'info') else None
                
                return AudioFormat(
                    extension=ext,
                    is_valid=True,
                    codec=type(audio_file).__name__,
                    bitrate=getattr(info, 'bitrate', None),
                    samplerate=getattr(info, 'sample_rate', None),
                    channels=getattr(info, 'channels', None),
                    duration=getattr(info, 'length', None)
                )
        except Exception as e:
            logger.debug(f"Mutagen failed for {file_path.name}: {e}")
    
    # Intento 2: Usar soundfile para WAV/FLAC
    if SOUNDFILE_AVAILABLE and ext in {".wav", ".flac"}:
        try:
            info = sf.info(file_path)
            return AudioFormat(
                extension=ext,
                is_valid=True,
                codec="PCM" if ext == ".wav" else "FLAC",
                samplerate=info.samplerate,
                channels=info.channels,
                duration=info.duration
            )
        except Exception as e:
            logger.debug(f"Soundfile failed for {file_path.name}: {e}")
    
    # Intento 3: Usar pydub (requiere ffmpeg, pero más robusto)
    if PYDUB_AVAILABLE and FFMPEG_AVAILABLE:
        try:
            audio = AudioSegment.from_file(file_path)
            return AudioFormat(
                extension=ext,
                is_valid=True,
                codec="unknown",
                samplerate=audio.frame_rate,
                channels=audio.channels,
                duration=len(audio) / 1000.0  # ms to seconds
            )
        except Exception as e:
            logger.debug(f"Pydub failed for {file_path.name}: {e}")
    
    # No se pudo identificar como audio válido
    logger.warning(f"Could not validate audio format for: {file_path.name}")
    return AudioFormat(extension=ext, is_valid=False)


def is_format_supported(file_path: Path) -> bool:
    """
    Verifica si el archivo es un formato de audio válido y soportado.
    
    Args:
        file_path: Ruta al archivo de audio
        
    Returns:
        True si es formato soportado y válido, False en caso contrario
    """
    format_info = detect_audio_format(file_path)
    
    if format_info is None or not format_info.is_valid:
        return False
    
    # Verificar si la extensión está en formatos soportados
    return format_info.extension in SUPPORTED_FORMATS


def convert_to_supported_format(
    source: Path, 
    target_format: str = "wav",
    target_bitrate: str = "320k"
) -> Optional[Path]:
    """
    Convierte un archivo de audio a un formato soportado con máxima calidad.
    
    Args:
        source: Ruta al archivo de audio original
        target_format: Formato destino ("wav", "mp3", "ogg", "flac")
        target_bitrate: Bitrate para formatos con pérdida (solo mp3/ogg)
        
    Returns:
        Path al archivo convertido, o None si falla
    """
    if not source.exists():
        logger.error(f"Source file not found: {source}")
        return None
    
    # Validar que target_format sea soportado
    if f".{target_format}" not in SUPPORTED_FORMATS:
        logger.error(f"Target format not supported: {target_format}")
        return None
    
    # Verificar disponibilidad de herramientas
    if not PYDUB_AVAILABLE:
        logger.error("pydub not available - cannot convert audio")
        return None
    
    if not FFMPEG_AVAILABLE:
        logger.error("ffmpeg/avconv not found - cannot convert audio")
        return None
    
    try:
        # Cargar audio original
        logger.info(f"Loading audio file: {source.name}")
        audio = AudioSegment.from_file(source)
        
        # Crear archivo temporal para el resultado
        temp_dir = tempfile.gettempdir()
        output_filename = f"voicevault_converted_{source.stem}.{target_format}"
        output_path = Path(temp_dir) / output_filename
        
        # Configurar parámetros de exportación según formato
        export_params: Dict[str, Any] = {}
        
        if target_format == "mp3":
            export_params = {
                "format": "mp3",
                "bitrate": target_bitrate,
                "parameters": ["-q:a", "0"]  # Máxima calidad VBR
            }
        elif target_format == "wav":
            export_params = {
                "format": "wav",
                "parameters": ["-acodec", "pcm_s16le"]  # PCM 16-bit
            }
        elif target_format == "ogg":
            export_params = {
                "format": "ogg",
                "codec": "libvorbis",
                "parameters": ["-q:a", "10"]  # Máxima calidad Vorbis
            }
        elif target_format == "flac":
            export_params = {
                "format": "flac",
                "parameters": ["-compression_level", "5"]
            }
        
        # Exportar con configuración optimizada
        logger.info(f"Converting {source.name} to {target_format}...")
        audio.export(str(output_path), **export_params)
        
        logger.info(f"Conversion successful: {output_path.name}")
        return output_path
        
    except Exception as e:
        logger.error(f"Conversion failed for {source.name}: {e}")
        return None


def get_conversion_capabilities() -> Dict[str, bool]:
    """
    Retorna información sobre capacidades de conversión disponibles.
    
    Returns:
        Dict con flags de disponibilidad de herramientas
    """
    return {
        "soundfile_available": SOUNDFILE_AVAILABLE,
        "mutagen_available": MUTAGEN_AVAILABLE,
        "pydub_available": PYDUB_AVAILABLE,
        "ffmpeg_available": FFMPEG_AVAILABLE,
        "can_convert": PYDUB_AVAILABLE and FFMPEG_AVAILABLE
    }


def install_ffmpeg_instructions() -> str:
    """
    Retorna instrucciones para instalar ffmpeg según el sistema operativo.
    
    Returns:
        String con instrucciones de instalación
    """
    import platform
    os_type = platform.system()
    
    if os_type == "Windows":
        return """
FFmpeg no está instalado. Para habilitar conversión de audio:

1. Descargar ffmpeg desde: https://www.gyan.dev/ffmpeg/builds/
2. Extraer el ZIP y copiar los archivos .exe de la carpeta 'bin' a:
   C:\\ffmpeg\\bin\\
3. Agregar C:\\ffmpeg\\bin\\ a las variables de entorno PATH
4. Reiniciar VoiceVault

Alternativamente, usar chocolatey:
  choco install ffmpeg
"""
    elif os_type == "Darwin":  # macOS
        return """
FFmpeg no está instalado. Para habilitar conversión de audio:

Usando Homebrew:
  brew install ffmpeg

Reiniciar VoiceVault después de la instalación.
"""
    else:  # Linux
        return """
FFmpeg no está instalado. Para habilitar conversión de audio:

Ubuntu/Debian:
  sudo apt-get install ffmpeg

Fedora:
  sudo dnf install ffmpeg

Arch Linux:
  sudo pacman -S ffmpeg

Reiniciar VoiceVault después de la instalación.
"""
