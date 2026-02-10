#!/usr/bin/env python3
"""
Sprite Animator CLI - Generate animated pixel art sprites from any image.

Uses a template-based sprite sheet approach: sends a grid template + source image
to Gemini in a SINGLE request, then splits the result into frames for a GIF.
This ensures visual consistency across all animation frames.
"""

import argparse
import base64
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path

from sprite_animator.template import create_template, extract_frames

# Animation presets: (labels, prompt_suffix)
ANIMATION_PRESETS = {
    "idle": {
        "cols": 4, "rows": 4,
        "labels": [
            "1:stand", "2:breathe↑", "3:breathe↑↑", "4:breathe↑",
            "5:stand", "6:blink¼", "7:blink½", "8:blink¾",
            "9:eyes shut", "10:blink¾", "11:blink½", "12:blink¼",
            "13:stand", "14:breathe↓", "15:breathe↓↓", "16:breathe↓",
        ],
        "prompt": (
            "Fill this 4x4 sprite sheet grid (16 cells, read left-to-right, top-to-bottom) "
            "with a cute pixel art version of the character from the reference image. "
            "32x32 pixel art style, retro game aesthetic, clean chunky pixels. "
            "This is an IDLE animation loop with smooth transitions. Each cell is one frame: "
            "Row 1: standing → gentle breathe up (body rises 1px each frame) → back to center. "
            "Row 2: standing → slow eye blink (eyes gradually close over 4 frames). "
            "Row 3: eyes fully shut → slow eye open (eyes gradually open over 4 frames). "
            "Row 4: standing → gentle breathe down (body lowers 1px each frame) → back to center. "
            "CRITICAL: Keep the character IDENTICAL across all 16 frames — same colors, proportions, "
            "size, position. Only the specified micro-movement should change. "
            "Solid flat color background (same in all cells)."
        ),
    },
    "wave": {
        "cols": 4, "rows": 4,
        "labels": [
            "1:stand", "2:arm↑¼", "3:arm↑½", "4:arm↑¾",
            "5:arm up", "6:wave R", "7:wave L", "8:wave R",
            "9:wave L", "10:wave R", "11:arm↓¾", "12:arm↓½",
            "13:arm↓¼", "14:stand", "15:smile", "16:stand",
        ],
        "prompt": (
            "Fill this 4x4 sprite sheet grid (16 cells, read left-to-right, top-to-bottom) "
            "with a cute pixel art version of the character from the reference image. "
            "32x32 pixel art style, retro game aesthetic, clean chunky pixels. "
            "This is a WAVE animation loop with smooth transitions. Each cell is one frame: "
            "Row 1: standing still → arm gradually raising up (4 incremental positions). "
            "Row 2: arm fully up → waving side to side (arm tilts right, left, right). "
            "Row 3: still waving (left, right) → arm gradually lowering (2 frames). "
            "Row 4: arm coming down → back to standing → happy smile → standing. "
            "CRITICAL: Keep the character IDENTICAL across all 16 frames — same colors, proportions, "
            "size, position. Only the arm position and expression should change. "
            "Solid flat color background (same in all cells)."
        ),
    },
    "bounce": {
        "cols": 4, "rows": 4,
        "labels": [
            "1:stand", "2:crouch¼", "3:crouch½", "4:crouch full",
            "5:launch", "6:rise", "7:peak", "8:peak+happy",
            "9:fall start", "10:falling", "11:land", "12:squish",
            "13:recover¼", "14:recover½", "15:recover¾", "16:stand",
        ],
        "prompt": (
            "Fill this 4x4 sprite sheet grid (16 cells, read left-to-right, top-to-bottom) "
            "with a cute pixel art version of the character from the reference image. "
            "32x32 pixel art style, retro game aesthetic, clean chunky pixels. "
            "This is a BOUNCE animation loop with smooth transitions. Each cell is one frame: "
            "Row 1: standing → gradually crouching down (getting squished/compressed). "
            "Row 2: launching upward → rising → at peak of jump (stretched tall) → happy face at peak. "
            "Row 3: starting to fall → falling fast → landing impact → squished on landing. "
            "Row 4: gradually recovering from squish back to standing position. "
            "CRITICAL: Keep the character IDENTICAL across all 16 frames — same colors, proportions. "
            "Only the vertical position and squish/stretch should change. "
            "Solid flat color background (same in all cells)."
        ),
    },
    "dance": {
        "cols": 4, "rows": 4,
        "labels": [
            "1:center", "2:lean L", "3:arms L", "4:lean L+",
            "5:center", "6:lean R", "7:arms R", "8:lean R+",
            "9:center", "10:arms up", "11:spin¼", "12:spin½",
            "13:spin¾", "14:arms up", "15:jump", "16:land",
        ],
        "prompt": (
            "Fill this 4x4 sprite sheet grid (16 cells, read left-to-right, top-to-bottom) "
            "with a cute pixel art version of the character from the reference image. "
            "32x32 pixel art style, retro game aesthetic, clean chunky pixels. "
            "This is a fun DANCE animation loop with smooth transitions. Each cell is one frame: "
            "Row 1: center pose → leaning left → arms out left → full left lean. "
            "Row 2: back to center → leaning right → arms out right → full right lean. "
            "Row 3: center → arms up high → spinning (4 rotation frames). "
            "Row 4: finish spin → arms up → jump → land back in center. "
            "CRITICAL: Keep the character IDENTICAL across all 16 frames — same colors, proportions. "
            "Only the pose/position should change. Make it look fun and energetic! "
            "Solid flat color background (same in all cells)."
        ),
    },
}

