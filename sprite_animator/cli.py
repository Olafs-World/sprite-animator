#!/usr/bin/env python3
"""
Sprite Animator CLI - Generate animated pixel art sprites from any image.

Uses a template-based sprite sheet approach: sends a grid template + source image
to nano-banana-pro in a SINGLE request, then splits the result into frames for a GIF.
This ensures visual consistency across all animation frames.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from sprite_animator.template import create_template, extract_frames

# nano-banana-pro script path
NANO_BANANA_SCRIPT = Path(
    "/home/ec2-user/.npm-global/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/generate_image.py"
)

# Animation presets: (labels, prompt_suffix)
ANIMATION_PRESETS = {
    "idle": {
        "labels": ["Normal", "Breathe in", "Blink", "Breathe out"],
        "prompt": (
            "Fill each cell of this 4-panel sprite sheet grid with a cute pixel art version "
            "of the character from the reference image. 32x32 pixel art style, retro game aesthetic, "
            "clean chunky pixels. Each cell should show a DIFFERENT frame of a subtle idle animation: "
            "Panel 1 (Normal): standing still. "
            "Panel 2 (Breathe in): body raised slightly. "
            "Panel 3 (Blink): eyes half-closed/blinking. "
            "Panel 4 (Breathe out): body lowered slightly. "
            "Keep the character's colors, features, and proportions IDENTICAL across all 4 panels. "
            "Only the specified body part should change between frames. "
            "Solid flat color background (same in all panels). Keep the grid lines visible."
        ),
    },
    "wave": {
        "labels": ["Stand", "Arm up", "Wave right", "Arm down"],
        "prompt": (
            "Fill each cell of this 4-panel sprite sheet grid with a cute pixel art version "
            "of the character from the reference image. 32x32 pixel art style, retro game aesthetic, "
            "clean chunky pixels. Each cell should show a DIFFERENT frame of a waving animation: "
            "Panel 1 (Stand): standing with arms at sides. "
            "Panel 2 (Arm up): one arm/paw raised up to wave. "
            "Panel 3 (Wave right): arm waving to the right. "
            "Panel 4 (Arm down): arm coming back down. "
            "Keep the character's colors, features, and proportions IDENTICAL across all 4 panels. "
            "Only the arm position should change between frames. "
            "Solid flat color background (same in all panels). Keep the grid lines visible."
        ),
    },
    "bounce": {
        "labels": ["Stand", "Crouch", "Jump", "Fall"],
        "prompt": (
            "Fill each cell of this 4-panel sprite sheet grid with a cute pixel art version "
            "of the character from the reference image. 32x32 pixel art style, retro game aesthetic, "
            "clean chunky pixels. Each cell should show a DIFFERENT frame of a bouncing animation: "
            "Panel 1 (Stand): standing normally. "
            "Panel 2 (Crouch): squished down, preparing to jump. "
            "Panel 3 (Jump): at peak of jump, stretched tall, feet off ground. "
            "Panel 4 (Fall): coming back down. "
            "Keep the character's colors, features, and proportions IDENTICAL across all 4 panels. "
            "Only the vertical position and squish should change between frames. "
            "Solid flat color background (same in all panels). Keep the grid lines visible."
        ),
    },
    "dance": {
        "labels": ["Pose 1", "Pose 2", "Pose 3", "Pose 4"],
        "prompt": (
            "Fill each cell of this 4-panel sprite sheet grid with a cute pixel art version "
            "of the character from the reference image. 32x32 pixel art style, retro game aesthetic, "
            "clean chunky pixels. Each cell should show a DIFFERENT frame of a fun dance animation: "
            "Panel 1: leaning left with arms out. "
            "Panel 2: centered with arms up. "
            "Panel 3: leaning right with arms out. "
            "Panel 4: centered with one arm on hip. "
            "Keep the character's colors, features, and proportions IDENTICAL across all 4 panels. "
            "Solid flat color background (same in all panels). Keep the grid lines visible."
        ),
    },
}


def generate_sprite_sheet(
    input_image: Path,
    template_path: Path,
    output_path: Path,
    prompt: str,
    resolution: str = "1K",
) -> bool:
    """Generate a sprite sheet using nano-banana-pro with template + reference image."""
    cmd = [
        "uv", "run", str(NANO_BANANA_SCRIPT),
        "--prompt", prompt,
        "--filename", str(output_path),
        "-i", str(template_path),
        "-i", str(input_image),
        "--resolution", resolution,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            print(f"  Error: {result.stderr.strip()}", file=sys.stderr, flush=True)
            return False

        if not output_path.exists():
            print(f"  Sheet not created: {output_path}", file=sys.stderr, flush=True)
            return False

        return True

    except subprocess.TimeoutExpired:
        print("  Timeout generating sprite sheet", file=sys.stderr, flush=True)
        return False
    except Exception as e:
        print(f"  Exception: {e}", file=sys.stderr, flush=True)
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
        """,
    )

    parser.add_argument("-i", "--input", required=True, type=Path, help="Input image")
    parser.add_argument("-o", "--output", required=True, type=Path, help="Output GIF path")
    parser.add_argument("-a", "--animation", choices=list(ANIMATION_PRESETS.keys()), default="idle", help="Animation type (default: idle)")
    parser.add_argument("-d", "--duration", type=int, default=200, help="Frame duration in ms (default: 200)")
    parser.add_argument("-s", "--size", type=int, default=128, help="Output sprite size in px (default: 128)")
    parser.add_argument("-r", "--resolution", choices=["1K", "2K"], default="1K", help="Generation resolution")
    parser.add_argument("--keep-sheet", action="store_true", help="Keep the raw sprite sheet")
    parser.add_argument("--keep-frames", action="store_true", help="Keep individual frame files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr, flush=True)
        sys.exit(1)

    if not NANO_BANANA_SCRIPT.exists():
        print(f"Error: nano-banana-pro not found: {NANO_BANANA_SCRIPT}", file=sys.stderr, flush=True)
        sys.exit(1)

    preset = ANIMATION_PRESETS[args.animation]
    cols = len(preset["labels"])

    print(f"🎮 sprite-animator", flush=True)
    print(f"   input: {args.input}", flush=True)
    print(f"   animation: {args.animation} ({cols} frames)", flush=True)
    print(f"   output: {args.output}", flush=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Create template
        print(f"\n📐 creating sprite sheet template...", flush=True)
        template_img = create_template(cols=cols, rows=1, labels=preset["labels"])
        template_path = tmpdir / "template.png"
        template_img.save(template_path)
        if args.verbose:
            print(f"   template: {template_img.size}", flush=True)

        # Step 2: Generate sprite sheet (single request!)
        print(f"🎨 generating sprite sheet (single request)...", flush=True)
        sheet_path = tmpdir / "sprite_sheet.png"

        success = generate_sprite_sheet(
            args.input,
            template_path,
            sheet_path,
            preset["prompt"],
            args.resolution,
        )

        if not success:
            print("❌ failed to generate sprite sheet", file=sys.stderr, flush=True)
            sys.exit(1)

        print(f"   ✓ sprite sheet generated", flush=True)

        # Step 3: Extract frames
        print(f"✂️  extracting {cols} frames...", flush=True)
        from PIL import Image
        sheet = Image.open(sheet_path)
        if args.verbose:
            print(f"   sheet size: {sheet.size}", flush=True)

        # Auto-detect grid layout — model might return 2x2 instead of 4x1
        w, h = sheet.size
        if w == h and cols == 4:
            # Square image = likely 2x2 grid
            grid_cols, grid_rows = 2, 2
            if args.verbose:
                print(f"   detected 2x2 grid layout", flush=True)
        else:
            grid_cols, grid_rows = cols, 1
        frames = extract_frames(sheet, cols=grid_cols, rows=grid_rows)
        print(f"   ✓ extracted {len(frames)} frames", flush=True)

        # Step 4: Assemble GIF
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
