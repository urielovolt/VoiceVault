"""
VoiceVault - Álbum de Recuerdos Sonoros
Diseño: True Black OLED + Gold Accents
Tecnología: Python 3.x + CustomTkinter + Pygame
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import json
import shutil
import uuid
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from PIL import Image, ImageTk, ImageDraw, ImageChops
import pygame

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

APP_DIR = Path(__file__).parent
ASSETS_DIR = APP_DIR / "assets"
PHOTOS_DIR = ASSETS_DIR / "photos"
AUDIOS_DIR = ASSETS_DIR / "audios"
DATA_DIR = APP_DIR / "data"
DATA_FILE = DATA_DIR / "voicevault.json"
DEFAULT_AVATAR = ASSETS_DIR / "default_avatar.png"
APP_ICON = ASSETS_DIR / "app_icon.png"
LOGO_FILE = ASSETS_DIR / "LogoVoiceVault.png"
TEXTURE_FILE = ASSETS_DIR / "texture.png"
EMPTY_STATE_FILE = ASSETS_DIR / "BaulVacio.png"
CATEGORIES_DIR = ASSETS_DIR / "Categorias"
CAPTURE_ICON = ASSETS_DIR / "CapturaRecuerdos.png"
PLUS_ICON = ASSETS_DIR / "plus_icon.png"
WAVEFORMS_DIR = ASSETS_DIR / "waveforms"

# Import Audio Utils
try:
    from audio_utils import AudioRecorder, generate_waveform
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Audio libraries not installed (sounddevice, soundfile, numpy)")

# Configurar tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class Colors:
    # === Fondos - Degradado de profundidad ===
    BLACK = "#050508"           # Negro profundo con tinte azulado
    DARK_BG = "#0C0C10"         # Fondo oscuro principal
    CARD_BG = "#141418"         # Fondo de tarjetas
    SURFACE = "#1C1C22"         # Superficies elevadas
    ELEVATED = "#242430"        # Elementos flotantes

    # === Bordes y líneas ===
    BORDER = "#2A2A35"          # Borde sutil
    BORDER_LIGHT = "#3A3A48"    # Borde más visible

    # === Dorado - Paleta principal ===
    GOLD_DARK = "#8B7355"       # Dorado oscuro para acentos
    GOLD = "#C9A962"            # Dorado principal (más cálido)
    GOLD_LIGHT = "#E8D5A3"      # Dorado claro para highlights
    GOLD_GLOW = "#D4B872"       # Resplandor dorado

    # === Texto - Jerarquía clara ===
    TEXT_PRIMARY = "#F5F5F7"    # Texto principal (blanco cálido)
    TEXT_SECONDARY = "#9898A0"  # Texto secundario
    TEXT_MUTED = "#5C5C66"      # Texto deshabilitado
    TEXT_ACCENT = "#C9A962"     # Texto de acento (dorado)

    # === Estados ===
    SUCCESS = "#5DB075"         # Verde éxito (más sofisticado)
    ERROR = "#E85D75"           # Rojo error (coral)
    FAVORITE = "#E8587A"        # Rosa favoritos
    WARNING = "#E8A857"         # Naranja advertencia

    # === Efectos ===
    SHADOW = "#020204"          # Sombra profunda
    PLAYING_GLOW = "#E8C55A"    # Resplandor reproduciendo
    OVERLAY = "#0A0A0F80"       # Overlay semi-transparente

    # === Gradientes simulados (para efectos) ===
    GRADIENT_START = "#141418"
    GRADIENT_END = "#1C1C22"

CATEGORIES = ["Familiares", "Amigos", "Especiales"]
ALLOWED_AUDIO = (".mp3", ".wav", ".m4a", ".ogg", ".flac")
ALLOWED_IMAGE = (".jpg", ".jpeg", ".png", ".webp", ".gif")

# Opciones de ordenamiento
SORT_OPTIONS = {
    "Más recientes": lambda m: m.get("created_at", ""),
    "Más antiguos": lambda m: m.get("created_at", ""),
    "Nombre A-Z": lambda m: m.get("name", "").lower(),
    "Nombre Z-A": lambda m: m.get("name", "").lower()
}

# =============================================================================
# DATA MANAGER
# =============================================================================

class DataManager:
    def __init__(self):
        for d in [ASSETS_DIR, PHOTOS_DIR, AUDIOS_DIR, DATA_DIR, WAVEFORMS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> Dict:
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"memories": []}
        return {"memories": []}

    def _save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_all(self) -> List[Dict]:
        return self._data.get("memories", [])

    def get_by_category(self, category: str) -> List[Dict]:
        if category == "Todos":
            return self.get_all()
        if category == "Favoritos":
            return [m for m in self.get_all() if m.get("is_favorite", False)]
        return [m for m in self.get_all() if m.get("category") == category]

    def search(self, query: str) -> List[Dict]:
        """Búsqueda avanzada: busca en nombre, nota y fecha."""
        q = query.lower().strip()
        if not q:
            return self.get_all()
        results = []
        for m in self.get_all():
            if (q in m.get("name", "").lower() or
                q in m.get("note", "").lower() or
                q in m.get("date", "").lower() or
                q in m.get("category", "").lower()):
                results.append(m)
        return results

    def add(self, memory: Dict):
        memory["id"] = str(uuid.uuid4())[:8]
        memory["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memory["is_favorite"] = memory.get("is_favorite", False)
        self._data["memories"].append(memory)
        self._save()

    def update(self, memory_id: str, updates: Dict) -> bool:
        """Actualiza un recuerdo existente."""
        for m in self._data.get("memories", []):
            if m.get("id") == memory_id:
                for key, value in updates.items():
                    if key != "id":  # No permitir cambiar el ID
                        m[key] = value
                self._save()
                return True
        return False

    def get_by_id(self, memory_id: str) -> Optional[Dict]:
        """Obtiene un recuerdo por su ID."""
        for m in self._data.get("memories", []):
            if m.get("id") == memory_id:
                return m
        return None

    def delete(self, memory_id: str):
        for i, m in enumerate(self._data.get("memories", [])):
            if m.get("id") == memory_id:
                if m.get("photo"):
                    photo_path = PHOTOS_DIR / m["photo"]
                    if photo_path.exists():
                        photo_path.unlink()
                if m.get("audio"):
                    audio_path = AUDIOS_DIR / m["audio"]
                    if audio_path.exists():
                        audio_path.unlink()
                self._data["memories"].pop(i)
                self._save()
                return True
        return False

    def toggle_favorite(self, memory_id: str) -> bool:
        """Cambia el estado de favorito de un recuerdo."""
        for m in self._data.get("memories", []):
            if m.get("id") == memory_id:
                m["is_favorite"] = not m.get("is_favorite", False)
                self._save()
                return m["is_favorite"]
        return False

    def copy_to_assets(self, source_path: str, file_type: str) -> Optional[str]:
        source = Path(source_path)
        if not source.exists():
            return None

        ext = source.suffix.lower()
        allowed = ALLOWED_IMAGE if file_type == "photo" else ALLOWED_AUDIO
        if ext not in allowed:
            return None

        new_name = f"{uuid.uuid4()}{ext}"
        dest_dir = PHOTOS_DIR if file_type == "photo" else AUDIOS_DIR
        dest_path = dest_dir / new_name

        try:
            shutil.copy2(source, dest_path)
            return new_name
        except Exception as e:
            print(f"Error copiando archivo: {e}")
            return None

    def export_backup(self, export_path: str) -> bool:
        """Exporta todos los recuerdos a un archivo ZIP."""
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Agregar archivo de datos
                zipf.write(DATA_FILE, "data/voicevault.json")

                # Agregar fotos
                for photo in PHOTOS_DIR.glob("*"):
                    if photo.is_file():
                        zipf.write(photo, f"assets/photos/{photo.name}")

                # Agregar audios
                for audio in AUDIOS_DIR.glob("*"):
                    if audio.is_file():
                        zipf.write(audio, f"assets/audios/{audio.name}")
            return True
        except Exception as e:
            print(f"Error exportando: {e}")
            return False

    def import_backup(self, import_path: str) -> tuple:
        """Importa recuerdos desde un archivo ZIP, combinando con existentes."""
        try:
            imported_count = 0
            skipped_count = 0

            # IDs existentes para detectar duplicados
            existing_ids = {m.get("id") for m in self._data.get("memories", [])}
            # También detectar por nombre + audio para duplicados sin mismo ID
            existing_signatures = {
                (m.get("name", "").lower(), m.get("audio", ""))
                for m in self._data.get("memories", [])
            }

            with zipfile.ZipFile(import_path, 'r') as zipf:
                # Primero leer el JSON del backup para analizar
                backup_data = {"memories": []}
                for member in zipf.namelist():
                    if member.startswith("data/") and member.endswith(".json"):
                        with zipf.open(member) as f:
                            backup_data = json.load(f)
                        break

                # Procesar cada recuerdo del backup
                for memory in backup_data.get("memories", []):
                    memory_id = memory.get("id")
                    signature = (memory.get("name", "").lower(), memory.get("audio", ""))

                    # Verificar si es duplicado
                    if memory_id in existing_ids or signature in existing_signatures:
                        skipped_count += 1
                        continue

                    # Extraer archivos asociados
                    photo = memory.get("photo")
                    audio = memory.get("audio")

                    if photo:
                        photo_member = f"assets/photos/{photo}"
                        if photo_member in zipf.namelist():
                            with zipf.open(photo_member) as src:
                                with open(PHOTOS_DIR / photo, 'wb') as dst:
                                    dst.write(src.read())

                    if audio:
                        audio_member = f"assets/audios/{audio}"
                        if audio_member in zipf.namelist():
                            with zipf.open(audio_member) as src:
                                with open(AUDIOS_DIR / audio, 'wb') as dst:
                                    dst.write(src.read())

                    # Agregar recuerdo a la lista
                    self._data["memories"].append(memory)
                    existing_ids.add(memory_id)
                    existing_signatures.add(signature)
                    imported_count += 1

                # Guardar cambios
                self._save()

            return True, imported_count, skipped_count
        except Exception as e:
            print(f"Error importando: {e}")
            return False, 0, 0

# =============================================================================
# UTILIDADES DE IMAGEN
# =============================================================================

class ToolTip:
    """Tooltip simple para widgets."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#333333",
            foreground="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=4,
            font=("Roboto", 10)
        )
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def make_circular_image(img: Image.Image, size: tuple) -> Image.Image:
    """Convierte una imagen en circular, preservando transparencia."""
    # Convertir a RGBA si no lo es
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    img = img.resize(size, Image.Resampling.LANCZOS)

    # Crear máscara circular
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0]-1, size[1]-1), fill=255)

    # Crear imagen de salida transparente
    output = Image.new('RGBA', size, (0, 0, 0, 0))
    output.paste(img, (0, 0), img)  # Usar img como máscara para preservar alfa

    # Combinar con máscara circular
    output.putalpha(ImageChops.multiply(output.split()[3], mask))

    return output