PIXELATE_PROMPT = (
    "Convert this person into a cute 32x32 pixel art character sprite. "
    "Retro game aesthetic, clean chunky pixels. Keep their exact appearance: "
    "skin tone, hair style, facial hair, clothing colors and style. "
    "Full body, standing pose, centered on a solid flat color background."
)


def get_api_key(provided_key: str | None = None) -> str:
    """Get Gemini API key from argument, GOOGLE_API_KEY, or GEMINI_API_KEY."""
    if provided_key:
        return provided_key
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        print(
            "Error: No API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY env var, "
            "or pass --api-key.",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)
    return key


def call_gemini(
    api_key: str,
    images: list,
    prompt: str,
    resolution: str = "1K",
) -> "PILImage":
    """Call Gemini image generation and return a PIL Image."""
    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=api_key)

    contents = [*images, prompt]

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(image_size=resolution),
        ),
    )

    for part in response.parts:
        if part.text is not None:
            print(f"   model: {part.text}", flush=True)
        elif part.inline_data is not None:
            image_data = part.inline_data.data
            if isinstance(image_data, str):
                image_data = base64.b64decode(image_data)
            return PILImage.open(BytesIO(image_data))

    raise RuntimeError("Gemini returned no image data")


def generate_sprite_sheet(
    api_key: str,
    input_image: "PILImage",
    template_path: Path,
    output_path: Path,
    prompt: str,
    resolution: str = "1K",
) -> bool:
    """Generate a sprite sheet using Gemini with template + reference image."""
    from PIL import Image as PILImage

    try:
        template_img = PILImage.open(template_path)
        result = call_gemini(api_key, [template_img, input_image], prompt, resolution)

        # Save as PNG
        if result.mode == "RGBA":
            rgb = PILImage.new("RGB", result.size, (255, 255, 255))
            rgb.paste(result, mask=result.split()[3])
            rgb.save(str(output_path), "PNG")
        else:
            result.convert("RGB").save(str(output_path), "PNG")

        return True
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr, flush=True)
        return False


