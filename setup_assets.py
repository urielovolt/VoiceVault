"""
Script para generar los assets iniciales de VoiceVault.
Ejecutar una vez antes de usar la aplicación.
"""

from PIL import Image, ImageDraw
from pathlib import Path

# Rutas
ASSETS_DIR = Path(__file__).parent / "assets"
DEFAULT_AVATAR = ASSETS_DIR / "default_avatar.png"
APP_ICON = ASSETS_DIR / "app_icon.png"

# Colores
BG_COLOR = (20, 20, 20)  # #141414
ICON_COLOR = (197, 160, 89)  # #C5A059 (Dorado)


def create_default_avatar():
    """Crea una imagen de avatar por defecto elegante."""
    size = 400
    img = Image.new("RGB", (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Dibujar un icono de persona estilizado
    center_x, center_y = size // 2, size // 2

    # Cabeza (círculo)
    head_radius = 50
    draw.ellipse(
        [
            center_x - head_radius,
            center_y - 80 - head_radius,
            center_x + head_radius,
            center_y - 80 + head_radius,
        ],
        fill=ICON_COLOR,
    )

    # Cuerpo (arco/semicírculo)
    body_width = 120
    body_height = 80
    draw.ellipse(
        [
            center_x - body_width,
            center_y + 20,
            center_x + body_width,
            center_y + 20 + body_height * 2,
        ],
        fill=ICON_COLOR,
    )

    # Recortar parte inferior del cuerpo con un rectángulo del color de fondo
    draw.rectangle(
        [0, center_y + 20 + body_height, size, size],
        fill=BG_COLOR,
    )

    # Agregar ícono de audio pequeño
    wave_y = center_y + 100
    for i, offset in enumerate([-30, -15, 0, 15, 30]):
        height = 15 + (15 - abs(offset) // 2)
        draw.rectangle(
            [
                center_x + offset - 3,
                wave_y - height,
                center_x + offset + 3,
                wave_y + height,
            ],
            fill=ICON_COLOR,
        )

    # Guardar
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(DEFAULT_AVATAR, "PNG")
    print(f"Avatar creado en: {DEFAULT_AVATAR}")


def create_app_icon():
    """Crea un icono para la ventana de la aplicación."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0)) # Transparente
    draw = ImageDraw.Draw(img)
    
    # Dibujar un círculo dorado de fondo
    draw.ellipse([2, 2, size-2, size-2], fill=ICON_COLOR)
    
    # Dibujar nota musical (dos rectángulos y una elipse)
    # Nota: Simplificado para visualización
    note_color = BG_COLOR
    
    # Cabeza de la nota
    draw.ellipse([15, 35, 35, 50], fill=note_color)
    
    # Plica (palito)
    draw.rectangle([30, 10, 35, 45], fill=note_color)
    
    # Corchete
    draw.polygon([(30, 10), (30, 20), (50, 25), (50, 10)], fill=note_color)
    
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(APP_ICON, "PNG")
    print(f"Icono creado en: {APP_ICON}")


def create_background_texture():
    """Genera una textura sutil para el fondo."""
    texture_path = ASSETS_DIR / "texture.png"
    if texture_path.exists():
        return

    width, height = 1200, 900 # Cover most window sizes
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Patrón de puntos muy sutiles
    for x in range(0, width, 20):
        for y in range(0, height, 20):
            # Color dorado muy tenue (alpha bajo)
            draw.ellipse([x, y, x+2, y+2], fill=(197, 160, 89, 15))
            
    img.save(texture_path, "PNG")
    print(f"Textura creada en: {texture_path}")


def create_plus_icon():
    """Genera un icono de 'Más' (+) para el botón flotante."""
    icon_path = ASSETS_DIR / "plus_icon.png"
    # Siempre regenerar para asegurar calidad
    
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # El botón ya es dorado, así que el icono debe ser negro
    # Dibujar cruz
    thickness = 8
    center = size // 2
    length = 24
    
    # Horizontal
    draw.rectangle(
        [center - length, center - thickness//2, center + length, center + thickness//2],
        fill=(0, 0, 0) # Negro
    )
    # Vertical
    draw.rectangle(
        [center - thickness//2, center - length, center + thickness//2, center + length],
        fill=(0, 0, 0)
    )
    
    img.save(icon_path, "PNG")
    print(f"Icono Plus creado en: {icon_path}")


if __name__ == "__main__":
    create_default_avatar()
    create_app_icon()
    create_background_texture()
    create_plus_icon() # Nuevo
    print("Assets generados correctamente.")
