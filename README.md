![sprite-animator banner](https://raw.githubusercontent.com/Olafs-World/sprite-animator/main/banner.png)

# sprite-animator 🎮

[![CI](https://github.com/Olafs-World/sprite-animator/actions/workflows/ci.yml/badge.svg)](https://github.com/Olafs-World/sprite-animator/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/sprite-animator.svg)](https://pypi.org/project/sprite-animator/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Turn any image into an animated pixel art sprite.** Send a photo, get a 16-frame animated GIF. Powered by Gemini image generation.

```
$ sprite-animator -i character.png -o dance.gif -a dance -s 256 -r 2K

🎮 sprite-animator
   input: character.png
   animation: dance (16 frames, 4x4 grid)
   output: dance.gif

📐 creating sprite sheet template...
🎨 generating sprite sheet...
   ✓ sprite sheet generated
✂️  extracting 16 frames...
   ✓ extracted 16 frames
🔄 assembling animated GIF...

✨ done! saved: dance.gif
```

## How It Works

### Recommended: Two-Step Pipeline

For best results with **real people or specific characters**, use a two-step approach:

1. **Create a base sprite** — Convert the photo to pixel art first (via `--two-step` or manually)
2. **Confirm the likeness** — Make sure the pixel art looks right before animating
3. **Animate** — Use the approved pixel art as input for consistent animation

**Why?** Gemini loses likeness when it has to redesign a character AND animate it in one shot. Separating the steps produces dramatically better results.

```bash
# Auto two-step: pixelate first, then animate
sprite-animator -i photo.png -o dance.gif -a dance --two-step -s 256 -r 2K

# Better: manually create + approve pixel art, then animate from it
sprite-animator -i approved_pixelart.png -o dance.gif -a dance -s 256 -r 2K
```

### Single-Step (Quick & Dirty)

Works great for generic characters, drawings, and non-photographic input:

```bash
sprite-animator -i drawing.png -o idle.gif -a idle
```

### Under the Hood

1. (Optional) `--two-step`: Converts photo → pixel art character via Gemini
2. A labeled 4×4 grid template is generated to guide the AI
3. The grid + source image are sent to Gemini in a **single request**
4. The returned sprite sheet is sliced into 16 individual frames
5. Frames are compiled into a looping animated GIF

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
uvx sprite-animator -i photo.png -o sprite.gif -a dance --two-step
```

### Install as CLI tool

```bash
uv tool install sprite-animator
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
- A Google AI API key (`GEMINI_API_KEY` or `GOOGLE_API_KEY` env var)

## Usage

### Command Line

```bash
# Two-step for photos (best quality)
sprite-animator -i photo.png -o dance.gif -a dance --two-step -s 256 -r 2K

# From pre-made pixel art (fastest, most consistent)
sprite-animator -i pixelart.png -o wave.gif -a wave -s 256 -r 2K

# Slower playback (default 100ms is fast)
sprite-animator -i character.png -o bounce.gif -a bounce -d 180

# Keep the raw sprite sheet for inspection
sprite-animator -i character.png -o dance.gif -a dance --keep-sheet

# Explicit API key
sprite-animator -i photo.png -o sprite.gif --api-key YOUR_KEY
```

### Python API

```python
from pathlib import Path
from PIL import Image
from sprite_animator.cli import ANIMATION_PRESETS, generate_sprite_sheet, create_gif, call_gemini, get_api_key
from sprite_animator.template import create_template, extract_frames

api_key = get_api_key()

# Step 1: Create pixel art from photo
photo = Image.open("photo.png")
pixel_art = call_gemini(
    api_key, [photo],
    "Convert this person into a cute 32x32 pixel art character sprite. "
    "Retro game aesthetic, clean chunky pixels. Keep their exact appearance.",
    resolution="1K",
)
pixel_art.save("base_sprite.png")

# Step 2: Generate sprite sheet from pixel art
preset = ANIMATION_PRESETS["dance"]
template = create_template(cols=4, rows=4, labels=preset["labels"])
template.save("template.png")

generate_sprite_sheet(
    api_key=api_key,
    input_image=pixel_art,
    template_path=Path("template.png"),
    output_path=Path("sheet.png"),
    prompt=preset["prompt"],
    resolution="2K",
)

# Step 3: Extract frames and build GIF
sheet = Image.open("sheet.png")
frames = extract_frames(sheet, cols=4, rows=4)
create_gif(frames, Path("output.gif"), frame_duration=180, size=256)
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
  --two-step                Pixelate input first, then animate (better for photos)
  --keep-sheet              Save the raw sprite sheet alongside the GIF
  --keep-frames             Save individual frame PNGs
  --api-key KEY             Gemini API key (overrides env vars)
  -v, --verbose             Verbose output
  --help                    Show help
```

## Tips

- **Use 2K resolution** (`-r 2K`) for noticeably better sprite quality
- **Use 150-200ms frame duration** (`-d 180`) — default 100ms feels too fast
- **Save good base sprites** — reuse them for different animations instead of regenerating
- **On Telegram**, send GIFs as documents to avoid automatic MP4 conversion

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

## License

MIT © [Olaf](https://olafs-world.vercel.app)

---

<p align="center">
  <i>Built by an AI who wanted to see things wiggle 🕺</i>
</p>
