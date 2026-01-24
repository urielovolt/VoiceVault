# VoiceVault

**Álbum de Recuerdos Sonoros** - Una aplicación de escritorio para guardar y organizar memorias de voz con fotos, categorías y funciones de reproducción.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Descripción

VoiceVault te permite capturar y preservar recuerdos sonoros importantes: la voz de un ser querido, un momento especial, o cualquier audio que quieras conservar para siempre. Cada recuerdo puede incluir una foto, título, descripción y categoría para mantenerlos organizados.

## Características

- **Grabar y guardar** memorias de audio con fotos personalizadas
- **Organizar por categorías**: Familia, Amigos, Favoritos, Especiales
- **Buscar y ordenar** recuerdos por nombre, fecha o categoría
- **Modo playlist** para reproducción continua
- **Importar/Exportar** backups en formato ZIP
- **Atajos de teclado** para acceso rápido
- **Indicador visual** de audio en reproducción (borde dorado)
- **Animaciones hover** en las tarjetas de recuerdos
- **Duración del audio** visible en cada tarjeta
- **Doble clic** para reproducir directamente

## Capturas de Pantalla

<p align="center">
  <img src="assets/LogoVoiceVault.png" alt="VoiceVault Logo" width="200">
</p>

## Requisitos

- Python 3.8 o superior
- Windows / macOS / Linux

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/urielovolt/VoiceVault.git
cd VoiceVault
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:
```bash
python main.py
```

## Dependencias

- `customtkinter` - Interfaz gráfica moderna
- `pygame` - Reproducción de audio
- `Pillow` - Manipulación de imágenes
- `mutagen` - Lectura de metadatos de audio
- `soundfile` - Procesamiento de audio
- `numpy` - Operaciones numéricas
- `sounddevice` - Grabación de audio

## Uso

### Crear un nuevo recuerdo
1. Haz clic en el botón **+** en la esquina inferior derecha
2. Completa el título y descripción
3. Selecciona una categoría
4. Graba un audio o selecciona un archivo existente
5. Opcionalmente, añade una foto
6. Guarda el recuerdo

### Atajos de teclado
| Atajo | Acción |
|-------|--------|
| `Ctrl + N` | Nuevo recuerdo |
| `Ctrl + F` | Buscar |
| `Ctrl + E` | Exportar backup |
| `Ctrl + I` | Importar backup |
| `Espacio` | Pausar/Reanudar reproducción |
| `Escape` | Detener reproducción |

### Backup
- **Exportar**: Crea un archivo ZIP con todos tus recuerdos (audio, fotos y datos)
- **Importar**: Restaura recuerdos desde un backup. Los duplicados se detectan automáticamente y se omiten

## Estructura del Proyecto

```
VoiceVault/
├── main.py              # Aplicación principal
├── audio_utils.py       # Utilidades de audio
├── requirements.txt     # Dependencias
├── assets/              # Recursos gráficos
│   ├── Categorias/      # Iconos de categorías
│   └── ...
└── data/                # Datos de usuario (no incluido en repo)
    ├── memories.json    # Base de datos de recuerdos
    ├── photos/          # Fotos de recuerdos
    └── audio/           # Archivos de audio
```

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcion`)
3. Commit tus cambios (`git commit -m 'Añadir nueva función'`)
4. Push a la rama (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Autor

Creado por [@urielovolt](https://github.com/urielovolt)

---

<p align="center">
  Hecho con amor para preservar los recuerdos que importan
</p>