def create_gif(
    frames: list,
    output_path: Path,
    frame_duration: int = 200,
    size: int | None = None,
) -> bool:
    """Assemble PIL Image frames into an animated GIF."""
    from PIL import Image

    try:
        processed = []
        for frame in frames:
            if size:
                frame = frame.resize((size, size), Image.Resampling.NEAREST)
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            bg = Image.new("RGBA", frame.size, (255, 255, 255, 255))
            composite = Image.alpha_composite(bg, frame)
            processed.append(composite.convert("P", palette=Image.Palette.ADAPTIVE))

        if not processed:
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        processed[0].save(
            output_path,
            save_all=True,
            append_images=processed[1:],
            duration=frame_duration,
            loop=0,
            optimize=True,
        )
        return True
    except Exception as e:
        print(f"Error creating GIF: {e}", file=sys.stderr, flush=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate animated pixel art sprites from any image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sprite-animator -i photo.png -o sprite.gif
  sprite-animator -i avatar.png -o wave.gif -a wave
  sprite-animator -i pet.jpg -o bounce.gif -a bounce -s 256
  sprite-animator -i photo.png -o dance.gif -a dance --two-step
        """,
    )

    parser.add_argument("-i", "--input", required=True, type=Path, help="Input image")
    parser.add_argument("-o", "--output", required=True, type=Path, help="Output GIF path")
    parser.add_argument("-a", "--animation", choices=list(ANIMATION_PRESETS.keys()), default="idle", help="Animation type (default: idle)")
    parser.add_argument("-d", "--duration", type=int, default=100, help="Frame duration in ms (default: 100)")
    parser.add_argument("-s", "--size", type=int, default=128, help="Output sprite size in px (default: 128)")
    parser.add_argument("-r", "--resolution", choices=["1K", "2K"], default="1K", help="Generation resolution")
    parser.add_argument("--two-step", action="store_true", help="First pixelate the input, then animate (better likeness for photos)")
    parser.add_argument("--keep-sheet", action="store_true", help="Keep the raw sprite sheet")
    parser.add_argument("--keep-frames", action="store_true", help="Keep individual frame files")
    parser.add_argument("--api-key", help="Gemini API key (overrides env vars)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr, flush=True)
        sys.exit(1)

    api_key = get_api_key(args.api_key)

    from PIL import Image as PILImage

    preset = ANIMATION_PRESETS[args.animation]
    cols = preset["cols"]
    rows = preset["rows"]
    total_frames = cols * rows

    print(f"🎮 sprite-animator", flush=True)
    print(f"   input: {args.input}", flush=True)
    print(f"   animation: {args.animation} ({total_frames} frames, {cols}x{rows} grid)", flush=True)
    if args.two_step:
        print(f"   mode: two-step (pixelate → animate)", flush=True)
    print(f"   output: {args.output}", flush=True)

    # Load input image
    input_img = PILImage.open(args.input)

    # Optional two-step: pixelate first for better likeness
    if args.two_step:
        print(f"\n🎨 step 1: pixelating input image...", flush=True)
        try:
            pixel_img = call_gemini(api_key, [input_img], PIXELATE_PROMPT, "1K")
            input_img = pixel_img
            print(f"   ✓ pixelated version created", flush=True)

            # Optionally save the pixelated version
            pixel_out = args.output.parent / f"{args.output.stem}_pixel.png"
            if pixel_img.mode == "RGBA":
                rgb = PILImage.new("RGB", pixel_img.size, (255, 255, 255))
                rgb.paste(pixel_img, mask=pixel_img.split()[3])
                rgb.save(str(pixel_out), "PNG")
            else:
                pixel_img.convert("RGB").save(str(pixel_out), "PNG")
            print(f"   saved: {pixel_out}", flush=True)
        except Exception as e:
            print(f"   ⚠️  pixelation failed ({e}), falling back to original image", flush=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create template
        step = "2" if args.two_step else "1"
        print(f"\n📐 step {step}: creating sprite sheet template...", flush=True)
        template_img = create_template(cols=cols, rows=rows, labels=preset["labels"])
        template_path = tmpdir / "template.png"
        template_img.save(template_path)
        if args.verbose:
            print(f"   template: {template_img.size}", flush=True)

        # Generate sprite sheet
        print(f"🎨 generating sprite sheet...", flush=True)
        sheet_path = tmpdir / "sprite_sheet.png"

        success = generate_sprite_sheet(
            api_key,
            input_img,
            template_path,
            sheet_path,
            preset["prompt"],
            args.resolution,
        )

        if not success:
            print("❌ failed to generate sprite sheet", file=sys.stderr, flush=True)
            sys.exit(1)

        print(f"   ✓ sprite sheet generated", flush=True)

        # Extract frames
        print(f"✂️  extracting {total_frames} frames...", flush=True)
        sheet = PILImage.open(sheet_path)
        if args.verbose:
            print(f"   sheet size: {sheet.size}", flush=True)

        frames = extract_frames(sheet, cols=cols, rows=rows)
        print(f"   ✓ extracted {len(frames)} frames", flush=True)

        # Assemble GIF
        print(f"🔄 assembling animated GIF...", flush=True)
        success = create_gif(frames, args.output, frame_duration=args.duration, size=args.size)

        if not success:
            print("❌ failed to create GIF", file=sys.stderr, flush=True)
            sys.exit(1)

        print(f"\n✨ done! saved: {args.output.resolve()}", flush=True)

        # Optionally save sheet and frames
        if args.keep_sheet:
            sheet_out = args.output.parent / f"{args.output.stem}_sheet.png"
            import shutil
            shutil.copy2(sheet_path, sheet_out)
            print(f"   sheet: {sheet_out}", flush=True)

        if args.keep_frames:
            frames_dir = args.output.parent / f"{args.output.stem}_frames"
            frames_dir.mkdir(exist_ok=True)
            for idx, frame in enumerate(frames):
                frame.save(frames_dir / f"frame_{idx:02d}.png")
            print(f"   frames: {frames_dir}/", flush=True)


if __name__ == "__main__":
    main()
