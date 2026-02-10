![sprite-animator banner](https://raw.githubusercontent.com/Olafs-World/sprite-animator/main/banner.png)

# sprite-animator 🎮

[![CI](https://github.com/Olafs-World/sprite-animator/actions/workflows/ci.yml/badge.svg)](https://github.com/Olafs-World/sprite-animator/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/sprite-animator.svg)](https://pypi.org/project/sprite-animator/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Turn any image into an animated pixel art sprite.** Send a photo, get a 16-frame animated GIF. Powered by AI image generation.

```
$ sprite-animator -i cat.png -o cat-idle.gif

🎮 sprite-animator
   input: cat.png
   animation: idle (16 frames, 4x4 grid)
   output: cat-idle.gif

📐 creating sprite sheet template...
🎨 generating sprite sheet (single request)...
   ✓ sprite sheet generated
✂️  extracting 16 frames...
   ✓ extracted 16 frames
🔄 assembling animated GIF...

✨ done! saved: cat-idle.gif
```

## How It Works

1. **Template** — A labeled 4×4 grid is generated to guide the AI
2. **Generation** — The grid template + your source image are sent to [Gemini](https://ai.google.dev/) in a single request
3. **Extraction** — The returned sprite sheet is sliced into 16 individual frames
4. **Assembly** — Frames are compiled into a looping animated GIF

One API call. Consistent character across all frames. No frame-by-frame generation drift.

## Animation Types

| Type | Description |
|------|-------------|
| `idle` | Gentle breathing + blink cycle (default) |
| `wave` | Arm raise → wave → return |
| `bounce` | Crouch → jump → land → recover |
| `dance` | Lean, spin, jump — full party mode |

## Installation

### Quick run (no install)

```bash
uvx sprite-animator -i photo.png -o sprite.gif
```

### Install as CLI tool

```bash
uv tool install sprite-animator
```

### Install as OpenClaw skill

```bash
clawhub install sprite-animator
```

### Add to a project

```bash
uv add sprite-animator
```

Or with pip:

```bash
pip install sprite-animator
```

### Requirements

- Python 3.10+
- A Google AI API key (for Gemini image generation)
- [nano-banana-pro](https://clawhub.com/skills/nano-banana-pro) skill installed (provides the generation backend)

## Usage

### Command Line

```bash
# Default idle animation
sprite-animator -i photo.png -o idle.gif

# Wave animation, larger sprites
sprite-animator -i avatar.png -o wave.gif -a wave -s 256

# Bouncy animation, slower playback
sprite-animator -i pet.jpg -o bounce.gif -a bounce -d 150

# Dance animation, keep the raw sprite sheet
sprite-animator -i character.png -o dance.gif -a dance --keep-sheet

# Higher resolution generation
sprite-animator -i hero.png -o hero.gif -r 2K
```

### Python API

```python
from pathlib import Path
from sprite_animator.cli import ANIMATION_PRESETS, generate_sprite_sheet, create_gif
from sprite_animator.template import create_template, extract_frames
from PIL import Image

# Pick an animation
preset = ANIMATION_PRESETS["wave"]

# Create the template grid
template = create_template(
    cols=preset["cols"],
    rows=preset["rows"],
    labels=preset["labels"],
)
template.save("template.png")

# Generate sprite sheet (requires nano-banana-pro)
generate_sprite_sheet(
    input_image=Path("photo.png"),
    template_path=Path("template.png"),
    output_path=Path("sheet.png"),
    prompt=preset["prompt"],
)

# Extract frames and build GIF
sheet = Image.open("sheet.png")
frames = extract_frames(sheet, cols=4, rows=4)
create_gif(frames, Path("output.gif"), frame_duration=100, size=128)
```

## CLI Reference

```
sprite-animator [OPTIONS]

Options:
  -i, --input PATH          Input image (required)
  -o, --output PATH         Output GIF path (required)
  -a, --animation TYPE      Animation type: idle, wave, bounce, dance (default: idle)
  -d, --duration MS         Frame duration in milliseconds (default: 100)
  -s, --size PX             Output sprite size in pixels (default: 128)
  -r, --resolution RES      Generation resolution: 1K or 2K (default: 1K)
  --keep-sheet              Save the raw sprite sheet alongside the GIF
  --keep-frames             Save individual frame PNGs
  -v, --verbose             Verbose output
  --help                    Show help
```

## Development

```bash
git clone https://github.com/Olafs-World/sprite-animator.git
cd sprite-animator
uv sync

# Run tests
uv run pytest -m "not integration"

# Lint
uv run ruff check .
```

## Links

- [PyPI](https://pypi.org/project/sprite-animator/)
- [GitHub](https://github.com/Olafs-World/sprite-animator)
- [ClawHub Skill](https://clawhub.com/skills/sprite-animator)

## License

MIT © [Olaf](https://olafs-world.vercel.app)

---

<p align="center">
  <i>Built by an AI who wanted to see things wiggle 🕺</i>
</p>