# =============================================================================
# APLICACIÓN PRINCIPAL
# =============================================================================

class VoiceVault(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VoiceVault")
        if APP_ICON.exists():
            try:
                icon_image = Image.open(APP_ICON)
                photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(False, photo)
            except Exception as e:
                print(f"Error cargando icono: {e}")
        self.geometry("1000x700")

        # Background: Color sólido negro
        self.configure(fg_color=Colors.BLACK)

        self.dm = DataManager()
        self.current_filter = "Todos"
        self.search_query = ""
        self.current_memory = None
        self.current_dialog = None
        self.auto_play_next = False
        self.current_sort = "Más recientes"
        self.playing_memory_id = None  # Para indicador de reproducción
        self.card_refs = {}  # Referencias a tarjetas para actualizar indicador

        # Playlist mode
        self.playlist_mode = False
        self.playlist_memories = []
        self.playlist_index = 0

        # Inicializar pygame mixer para audio
        pygame.mixer.init()
        self.playing = False

        # Audio Recorder
        self.recorder = AudioRecorder() if AUDIO_AVAILABLE else None

        self.create_widgets()
        self.setup_keyboard_shortcuts()
        self.refresh_grid()

    def setup_keyboard_shortcuts(self):
        """Configura atajos de teclado."""
        self.bind("<space>", self.toggle_play_shortcut)
        self.bind("<Escape>", self.stop_playback_shortcut)
        self.bind("<Control-e>", lambda e: self.export_backup())
        self.bind("<Control-i>", lambda e: self.import_backup())
        self.bind("<Control-n>", lambda e: self.show_add_dialog())
        self.bind("<Control-f>", lambda e: self.search_entry.focus_set())


    def toggle_play_shortcut(self, event):
        """Atajo de teclado para play/pausa."""
        if self.current_dialog and self.current_dialog.winfo_exists():
            # Si hay un diálogo abierto, enviar evento
            pass
        return "break"

    def stop_playback_shortcut(self, event):
        """Atajo para detener reproducción."""
        if self.playing:
            pygame.mixer.music.stop()
            self.playing = False
            self.playing_memory_id = None
            self.update_playing_indicator()

    def create_widgets(self):
        # =================================================================
        # HEADER - Estilo editorial refinado
        # =================================================================
        header = ctk.CTkFrame(self, fg_color=Colors.DARK_BG, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)

        # Línea decorativa superior dorada (más sutil)
        accent_line = ctk.CTkFrame(header, fg_color=Colors.GOLD, height=1, corner_radius=0)
        accent_line.pack(fill="x")

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=30, pady=16)

        # Logo y título
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(side="left")

        # Logo Image
        if LOGO_FILE.exists():
            try:
                logo_img = Image.open(LOGO_FILE)
                aspect_ratio = logo_img.width / logo_img.height
                new_height = 45
                new_width = int(new_height * aspect_ratio)

                logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(new_width, new_height))

                logo_label = ctk.CTkLabel(title_frame, image=logo_ctk, text="")
                logo_label.image = logo_ctk
                logo_label.pack(side="top", anchor="w")
            except Exception as e:
                print(f"Error loading logo: {e}")
                ctk.CTkLabel(title_frame, text="VoiceVault", font=("Georgia", 22, "bold"), text_color=Colors.TEXT_PRIMARY).pack(side="top", anchor="w")
        else:
            ctk.CTkLabel(
                title_frame,
                text="VoiceVault",
                font=("Georgia", 22, "bold"),
                text_color=Colors.TEXT_PRIMARY
            ).pack(side="top", anchor="w")

        # Contenedor para subtítulo y contador
        meta_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        meta_frame.pack(side="top", anchor="w", pady=(4, 0))

        self.subtitle_label = ctk.CTkLabel(
            meta_frame,
            text="by @urielovolt",
            font=("Segoe UI", 10),
            text_color=Colors.GOLD
        )
        self.subtitle_label.pack(side="left")

        ctk.CTkLabel(
            meta_frame,
            text=" • ",
            font=("Segoe UI", 10),
            text_color=Colors.TEXT_MUTED
        ).pack(side="left")

        self.counter_label = ctk.CTkLabel(
            meta_frame,
            text="0 recuerdos",
            font=("Segoe UI", 10),
            text_color=Colors.TEXT_SECONDARY
        )
        self.counter_label.pack(side="left")

        # Buscador y controles
        right_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        right_frame.pack(side="right")

        # Botones de Import/Export
        export_btn = ctk.CTkButton(
            right_frame,
            text="📤",
            width=36,
            height=36,
            fg_color=Colors.CARD_BG,
            hover_color=Colors.SURFACE,
            font=("Segoe UI Symbol", 14),
            corner_radius=8,
            command=self.export_backup
        )
        export_btn.pack(side="right", padx=(4, 0))
        ToolTip(export_btn, "Exportar backup")

        import_btn = ctk.CTkButton(
            right_frame,
            text="📥",
            width=36,
            height=36,
            fg_color=Colors.CARD_BG,
            hover_color=Colors.SURFACE,
            font=("Segoe UI Symbol", 14),
            corner_radius=8,
            command=self.import_backup
        )
        import_btn.pack(side="right", padx=(4, 0))
        ToolTip(import_btn, "Importar backup")

        # Buscador compacto
        self.search_entry = ctk.CTkEntry(
            right_frame,
            placeholder_text="🔍 Buscar...",
            width=230,
            height=36,
            fg_color=Colors.CARD_BG,
            border_color=Colors.BORDER,
            border_width=1,
            corner_radius=8,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            font=("Segoe UI", 12)
        )
        self.search_entry.pack(side="right", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Botón Captura Recuerdos (Header)
        if AUDIO_AVAILABLE and CAPTURE_ICON.exists():
            try:
                cap_img = Image.open(CAPTURE_ICON)
                cap_icon = ctk.CTkImage(light_image=cap_img, dark_image=cap_img, size=(22, 22))

                self.rec_btn_header = ctk.CTkButton(
                    right_frame,
                    text="",
                    image=cap_icon,
                    width=36,
                    height=36,
                    fg_color=Colors.GOLD,
                    hover_color=Colors.GOLD_LIGHT,
                    corner_radius=18,
                    command=self.show_recording_dialog
                )
                self.rec_btn_header.pack(side="right", padx=(0, 10))
                ToolTip(self.rec_btn_header, "Capturar recuerdo")
            except Exception as e:
                print(f"Error loading capture icon: {e}")

        # =================================================================
        # FILTERS & SORT - Compacto
        # =================================================================
        filters_section = ctk.CTkFrame(self, fg_color=Colors.BLACK, corner_radius=0)
        filters_section.pack(fill="x", padx=30, pady=(0, 8))

        # Filtros de categoría
        self.filter_buttons = {}
        for category in ["Todos", "Favoritos"] + CATEGORIES:
            icon = None
            try:
                if category != "Todos":
                   filename = category
                   if category == "Familiares":
                       filename = "Familia"

                   icon_path = CATEGORIES_DIR / f"{filename}.png"
                   if icon_path.exists():
                       pil_img = Image.open(icon_path)
                       icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(16, 16))
            except Exception:
                pass

            is_active = category == "Todos"
            btn = ctk.CTkButton(
                filters_section,
                text=category,
                image=icon,
                compound="left",
                width=100 if icon else 80,
                height=32,
                fg_color=Colors.GOLD if is_active else Colors.CARD_BG,
                hover_color=Colors.GOLD_GLOW if is_active else Colors.SURFACE,
                border_width=1,
                border_color=Colors.GOLD if is_active else Colors.BORDER,
                corner_radius=8,
                text_color=Colors.BLACK if is_active else Colors.TEXT_SECONDARY,
                font=("Segoe UI", 11),
                command=lambda c=category: self.on_filter_click(c)
            )
            btn.pack(side="left", padx=(0, 6))
            self.filter_buttons[category] = btn

        # Ordenamiento y Playlist (a la derecha)
        self.sort_menu = ctk.CTkOptionMenu(
            filters_section,
            values=list(SORT_OPTIONS.keys()),
            variable=ctk.StringVar(value=self.current_sort),
            fg_color=Colors.CARD_BG,
            button_color=Colors.SURFACE,
            button_hover_color=Colors.GOLD,
            dropdown_fg_color=Colors.CARD_BG,
            dropdown_hover_color=Colors.SURFACE,
            dropdown_text_color=Colors.TEXT_PRIMARY,
            width=135,
            height=32,
            corner_radius=8,
            font=("Segoe UI", 11),
            command=self.on_sort_change
        )
        self.sort_menu.pack(side="right")

        # Botón Playlist
        self.playlist_btn = ctk.CTkButton(
            filters_section,
            text="▶ Playlist",
            width=90,
            height=32,
            fg_color=Colors.CARD_BG,
            hover_color=Colors.GOLD,
            text_color=Colors.TEXT_SECONDARY,
            border_width=1,
            border_color=Colors.BORDER,
            corner_radius=8,
            font=("Segoe UI", 11),
            command=self.toggle_playlist_mode
        )
        self.playlist_btn.pack(side="right", padx=(0, 8))

        # =================================================================
        # GRID SCROLLABLE
        # =================================================================
        self.grid_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Colors.BLACK,
            corner_radius=0,
            scrollbar_button_color=Colors.SURFACE,
            scrollbar_button_hover_color=Colors.GOLD
        )
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        # =================================================================
        # FAB (Add Button)
        # =================================================================
        fab_image = None
        if PLUS_ICON.exists():
            try:
                pi = Image.open(PLUS_ICON)
                fab_image = ctk.CTkImage(light_image=pi, dark_image=pi, size=(60, 60))
            except: pass

        self.fab = ctk.CTkButton(
            self,
            text="",
            image=fab_image if fab_image else None,
            width=60,
            height=60,
            fg_color="transparent",
            hover_color=Colors.SURFACE,
            border_width=0,
            corner_radius=30,
            command=self.show_add_dialog
        )
        if not fab_image:
            self.fab.configure(
                text="+",
                fg_color=Colors.GOLD,
                hover_color=Colors.GOLD_LIGHT,
                text_color=Colors.BLACK,
                font=("Segoe UI", 28, "bold"),
                corner_radius=30
            )

        self.fab.place(relx=0.96, rely=0.94, anchor="se")

    def update_counter(self):
        """Actualiza el contador de recuerdos."""
        total = len(self.dm.get_all())
        text = f"{total} recuerdo{'s' if total != 1 else ''}"
        self.counter_label.configure(text=text)


    def on_sort_change(self, choice):
        """Cambia el ordenamiento."""
        self.current_sort = choice
        self.refresh_grid()

    def toggle_playlist_mode(self):
        """Activa/desactiva modo playlist."""
        self.playlist_mode = not self.playlist_mode
        if self.playlist_mode:
            self.playlist_btn.configure(
                fg_color=Colors.GOLD,
                text_color=Colors.BLACK,
                text="⏹ Parar"
            )
            self.start_playlist()
        else:
            self.playlist_btn.configure(
                fg_color=Colors.CARD_BG,
                text_color=Colors.TEXT_SECONDARY,
                text="▶ Playlist"
            )
            self.stop_playlist()

    def start_playlist(self):
        """Inicia reproducción en modo playlist."""
        if self.search_query:
            memories = self.dm.search(self.search_query)
        else:
            memories = self.dm.get_by_category(self.current_filter)

        self.playlist_memories = [m for m in memories if m.get("audio")]
        self.playlist_index = 0

        if self.playlist_memories:
            self.play_playlist_item()
        else:
            messagebox.showinfo("Playlist", "No hay recuerdos con audio para reproducir.")
            self.toggle_playlist_mode()

    def play_playlist_item(self):
        """Reproduce el item actual de la playlist."""
        if not self.playlist_mode or self.playlist_index >= len(self.playlist_memories):
            self.playlist_mode = False
            self.playlist_btn.configure(
                fg_color=Colors.CARD_BG,
                text_color=Colors.TEXT_SECONDARY,
                text="▶ Playlist"
            )
            self.playing_memory_id = None
            self.update_playing_indicator()
            return

        memory = self.playlist_memories[self.playlist_index]
        audio_path = self.get_audio_path(memory)

        if audio_path:
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                self.playing = True
                self.playing_memory_id = memory.get("id")
                self.update_playing_indicator()

                # Verificar cuando termine para pasar al siguiente
                self.check_playlist_progress()
            except Exception as e:
                print(f"Error en playlist: {e}")
                self.playlist_index += 1
                self.play_playlist_item()

    def check_playlist_progress(self):
        """Verifica si la canción actual terminó."""
        if not self.playlist_mode:
            return

        if not pygame.mixer.music.get_busy():
            self.playlist_index += 1
            self.play_playlist_item()
        else:
            self.after(500, self.check_playlist_progress)

    def stop_playlist(self):
        """Detiene la playlist."""
        pygame.mixer.music.stop()
        self.playing = False
        self.playing_memory_id = None
        self.update_playing_indicator()

    def update_playing_indicator(self):
        """Actualiza el indicador visual de reproducción en las tarjetas."""
        for memory_id, card_frame in self.card_refs.items():
            try:
                if card_frame.winfo_exists():
                    if memory_id == self.playing_memory_id:
                        card_frame.configure(border_color=Colors.PLAYING_GLOW, border_width=2)
                    else:
                        card_frame.configure(border_color=Colors.BORDER, border_width=1)
            except:
                pass

    def export_backup(self):
        """Exporta backup a archivo ZIP."""
        path = filedialog.asksaveasfilename(
            title="Exportar Backup",
            defaultextension=".zip",
            filetypes=[("ZIP Archive", "*.zip")],
            initialfile=f"voicevault_backup_{datetime.now().strftime('%Y%m%d')}.zip"
        )
        if path:
            if self.dm.export_backup(path):
                messagebox.showinfo("Éxito", f"Backup exportado correctamente:\n{path}")
            else:
                messagebox.showerror("Error", "No se pudo exportar el backup.")

    def import_backup(self):
        """Importa backup desde archivo ZIP."""
        path = filedialog.askopenfilename(
            title="Importar Backup",
            filetypes=[("ZIP Archive", "*.zip")]
        )
        if path:
            if messagebox.askyesno("Confirmar", "¿Importar backup? Los recuerdos se combinarán con los existentes."):
                result = self.dm.import_backup(path)
                if result[0]:
                    imported, skipped = result[1], result[2]
                    msg = f"Backup importado correctamente.\n\n"
                    msg += f"• Recuerdos agregados: {imported}\n"
                    msg += f"• Recuerdos omitidos (duplicados): {skipped}"
                    messagebox.showinfo("Éxito", msg)
                    self.refresh_grid()
                else:
                    messagebox.showerror("Error", "No se pudo importar el backup.")

    def refresh_grid(self):
        # Limpiar grid y referencias
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.card_refs = {}

        # Actualizar contador
        self.update_counter()

        # Obtener memorias filtradas
        if self.search_query:
            memories = self.dm.search(self.search_query)
        else:
            memories = self.dm.get_by_category(self.current_filter)

        # Aplicar ordenamiento
        sort_key = SORT_OPTIONS.get(self.current_sort, lambda m: m.get("created_at", ""))
        reverse = self.current_sort in ["Más recientes", "Nombre Z-A"]
        memories = sorted(memories, key=sort_key, reverse=reverse)

        if not memories:
            empty_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
            empty_frame.pack(pady=80, fill="both", expand=True)

            if EMPTY_STATE_FILE.exists():
                try:
                    img = Image.open(EMPTY_STATE_FILE)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 280))
                    ctk.CTkLabel(empty_frame, image=ctk_img, text="").pack(pady=(0, 24))
                except Exception as e:
                    print(f"Error loading empty state: {e}")

            ctk.CTkLabel(
                empty_frame,
                text="Tu álbum está vacío",
                font=("Segoe UI", 20, "bold"),
                text_color=Colors.TEXT_PRIMARY
            ).pack()

            ctk.CTkLabel(
                empty_frame,
                text="Agrega tu primer recuerdo sonoro",
                font=("Segoe UI", 13),
                text_color=Colors.TEXT_MUTED
            ).pack(pady=(6, 0))
            return

        # Crear grid
        cols = 4
        for idx, memory in enumerate(memories):
            row = idx // cols
            col = idx % cols

            card = self.create_card(memory)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        for col in range(cols):
            self.grid_frame.grid_columnconfigure(col, weight=1, uniform="card")

    def create_card(self, memory: Dict):
        # Frame sombra
        shadow_frame = ctk.CTkFrame(
            self.grid_frame,
            width=200,
            height=248,
            fg_color=Colors.SHADOW,
            corner_radius=12
        )

        # Frame contenedor principal
        card_frame = ctk.CTkFrame(
            shadow_frame,
            width=196,
            height=244,
            fg_color=Colors.CARD_BG,
            border_color=Colors.BORDER,
            border_width=1,
            corner_radius=10
        )
        card_frame.place(x=0, y=0)
        card_frame.grid_propagate(False)

        # Guardar referencia para indicador de reproducción
        self.card_refs[memory.get("id")] = card_frame

        # Actualizar indicador si está reproduciendo
        if memory.get("id") == self.playing_memory_id:
            card_frame.configure(border_color=Colors.PLAYING_GLOW, border_width=2)

        # Variables para animación
        animation_step = [0]
        animation_id = [None]
        max_steps = 4

        # Hover effects
        def animate_enter():
            if animation_step[0] < max_steps:
                animation_step[0] += 1
                progress = animation_step[0] / max_steps
                border_width = 1 + int(progress * 1)
                offset_y = int(-progress * 4)
                card_frame.place(x=0, y=offset_y)
                card_frame.configure(border_color=Colors.GOLD, border_width=border_width)
                animation_id[0] = shadow_frame.after(20, animate_enter)

        def animate_leave():
            if animation_step[0] > 0:
                animation_step[0] -= 1
                progress = animation_step[0] / max_steps
                border_width = 1 + int(progress * 1)
                offset_y = int(-progress * 4)
                card_frame.place(x=0, y=offset_y)
                if animation_step[0] == 0:
                    card_frame.configure(border_color=Colors.BORDER, border_width=1)
                else:
                    card_frame.configure(border_width=border_width)
                shadow_frame.configure(fg_color=Colors.SHADOW)
                animation_id[0] = shadow_frame.after(20, animate_leave)

        def on_enter(e):
            if memory.get("id") != self.playing_memory_id:
                if animation_id[0]:
                    shadow_frame.after_cancel(animation_id[0])
                animate_enter()

        def on_leave(e):
            if memory.get("id") != self.playing_memory_id:
                if animation_id[0]:
                    shadow_frame.after_cancel(animation_id[0])
                animate_leave()

        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)

        # Container para imagen
        image_container = ctk.CTkFrame(
            card_frame,
            width=196,
            height=155,
            fg_color="transparent"
        )
        image_container.pack(pady=(8, 0))
        image_container.pack_propagate(False)

        # Foto circular
        photo_path = self.get_photo_path(memory)
        if photo_path:
            try:
                img = Image.open(photo_path)
                circular_img = make_circular_image(img, (130, 130))
                photo = ctk.CTkImage(light_image=circular_img, dark_image=circular_img, size=(130, 130))
                photo_label = ctk.CTkLabel(image_container, image=photo, text="")
                photo_label.image = photo
                photo_label.place(relx=0.5, rely=0.5, anchor="center")
            except Exception as e:
                print(f"Error cargando imagen: {e}")
                placeholder = ctk.CTkLabel(
                    image_container,
                    text="🎵",
                    font=("Segoe UI Symbol", 40),
                    text_color=Colors.TEXT_MUTED
                )
                placeholder.place(relx=0.5, rely=0.5, anchor="center")
        else:
            placeholder = ctk.CTkLabel(
                image_container,
                text="🎵",
                font=("Segoe UI Symbol", 40),
                text_color=Colors.TEXT_MUTED
            )
            placeholder.place(relx=0.5, rely=0.5, anchor="center")

        for child in image_container.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
        image_container.bind("<Enter>", on_enter)
        image_container.bind("<Leave>", on_leave)

        # "NEW" Badge
        try:
            created_at = datetime.strptime(memory.get("created_at", ""), "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - created_at).total_seconds() < 86400:
                new_badge = ctk.CTkLabel(
                    image_container,
                    text="NUEVO",
                    fg_color=Colors.GOLD,
                    text_color=Colors.BLACK,
                    corner_radius=6,
                    font=("Segoe UI", 9, "bold"),
                    width=50,
                    height=20
                )
                new_badge.place(x=8, y=6)
        except:
            pass

        # Badge de duración del audio
        if memory.get("audio"):
            audio_path = self.get_audio_path(memory)
            if audio_path:
                duration = self.get_audio_duration(audio_path)
                mins = int(duration // 60)
                secs = int(duration % 60)
                duration_text = f"{mins}:{secs:02d}"

                duration_badge = ctk.CTkLabel(
                    image_container,
                    text=duration_text,
                    fg_color=Colors.BLACK,
                    text_color=Colors.TEXT_PRIMARY,
                    corner_radius=6,
                    font=("Segoe UI", 9, "bold"),
                    width=40,
                    height=20
                )
                duration_badge.place(x=8, rely=1.0, anchor="sw", y=-6)

        # Favoritos Button
        is_fav = memory.get("is_favorite", False)
        fav_text = "❤" if is_fav else "♡"

        def toggle_fav():
            new_state = self.dm.toggle_favorite(memory.get("id"))
            fav_btn.configure(
                text="❤" if new_state else "♡",
                text_color=Colors.FAVORITE if new_state else Colors.TEXT_SECONDARY
            )
            if self.current_filter == "Favoritos" and not new_state:
                self.refresh_grid()

        fav_btn = ctk.CTkButton(
            image_container,
            text=fav_text,
            width=28,
            height=28,
            fg_color=Colors.BLACK,
            hover_color=Colors.SURFACE,
            text_color=Colors.FAVORITE if is_fav else Colors.TEXT_SECONDARY,
            corner_radius=14,
            command=toggle_fav,
            font=("Segoe UI", 14)
        )
        fav_btn.place(relx=0.95, y=6, anchor="ne")

        # Info container
        info_container = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_container.pack(fill="x", padx=10, pady=(4, 8))

        # Nombre
        name_label = ctk.CTkLabel(
            info_container,
            text=memory.get("name", "Sin nombre")[:20],
            font=("Segoe UI", 13, "bold"),
            text_color=Colors.TEXT_PRIMARY
        )
        name_label.pack()

        # Row con categoría y botones
        bottom_row = ctk.CTkFrame(info_container, fg_color="transparent")
        bottom_row.pack(pady=(4, 0))

        # Categoría
        category_frame = ctk.CTkFrame(
            bottom_row,
            fg_color=Colors.SURFACE,
            corner_radius=6
        )
        category_frame.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            category_frame,
            text=memory.get("category", ""),
            font=("Segoe UI", 10),
            text_color=Colors.GOLD
        ).pack(padx=8, pady=3)

        # Botón play
        if memory.get("audio"):
            def play_and_open():
                self.auto_play_next = True
                self.show_detail(memory)

            play_btn_small = ctk.CTkButton(
                bottom_row,
                text="▶",
                width=42,
                height=24,
                corner_radius=6,
                fg_color=Colors.GOLD,
                hover_color=Colors.GOLD_LIGHT,
                text_color=Colors.BLACK,
                font=("Arial", 14, "bold"),
                command=play_and_open
            )
            play_btn_small.pack(side="left")

        # Función para reproducir directamente (doble clic)
        def play_direct(e):
            if memory.get("audio"):
                audio_path = self.get_audio_path(memory)
                if audio_path:
                    # Detener playlist si está activa
                    if self.playlist_mode:
                        self.playlist_mode = False
                        self.playlist_btn.configure(
                            fg_color=Colors.CARD_BG,
                            text_color=Colors.TEXT_SECONDARY,
                            text="▶ Playlist"
                        )

                    # Detener reproducción actual si hay
                    if self.playing:
                        pygame.mixer.music.stop()

                    # Reproducir
                    pygame.mixer.music.load(audio_path)
                    pygame.mixer.music.play()
                    self.playing = True
                    self.playing_memory_id = memory.get("id")
                    self.update_playing_indicator()

        # Hacer tarjeta clickeable
        # Click simple = abrir detalle, Doble clic = reproducir directo
        for w in [card_frame, info_container, name_label, image_container]:
             w.bind("<Button-1>", lambda e, m=memory: self.show_detail(m))
             w.bind("<Double-Button-1>", play_direct)
             if w not in [image_container]:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)

        return shadow_frame

    def show_edit_dialog(self, memory: Dict):
        """Muestra diálogo para editar un recuerdo."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Recuerdo")
        dialog.geometry("450x550")
        dialog.configure(fg_color=Colors.DARK_BG)
        dialog.transient(self)
        dialog.grab_set()

        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Nombre
        ctk.CTkLabel(content, text="Nombre *", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        name_entry = ctk.CTkEntry(content, fg_color=Colors.CARD_BG, border_color=Colors.BORDER)
        name_entry.insert(0, memory.get("name", ""))
        name_entry.pack(fill="x", pady=(0, 15))

        # Categoría
        ctk.CTkLabel(content, text="Categoría", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        category_var = ctk.StringVar(value=memory.get("category", CATEGORIES[0]))
        category_menu = ctk.CTkOptionMenu(
            content,
            values=CATEGORIES,
            variable=category_var,
            fg_color=Colors.CARD_BG,
            button_color=Colors.SURFACE,
            button_hover_color=Colors.GOLD
        )
        category_menu.pack(fill="x", pady=(0, 15))

        # Fecha
        ctk.CTkLabel(content, text="Fecha", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        date_entry = ctk.CTkEntry(content, fg_color=Colors.CARD_BG, border_color=Colors.BORDER)
        date_entry.insert(0, memory.get("date", ""))
        date_entry.pack(fill="x", pady=(0, 15))

        # Nota
        ctk.CTkLabel(content, text="Nota breve", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        note_entry = ctk.CTkTextbox(content, height=70, fg_color=Colors.CARD_BG, border_color=Colors.BORDER)
        note_entry.insert("1.0", memory.get("note", ""))
        note_entry.pack(fill="x", pady=(0, 15))

        # Cambiar foto
        form_data = {"new_photo": None}
        photo_label = ctk.CTkLabel(content, text="Foto actual conservada", text_color=Colors.TEXT_MUTED)

        def pick_new_photo():
            path = filedialog.askopenfilename(
                title="Seleccionar Nueva Foto",
                filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp *.gif")]
            )
            if path:
                form_data["new_photo"] = path
                photo_label.configure(text=f"Nueva: {Path(path).name}", text_color=Colors.SUCCESS)

        ctk.CTkButton(
            content,
            text="📷 Cambiar Foto",
            fg_color=Colors.CARD_BG,
            hover_color=Colors.SURFACE,
            command=pick_new_photo
        ).pack(fill="x")
        photo_label.pack(pady=(5, 15))

        # Botones
        buttons_frame = ctk.CTkFrame(content, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))

        def save_changes():
            updates = {
                "name": name_entry.get().strip(),
                "category": category_var.get(),
                "date": date_entry.get(),
                "note": note_entry.get("1.0", "end").strip()[:100]
            }

            if not updates["name"]:
                messagebox.showwarning("Error", "El nombre es obligatorio")
                return

            # Si hay nueva foto
            if form_data["new_photo"]:
                # Eliminar foto anterior
                if memory.get("photo"):
                    old_photo = PHOTOS_DIR / memory["photo"]
                    if old_photo.exists():
                        old_photo.unlink()

                # Copiar nueva
                new_photo_name = self.dm.copy_to_assets(form_data["new_photo"], "photo")
                if new_photo_name:
                    updates["photo"] = new_photo_name

            self.dm.update(memory.get("id"), updates)
            dialog.destroy()
            self.refresh_grid()

        ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            height=38,
            fg_color=Colors.SURFACE,
            hover_color=Colors.BORDER,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            command=dialog.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            buttons_frame,
            text="Guardar Cambios",
            height=38,
            fg_color=Colors.GOLD,
            hover_color="#D4B06A",
            text_color=Colors.BLACK,
            command=save_changes
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def add_placeholder(self, parent):
        ctk.CTkLabel(
            parent,
            text="🎵",
            font=("Roboto", 80),
            text_color=Colors.TEXT_MUTED
        ).pack()

    def get_photo_path(self, memory: Dict) -> Optional[str]:
        if memory.get("photo"):
            photo = PHOTOS_DIR / memory["photo"]
            if photo.exists():
                return str(photo)
        if DEFAULT_AVATAR.exists():
            return str(DEFAULT_AVATAR)
        return None

    def on_filter_click(self, category: str):
        self.current_filter = category

        for cat, btn in self.filter_buttons.items():
            if cat == category:
                btn.configure(
                    fg_color=Colors.GOLD,
                    text_color=Colors.BLACK,
                    border_color=Colors.GOLD,
                    hover_color=Colors.GOLD_GLOW
                )
            else:
                btn.configure(
                    fg_color=Colors.CARD_BG,
                    text_color=Colors.TEXT_SECONDARY,
                    border_color=Colors.BORDER,
                    hover_color=Colors.SURFACE
                )

        self.refresh_grid()

    def on_search(self, event):
        self.search_query = self.search_entry.get()
        self.refresh_grid()

    def show_add_dialog(self, prefill_file: str = None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nuevo Recuerdo")
        dialog.geometry("450x520")
        dialog.configure(fg_color=Colors.DARK_BG)
        dialog.transient(self)
        dialog.grab_set()

        form_data = {"photo": None, "audio": None}

        # Pre-fill si hay archivo
        if prefill_file:
            ext = Path(prefill_file).suffix.lower()
            if ext in ALLOWED_IMAGE:
                form_data["photo"] = prefill_file
            elif ext in ALLOWED_AUDIO:
                form_data["audio"] = prefill_file

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Nombre
        ctk.CTkLabel(content, text="Nombre *", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        name_entry = ctk.CTkEntry(content, fg_color=Colors.CARD_BG, border_color=Colors.BORDER)
        name_entry.pack(fill="x", pady=(0, 10))

        # Categoría
        ctk.CTkLabel(content, text="Categoría", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        category_var = ctk.StringVar(value=CATEGORIES[0])
        category_menu = ctk.CTkOptionMenu(
            content,
            values=CATEGORIES,
            variable=category_var,
            fg_color=Colors.CARD_BG,
            button_color=Colors.SURFACE,
            button_hover_color=Colors.GOLD
        )
        category_menu.pack(fill="x", pady=(0, 10))

        # Fecha
        ctk.CTkLabel(content, text="Fecha", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        date_entry = ctk.CTkEntry(content, fg_color=Colors.CARD_BG, border_color=Colors.BORDER)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.pack(fill="x", pady=(0, 10))

        # Nota
        ctk.CTkLabel(content, text="Nota breve", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        note_entry = ctk.CTkTextbox(content, height=60, fg_color=Colors.CARD_BG, border_color=Colors.BORDER)
        note_entry.pack(fill="x", pady=(0, 10))

        # Foto
        photo_text = f"✓ {Path(form_data['photo']).name}" if form_data["photo"] else "Sin foto"
        photo_color = Colors.SUCCESS if form_data["photo"] else Colors.TEXT_MUTED
        photo_label = ctk.CTkLabel(content, text=photo_text, text_color=photo_color)

        def pick_photo():
            path = filedialog.askopenfilename(
                title="Seleccionar Foto",
                filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp *.gif"), ("Todos", "*.*")]
            )
            if path:
                form_data["photo"] = path
                photo_label.configure(text=f"✓ {Path(path).name}", text_color=Colors.SUCCESS)

        photo_btn = ctk.CTkButton(
            content,
            text="📷 Seleccionar Foto",
            fg_color=Colors.CARD_BG,
            hover_color=Colors.SURFACE,
            command=pick_photo
        )
        photo_btn.pack(fill="x")
        photo_label.pack(pady=(3, 10))

        # Audio
        audio_text = f"✓ {Path(form_data['audio']).name}" if form_data["audio"] else "Sin audio *"
        audio_color = Colors.SUCCESS if form_data["audio"] else Colors.TEXT_MUTED
        audio_label = ctk.CTkLabel(content, text=audio_text, text_color=audio_color)

        def pick_audio():
            path = filedialog.askopenfilename(
                title="Seleccionar Audio",
                filetypes=[("Audio", "*.mp3 *.wav *.m4a *.ogg *.flac"), ("Todos", "*.*")]
            )
            if path:
                form_data["audio"] = path
                audio_label.configure(text=f"✓ {Path(path).name}", text_color=Colors.SUCCESS)

        audio_btn = ctk.CTkButton(
            content,
            text="🎵 Seleccionar Audio",
            fg_color=Colors.CARD_BG,
            hover_color=Colors.SURFACE,
            command=pick_audio
        )
        audio_btn.pack(fill="x")
        audio_label.pack(pady=(3, 10))

        # Error label
        error_label = ctk.CTkLabel(content, text="", text_color=Colors.ERROR)
        error_label.pack(pady=(5, 0))

        # Botones
        buttons_frame = ctk.CTkFrame(content, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))

        def save():
            if not name_entry.get().strip():
                error_label.configure(text="El nombre es obligatorio")
                return

            if not form_data["audio"]:
                error_label.configure(text="Selecciona un archivo de audio")
                return

            photo_name = self.dm.copy_to_assets(form_data["photo"], "photo") if form_data["photo"] else None
            audio_name = self.dm.copy_to_assets(form_data["audio"], "audio")

            if not audio_name:
                error_label.configure(text="Error al copiar audio")
                return

            self.dm.add({
                "name": name_entry.get().strip(),
                "category": category_var.get(),
                "date": date_entry.get(),
                "note": note_entry.get("1.0", "end").strip()[:100],
                "photo": photo_name,
                "audio": audio_name
            })

            dialog.destroy()
            self.refresh_grid()

        ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            height=38,
            fg_color=Colors.SURFACE,
            hover_color=Colors.BORDER,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            command=dialog.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            buttons_frame,
            text="Guardar",
            height=38,
            fg_color=Colors.GOLD,
            hover_color="#D4B06A",
            text_color=Colors.BLACK,
            command=save
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def show_recording_dialog(self):
        if not self.recorder:
            messagebox.showerror("Error", "Librerías de grabación no disponibles.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Captura Recuerdos")
        dialog.geometry("500x700")
        dialog.configure(fg_color=Colors.DARK_BG)
        dialog.transient(self)
        dialog.grab_set()

        form_data = {"photo": None, "audio_temp": None}
        devices = self.recorder.get_devices()
        device_names = [d["name"] for d in devices]
        selected_device_idx = ctk.IntVar(value=devices[0]["id"] if devices else 0)

        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(content, text="🎙️ Grabación en vivo", font=("Roboto", 20, "bold"), text_color=Colors.GOLD).pack(pady=(0, 20))

        ctk.CTkLabel(content, text="Micrófono", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        if not devices:
            ctk.CTkLabel(content, text="No se detectaron micrófonos", text_color=Colors.ERROR).pack()
        else:
            dev_menu = ctk.CTkOptionMenu(
                content,
                values=device_names,
                fg_color=Colors.CARD_BG,
                button_color=Colors.SURFACE,
                command=lambda name: selected_device_idx.set(next(d["id"] for d in devices if d["name"] == name))
            )
            dev_menu.pack(fill="x", pady=(0, 15))

        rec_frame = ctk.CTkFrame(content, fg_color=Colors.SURFACE, corner_radius=10)
        rec_frame.pack(fill="x", pady=(0, 20))

        rec_status = ctk.StringVar(value="Listo para grabar")
        rec_time = ctk.IntVar(value=0)
        is_recording = [False]

        time_label = ctk.CTkLabel(rec_frame, text="00:00", font=("Roboto", 30, "bold"), text_color=Colors.TEXT_PRIMARY)
        time_label.pack(pady=10)

        status_label = ctk.CTkLabel(rec_frame, textvariable=rec_status, text_color=Colors.TEXT_SECONDARY)
        status_label.pack(pady=(0, 10))

        def update_timer():
            if is_recording[0]:
                rec_time.set(rec_time.get() + 1)
                mins, secs = divmod(rec_time.get(), 60)
                time_label.configure(text=f"{mins:02d}:{secs:02d}", text_color=Colors.ERROR)
                dialog.after(1000, update_timer)

        btns_container = ctk.CTkFrame(rec_frame, fg_color="transparent")
        btns_container.pack(pady=15)

        def play_preview():
            if form_data["audio_temp"]:
                try:
                    pygame.mixer.music.load(form_data["audio_temp"])
                    pygame.mixer.music.play()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al reproducir: {e}")

        def toggle_record():
            if not is_recording[0]:
                if form_data["audio_temp"]:
                     try:
                         try: pygame.mixer.music.unload()
                         except: pass
                         os.remove(form_data["audio_temp"])
                         form_data["audio_temp"] = None
                     except: pass

                try:
                    self.recorder.start_recording(device_id=selected_device_idx.get())
                    is_recording[0] = True
                    rec_time.set(0)
                    rec_status.set("Grabando...")

                    rec_btn.configure(text="⏹ Detener", fg_color=Colors.ERROR, hover_color="#B54A5A")
                    preview_btn.pack_forget()

                    update_timer()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo iniciar grabacion: {e}")
            else:
                path = self.recorder.stop_recording()
                is_recording[0] = False
                rec_status.set("Grabación finalizada")
                time_label.configure(text_color=Colors.SUCCESS)

                rec_btn.configure(text="🔄 Grabar de nuevo", fg_color=Colors.CARD_BG, hover_color=Colors.SURFACE)

                if path:
                    form_data["audio_temp"] = path
                    preview_btn.pack(side="left", padx=10)

        rec_btn = ctk.CTkButton(
            btns_container,
            text="🔴 Grabar",
            font=("Roboto", 14, "bold"),
            fg_color=Colors.CARD_BG,
            hover_color=Colors.SURFACE,
            border_color=Colors.ERROR,
            border_width=1,
            height=40,
            command=toggle_record
        )
        rec_btn.pack(side="left", padx=5)

        preview_btn = ctk.CTkButton(
            btns_container,
            text="▶ Escuchar",
            font=("Roboto", 14, "bold"),
            fg_color=Colors.GOLD,
            hover_color="#D4B06A",
            text_color=Colors.BLACK,
            height=40,
            command=play_preview
        )

        ctk.CTkFrame(content, height=2, fg_color=Colors.BORDER).pack(fill="x", pady=10)

        ctk.CTkLabel(content, text="Nombre del Recuerdo *", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        name_entry = ctk.CTkEntry(content, fg_color=Colors.CARD_BG, border_color=Colors.BORDER)
        name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(content, text="Categoría", text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        category_var = ctk.StringVar(value=CATEGORIES[0])
        category_menu = ctk.CTkOptionMenu(
            content,
            values=CATEGORIES,
            variable=category_var,
            fg_color=Colors.CARD_BG,
            button_color=Colors.SURFACE
        )
        category_menu.pack(fill="x", pady=(0, 10))

        photo_label = ctk.CTkLabel(content, text="Sin foto (usar avatar por defecto)", text_color=Colors.TEXT_MUTED)
        def pick_photo():
            path = filedialog.askopenfilename(title="Seleccionar Foto", filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")])
            if path:
                form_data["photo"] = path
                photo_label.configure(text=f"✓ {Path(path).name}", text_color=Colors.SUCCESS)

        ctk.CTkButton(content, text="📷 Agregar Foto (Opcional)", fg_color=Colors.CARD_BG, hover_color=Colors.SURFACE, command=pick_photo).pack(fill="x")
        photo_label.pack(pady=(5, 10))

        buttons_frame = ctk.CTkFrame(content, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 0))

        def save():
            if not name_entry.get().strip():
                messagebox.showwarning("Faltan datos", "El nombre es obligatorio")
                return
            if not form_data["audio_temp"]:
                messagebox.showwarning("Falta audio", "Debes grabar un audio primero")
                return

            photo_name = self.dm.copy_to_assets(form_data["photo"], "photo") if form_data["photo"] else None
            audio_name = self.dm.copy_to_assets(form_data["audio_temp"], "audio")

            if audio_name and AUDIO_AVAILABLE:
                audio_full_path = str(AUDIOS_DIR / audio_name)
                wave_name = f"waveform_{uuid.uuid4()}.png"
                wave_path = str(WAVEFORMS_DIR / wave_name)
                if generate_waveform(audio_full_path, wave_path):
                    pass

            memory_data = {
                "name": name_entry.get().strip(),
                "category": category_var.get(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "note": "Grabación en vivo",
                "photo": photo_name,
                "audio": audio_name
            }
            if 'wave_name' in locals():
                memory_data["waveform"] = wave_name

            self.dm.add(memory_data)

            try:
                os.remove(form_data["audio_temp"])
            except: pass

            dialog.destroy()
            self.refresh_grid()

        ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            height=38,
            fg_color=Colors.SURFACE,
            hover_color=Colors.BORDER,
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            command=dialog.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            buttons_frame,
            text="Guardar Recuerdo",
            height=38,
            fg_color=Colors.GOLD,
            hover_color="#D4B06A",
            text_color=Colors.BLACK,
            command=save
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def show_detail(self, memory: Dict):
        if self.current_dialog and self.current_dialog.winfo_exists():
            try:
                pygame.mixer.music.stop()
                self.playing = False
                self.current_dialog.destroy()
            except:
                pass

        dialog = ctk.CTkToplevel(self)
        dialog.title(memory.get("name", "Recuerdo"))
        dialog.geometry("650x600")
        dialog.configure(fg_color=Colors.DARK_BG)
        dialog.transient(self)

        self.current_dialog = dialog

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Foto circular en detalle
        photo_path = self.get_photo_path(memory)
        if photo_path:
            try:
                img = Image.open(photo_path)
                circular_img = make_circular_image(img, (250, 250))
                photo = ctk.CTkImage(light_image=circular_img, dark_image=circular_img, size=(250, 250))
                ctk.CTkLabel(content, image=photo, text="").pack(pady=10)
            except:
                pass

        ctk.CTkLabel(
            content,
            text=memory.get("name", ""),
            font=("Roboto", 22, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(10, 5))

        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack()

        cat_frame = ctk.CTkFrame(info_frame, fg_color=Colors.CARD_BG, corner_radius=15)
        cat_frame.pack(side="left", padx=5)
        ctk.CTkLabel(cat_frame, text=memory.get("category", ""), text_color=Colors.GOLD, font=("Roboto", 11)).pack(padx=10, pady=5)

        ctk.CTkLabel(info_frame, text=memory.get("date", ""), text_color=Colors.TEXT_SECONDARY, font=("Roboto", 11)).pack(side="left", padx=5)

        note = memory.get("note", "").strip()
        if note:
            note_frame = ctk.CTkFrame(content, fg_color=Colors.CARD_BG, corner_radius=8)
            note_frame.pack(fill="x", pady=15)
            ctk.CTkLabel(note_frame, text=f'"{note}"', text_color=Colors.TEXT_SECONDARY, wraplength=580, font=("Roboto", 13, "italic")).pack(padx=10, pady=10)

        audio_path = self.get_audio_path(memory)
        if audio_path:
            player_frame = ctk.CTkFrame(
                content,
                fg_color=Colors.SURFACE,
                corner_radius=12,
                border_width=1,
                border_color=Colors.BORDER
            )
            player_frame.pack(fill="x", pady=10)

            # Header del reproductor
            player_header = ctk.CTkFrame(player_frame, fg_color=Colors.CARD_BG, corner_radius=8)
            player_header.pack(fill="x", padx=15, pady=(15, 10))

            memory_name = memory.get("name", "Sin nombre")
            display_name = memory_name[:35] + "..." if len(memory_name) > 35 else memory_name

            ctk.CTkLabel(
                player_header,
                text=f"🎵 {display_name}",
                font=("Roboto", 14, "bold"),
                text_color=Colors.TEXT_PRIMARY
            ).pack(side="left", padx=10, pady=8)

            status_var = ctk.StringVar(value="⏹ Detenido")
            status_label = ctk.CTkLabel(
                player_header,
                textvariable=status_var,
                font=("Roboto", 11),
                text_color=Colors.TEXT_MUTED
            )
            status_label.pack(side="right", padx=10, pady=8)

            waveform_img = None
            if AUDIO_AVAILABLE:
                wave_path = None
                if "waveform" in memory:
                    wp = WAVEFORMS_DIR / memory["waveform"]
                    if wp.exists():
                        wave_path = str(wp)

                if not wave_path:
                     wave_name = f"waveform_{memory['id']}.png"
                     wave_path_target = WAVEFORMS_DIR / wave_name
                     if not wave_path_target.exists():
                         if generate_waveform(audio_path, str(wave_path_target)):
                             wave_path = str(wave_path_target)
                     else:
                         wave_path = str(wave_path_target)

                if wave_path:
                     try:
                         pil_wave = Image.open(wave_path)
                         waveform_img = ctk.CTkImage(light_image=pil_wave, dark_image=pil_wave, size=(500, 100))
                     except: pass

            if waveform_img:
                wave_label = ctk.CTkLabel(player_frame, image=waveform_img, text="")
                wave_label.pack(pady=(20, 0))

            play_var = ctk.StringVar(value="▶")
            time_var = ctk.StringVar(value="0:00")
            total_time_var = ctk.StringVar(value="0:00")
            volume_var = ctk.DoubleVar(value=0.7)
            song_length = [0]
            start_time = [0]
            pause_time = [0]
            is_paused = [False]
            is_seeking = [False]  # Para evitar conflictos al arrastrar
            loop_enabled = [False]

            pygame.mixer.music.set_volume(0.7)

            # Calcular y mostrar tiempo total al cargar
            try:
                initial_duration = self.get_audio_duration(audio_path)
                if initial_duration > 0:
                    song_length[0] = initial_duration
                    mins = int(initial_duration // 60)
                    secs = int(initial_duration % 60)
                    total_time_var.set(f"{mins}:{secs:02d}")
            except:
                pass

            def update_status(status):
                """Actualiza el indicador de estado y el borde del reproductor."""
                if status == "playing":
                    status_var.set("▶ Reproduciendo")
                    status_label.configure(text_color=Colors.GOLD)
                    player_frame.configure(border_color=Colors.PLAYING_GLOW, border_width=2)
                elif status == "paused":
                    status_var.set("⏸ Pausado")
                    status_label.configure(text_color=Colors.TEXT_SECONDARY)
                    player_frame.configure(border_color=Colors.GOLD, border_width=1)
                else:  # stopped
                    status_var.set("⏹ Detenido")
                    status_label.configure(text_color=Colors.TEXT_MUTED)
                    player_frame.configure(border_color=Colors.BORDER, border_width=1)

            def format_time(seconds):
                """Formatea segundos a mm:ss."""
                mins = int(seconds // 60)
                secs = int(seconds % 60)
                return f"{mins}:{secs:02d}"

            def update_time():
                if self.playing and pygame.mixer.music.get_busy() and not is_paused[0]:
                    try:
                        import time
                        elapsed = time.time() - start_time[0] + pause_time[0]

                        time_var.set(format_time(elapsed))

                        # Solo actualizar slider si no está siendo arrastrado
                        if not is_seeking[0]:
                            max_duration = song_length[0] if song_length[0] > 0 else 300
                            progress = elapsed / max_duration
                            progress_var.set(min(progress, 1.0))

                        if dialog.winfo_exists():
                            dialog.after(100, update_time)
                    except Exception as e:
                        print(f"Error update_time: {e}")
                elif self.playing and not is_paused[0]:
                    # Audio terminó
                    if loop_enabled[0] and song_length[0] > 0:
                        # Repetir el audio
                        import time as time_mod
                        try:
                            pygame.mixer.music.load(audio_path)
                            pygame.mixer.music.play()
                            start_time[0] = time_mod.time()
                            pause_time[0] = 0
                            self.playing = True
                            update_time()
                            return
                        except:
                            pass

                    self.playing = False
                    self.playing_memory_id = None
                    self.update_playing_indicator()
                    play_var.set("▶")
                    time_var.set("0:00")
                    progress_var.set(0)
                    start_time[0] = 0
                    pause_time[0] = 0
                    update_status("stopped")

            def toggle_play():
                import time as time_module

                # Si está en modo playlist, detenerla al dar play manual
                if self.playlist_mode:
                    self.playlist_mode = False
                    self.playlist_btn.configure(
                        fg_color=Colors.CARD_BG,
                        text_color=Colors.TEXT_SECONDARY,
                        text="▶ Playlist"
                    )

                if self.playing:
                    pygame.mixer.music.pause()
                    self.playing = False
                    is_paused[0] = True
                    pause_time[0] += time_module.time() - start_time[0]
                    play_var.set("▶")
                    update_status("paused")
                else:
                    try:
                        if is_paused[0]:
                            pygame.mixer.music.unpause()
                            start_time[0] = time_module.time()
                            is_paused[0] = False
                            self.playing = True
                            self.playing_memory_id = memory.get("id")
                            self.update_playing_indicator()
                            update_status("playing")
                            update_time()
                        else:
                            if pygame.mixer.music.get_busy():
                                pygame.mixer.music.stop()

                            # Detectar duración del audio
                            song_length[0] = self.get_audio_duration(audio_path)

                            # Mostrar tiempo total
                            total_time_var.set(format_time(song_length[0]))

                            pygame.mixer.music.load(audio_path)
                            pygame.mixer.music.play()

                            start_time[0] = time_module.time()
                            pause_time[0] = 0
                            is_paused[0] = False
                            self.playing = True
                            self.playing_memory_id = memory.get("id")
                            self.update_playing_indicator()
                            update_status("playing")

                            update_time()

                        play_var.set("⏸")
                    except Exception as e:
                        print(f"Error: {e}")
                        messagebox.showerror("Error", f"Error: {e}")

            if self.auto_play_next:
                self.auto_play_next = False
                dialog.after(300, toggle_play)

            def stop():
                pygame.mixer.music.stop()
                self.playing = False
                self.playing_memory_id = None
                self.update_playing_indicator()
                is_paused[0] = False
                pause_time[0] = 0
                start_time[0] = 0
                play_var.set("▶")
                time_var.set("0:00")
                progress_var.set(0)
                update_status("stopped")

            def skip_backward():
                """Retrocede 10 segundos en la reproducción."""
                import time as time_mod
                if song_length[0] > 0 and (self.playing or is_paused[0]):
                    current_pos = time_mod.time() - start_time[0] + pause_time[0] if self.playing else pause_time[0]
                    new_pos = max(0, current_pos - 10)
                    try:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play(start=new_pos)

                        start_time[0] = time_mod.time()
                        pause_time[0] = new_pos
                        is_paused[0] = False
                        self.playing = True
                        self.playing_memory_id = memory.get("id")
                        self.update_playing_indicator()
                        play_var.set("⏸")
                        update_status("playing")
                        update_time()
                    except Exception as e:
                        print(f"Error skip backward: {e}")

            def skip_forward():
                """Adelanta 10 segundos en la reproducción."""
                import time as time_mod
                if song_length[0] > 0 and (self.playing or is_paused[0]):
                    current_pos = time_mod.time() - start_time[0] + pause_time[0] if self.playing else pause_time[0]
                    new_pos = min(song_length[0] - 1, current_pos + 10)

                    if new_pos >= song_length[0] - 1:
                        # Si llegamos al final, detener
                        stop()
                        return

                    try:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play(start=new_pos)

                        start_time[0] = time_mod.time()
                        pause_time[0] = new_pos
                        is_paused[0] = False
                        self.playing = True
                        self.playing_memory_id = memory.get("id")
                        self.update_playing_indicator()
                        play_var.set("⏸")
                        update_status("playing")
                        update_time()
                    except Exception as e:
                        print(f"Error skip forward: {e}")

            def toggle_loop():
                """Activa/desactiva la repetición del audio."""
                loop_enabled[0] = not loop_enabled[0]
                if loop_enabled[0]:
                    loop_btn.configure(fg_color=Colors.GOLD, text_color=Colors.BLACK)
                else:
                    loop_btn.configure(fg_color=Colors.CARD_BG, text_color=Colors.TEXT_SECONDARY)

            def on_volume(val):
                pygame.mixer.music.set_volume(val)

            controls = ctk.CTkFrame(player_frame, fg_color="transparent")
            controls.pack(padx=20, pady=20, fill="both")

            # Barra de progreso con tiempo actual/total
            progress_row = ctk.CTkFrame(controls, fg_color="transparent")
            progress_row.pack(fill="x", pady=(0, 15))

            # Tiempo actual (izquierda)
            ctk.CTkLabel(
                progress_row,
                textvariable=time_var,
                font=("Roboto", 12),
                text_color=Colors.TEXT_SECONDARY,
                width=45
            ).pack(side="left")

            # Barra de progreso interactiva (seekable)
            progress_var = ctk.DoubleVar(value=0)
            last_seek_time = [0]

            def on_seek(value):
                """Permite adelantar/retroceder al hacer clic en la barra."""
                import time as time_mod

                # Evitar múltiples seeks en poco tiempo
                current_time = time_mod.time()
                if current_time - last_seek_time[0] < 0.3:
                    return
                last_seek_time[0] = current_time

                if song_length[0] > 0 and self.playing:
                    # Calcular nueva posición en segundos
                    new_pos = value * song_length[0]
                    try:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play(start=new_pos)

                        start_time[0] = time_mod.time()
                        pause_time[0] = new_pos
                        is_paused[0] = False
                        self.playing = True
                        self.playing_memory_id = memory.get("id")
                        self.update_playing_indicator()
                        play_var.set("⏸")
                        update_status("playing")
                        update_time()
                    except Exception as e:
                        print(f"Error seeking: {e}")

            progress_slider = ctk.CTkSlider(
                progress_row,
                from_=0,
                to=1,
                variable=progress_var,
                button_color=Colors.GOLD,
                button_hover_color="#D4B06A",
                progress_color=Colors.GOLD,
                fg_color=Colors.BORDER,
                height=14,
                command=on_seek
            )
            progress_slider.pack(side="left", fill="x", expand=True, padx=10)
            progress_slider.set(0)

            # Tiempo total (derecha)
            ctk.CTkLabel(
                progress_row,
                textvariable=total_time_var,
                font=("Roboto", 12),
                text_color=Colors.TEXT_SECONDARY,
                width=45
            ).pack(side="right")

            # Separador
            ctk.CTkFrame(controls, fg_color=Colors.BORDER, height=1).pack(fill="x", pady=(0, 15))

            # Fila de controles principales
            row1 = ctk.CTkFrame(controls, fg_color="transparent")
            row1.pack(fill="x")

            # Contenedor de botones de reproducción (izquierda)
            btn_container = ctk.CTkFrame(row1, fg_color="transparent")
            btn_container.pack(side="left")

            # Botón retroceder 10s
            ctk.CTkButton(
                btn_container,
                text="⏪",
                width=45,
                height=40,
                fg_color=Colors.CARD_BG,
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                font=("Segoe UI Symbol", 16),
                command=skip_backward
            ).pack(side="left", padx=(0, 5))

            # Botón Play/Pause
            ctk.CTkButton(
                btn_container,
                textvariable=play_var,
                width=60,
                height=40,
                fg_color=Colors.GOLD,
                hover_color="#D4B06A",
                text_color=Colors.BLACK,
                font=("Segoe UI Symbol", 20),
                command=toggle_play
            ).pack(side="left", padx=5)

            # Botón adelantar 10s
            ctk.CTkButton(
                btn_container,
                text="⏩",
                width=45,
                height=40,
                fg_color=Colors.CARD_BG,
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                font=("Segoe UI Symbol", 16),
                command=skip_forward
            ).pack(side="left", padx=5)

            # Botón Stop
            ctk.CTkButton(
                btn_container,
                text="⏹",
                width=45,
                height=40,
                fg_color=Colors.CARD_BG,
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                font=("Arial", 16, "bold"),
                command=stop
            ).pack(side="left", padx=(5, 15))

            # Botón Loop
            loop_btn = ctk.CTkButton(
                btn_container,
                text="🔁",
                width=45,
                height=40,
                fg_color=Colors.CARD_BG,
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_SECONDARY,
                font=("Segoe UI Symbol", 16),
                command=toggle_loop
            )
            loop_btn.pack(side="left")

            # Control de volumen (derecha)
            vol_container = ctk.CTkFrame(row1, fg_color="transparent")
            vol_container.pack(side="right")

            ctk.CTkLabel(vol_container, text="🔊", font=("Roboto", 14)).pack(side="left", padx=(0, 8))
            ctk.CTkSlider(
                vol_container,
                from_=0,
                to=1,
                variable=volume_var,
                button_color=Colors.GOLD,
                progress_color=Colors.GOLD,
                fg_color=Colors.BORDER,
                command=on_volume,
                width=120
            ).pack(side="left")

        buttons = ctk.CTkFrame(content, fg_color="transparent")
        buttons.pack(fill="x", pady=(20, 0))

        def delete():
            if messagebox.askyesno("Confirmar", "¿Eliminar este recuerdo?"):
                if self.playing:
                    pygame.mixer.music.stop()
                    self.playing = False
                    self.playing_memory_id = None
                    self.update_playing_indicator()

                try:
                    pygame.mixer.music.unload()
                except:
                    pass

                self.dm.delete(memory.get("id"))
                dialog.destroy()
                self.refresh_grid()

        def close():
            if self.playing:
                pygame.mixer.music.stop()
                self.playing = False
                self.playing_memory_id = None
                self.update_playing_indicator()
            dialog.destroy()

        def edit():
            dialog.destroy()
            self.show_edit_dialog(memory)

        dialog.protocol("WM_DELETE_WINDOW", close)

        ctk.CTkButton(
            buttons,
            text="🗑",
            width=40,
            height=40,
            fg_color=Colors.ERROR,
            hover_color="#B54A5A",
            command=delete,
            font=("Segoe UI Symbol", 20)
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            buttons,
            text="✏ Editar",
            width=80,
            height=40,
            fg_color=Colors.SURFACE,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            command=edit
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            buttons,
            text="Cerrar",
            fg_color=Colors.GOLD,
            hover_color="#D4B06A",
            text_color=Colors.BLACK,
            command=close
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))


    def get_audio_duration(self, audio_path: str) -> float:
        """Obtiene la duración del audio en segundos usando múltiples métodos."""
        duration = 0

        # Método 1: Usar mutagen si está disponible
        try:
            from mutagen.mp3 import MP3
            from mutagen.wave import WAVE
            from mutagen.mp4 import MP4

            ext = Path(audio_path).suffix.lower()
            if ext == '.mp3':
                audio_info = MP3(audio_path)
            elif ext == '.wav':
                audio_info = WAVE(audio_path)
            elif ext in ['.m4a', '.mp4']:
                audio_info = MP4(audio_path)
            else:
                audio_info = None

            if audio_info and hasattr(audio_info.info, 'length'):
                duration = audio_info.info.length
        except:
            pass

        # Método 2: Usar wave module para WAV (fallback)
        if duration == 0:
            try:
                import wave
                ext = Path(audio_path).suffix.lower()
                if ext == '.wav':
                    with wave.open(audio_path, 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration = frames / float(rate)
            except:
                pass

        # Método 3: Usar soundfile si está disponible
        if duration == 0:
            try:
                import soundfile as sf
                data, samplerate = sf.read(audio_path)
                duration = len(data) / samplerate
            except:
                pass

        # Si no se pudo detectar, usar un fallback más corto (30 segundos)
        if duration == 0:
            duration = 30

        return duration

    def get_audio_path(self, memory: Dict) -> Optional[str]:
        if memory.get("audio"):
            audio = AUDIOS_DIR / memory["audio"]
            if audio.exists():
                return str(audio)
        return None

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = VoiceVault()
    app.mainloop()
