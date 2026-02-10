#!/usr/bin/env python3
"""
Sprite Animator CLI - Generate animated pixel art sprites from any image.

Uses nano-banana-pro (Gemini image gen) to create pixel art frames,
then assembles them into an animated GIF.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# nano-banana-pro script path
NANO_BANANA_SCRIPT = Path(
    "/home/ec2-user/.npm-global/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/generate_image.py"
)

# Animation frame prompts for idle animation (subtle movements)
IDLE_FRAME_PROMPTS = [
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, standing still with arms at sides. Retro game aesthetic, clean pixels, transparent or solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, slight breathing motion with body raised 1 pixel. Retro game aesthetic, clean pixels, transparent or solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, eyes blinking (half closed). Retro game aesthetic, clean pixels, transparent or solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, slight breathing motion with body lowered 1 pixel. Retro game aesthetic, clean pixels, transparent or solid color background. Keep the character's key features and colors.",
]

# Wave animation prompts
WAVE_FRAME_PROMPTS = [
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, one arm raised to wave (position 1 - arm starting to go up). Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, one arm raised high waving (position 2 - arm fully up). Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, one arm waving to the side (position 3 - arm tilted). Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, facing forward, one arm coming back down (position 4 - arm lowering). Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
]

# Bounce animation prompts
BOUNCE_FRAME_PROMPTS = [
    "Transform this character into a cute pixel art sprite, 32x32 style, character at normal height, happy expression. Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, character squishing down (compressed, wider). Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, character jumping up high, stretched vertically. Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, character at peak of jump, happy/excited expression. Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, character coming down from jump. Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
    "Transform this character into a cute pixel art sprite, 32x32 style, character landing, slightly squished. Retro game aesthetic, clean pixels, solid color background. Keep the character's key features and colors.",
]

ANIMATION_PRESETS = {
    "idle": IDLE_FRAME_PROMPTS,
    "wave": WAVE_FRAME_PROMPTS,
    "bounce": BOUNCE_FRAME_PROMPTS,
}


def generate_frame(
    input_image: Path,
    output_path: Path,
    prompt: str,
    resolution: str = "1K",
) -> bool:
    """Generate a single sprite frame using nano-banana-pro."""
    cmd = [
        "uv", "run", str(NANO_BANANA_SCRIPT),
        "--prompt", prompt,
        "--filename", str(output_path),
        "-i", str(input_image),
        "--resolution", resolution,
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout per frame
        )
        
        if result.returncode != 0:
            print(f"  Error generating frame: {result.stderr}", file=sys.stderr)
            return False
            
        if not output_path.exists():
            print(f"  Frame not created: {output_path}", file=sys.stderr)
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        print(f"  Timeout generating frame", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Exception generating frame: {e}", file=sys.stderr)
        return False


def create_gif(
    frame_paths: list[Path],
    output_path: Path,
    frame_duration: int = 200,
    loop: int = 0,
    resize: Optional[tuple[int, int]] = None,
) -> bool:
    """Assemble frames into an animated GIF."""
    try:
        from PIL import Image
        
        frames = []
        for fp in frame_paths:
            img = Image.open(fp)
            
            # Resize if requested
            if resize:
                img = img.resize(resize, Image.Resampling.NEAREST)  # Nearest for pixel art
            
            # Convert to RGBA for consistency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            frames.append(img)
        
        if not frames:
            print("No frames to assemble", file=sys.stderr)
            return False
        
        # Save as GIF
        # Convert RGBA to P mode with transparency for GIF
        gif_frames = []
        for frame in frames:
            # Create a copy with white background for GIF compatibility
            bg = Image.new('RGBA', frame.size, (255, 255, 255, 255))
            composite = Image.alpha_composite(bg, frame)
            gif_frames.append(composite.convert('P', palette=Image.Palette.ADAPTIVE))
        
        gif_frames[0].save(
            output_path,
            save_all=True,
            append_images=gif_frames[1:],
            duration=frame_duration,
            loop=loop,
            optimize=True,
        )
        
        return True
        
    except Exception as e:
        print(f"Error creating GIF: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate animated pixel art sprites from any image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sprite-animator -i photo.png -o sprite.gif
  sprite-animator -i avatar.png -o wave.gif --animation wave
  sprite-animator -i pet.jpg -o bounce.gif --animation bounce --frames 6
        """,
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        type=Path,
        help="Input image (photo, drawing, etc.)",
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        type=Path,
        help="Output GIF path",
    )
    
    parser.add_argument(
        "-a", "--animation",
        choices=list(ANIMATION_PRESETS.keys()),
        default="idle",
        help="Animation type (default: idle)",
    )
    
    parser.add_argument(
        "-f", "--frames",
        type=int,
        default=4,
        help="Number of frames to generate (default: 4)",
    )
    
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=200,
        help="Frame duration in ms (default: 200)",
    )
    
    parser.add_argument(
        "-s", "--size",
        type=int,
        default=128,
        help="Output sprite size in pixels (default: 128)",
    )
    
    parser.add_argument(
        "-r", "--resolution",
        choices=["1K", "2K"],
        default="1K",
        help="Generation resolution (default: 1K)",
    )
    
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Keep individual frame files",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    if not NANO_BANANA_SCRIPT.exists():
        print(f"Error: nano-banana-pro script not found: {NANO_BANANA_SCRIPT}", file=sys.stderr)
        sys.exit(1)
    
    # Get prompts for animation type
    prompts = ANIMATION_PRESETS[args.animation]
    
    # Adjust frame count
    num_frames = min(args.frames, len(prompts))
    if args.frames > len(prompts):
        print(f"Note: {args.animation} animation has {len(prompts)} frames, using all of them")
    
    prompts = prompts[:num_frames]
    
    print(f"Generating {num_frames}-frame {args.animation} animation...")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    
    # Create temp directory for frames
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        frame_paths = []
        
        for i, prompt in enumerate(prompts):
            frame_path = tmpdir / f"frame_{i:02d}.png"
            print(f"Generating frame {i+1}/{num_frames}...")
            
            if args.verbose:
                print(f"  Prompt: {prompt[:80]}...")
            
            success = generate_frame(
                args.input,
                frame_path,
                prompt,
                args.resolution,
            )
            
            if success:
                frame_paths.append(frame_path)
                print(f"  ✓ Frame {i+1} generated")
            else:
                print(f"  ✗ Frame {i+1} failed, skipping")
        
        if len(frame_paths) < 2:
            print(f"Error: Only {len(frame_paths)} frames generated, need at least 2", file=sys.stderr)
            sys.exit(1)
        
        print(f"\nAssembling {len(frame_paths)} frames into GIF...")
        
        # Create output directory if needed
        args.output.parent.mkdir(parents=True, exist_ok=True)
        
        success = create_gif(
            frame_paths,
            args.output,
            frame_duration=args.duration,
            resize=(args.size, args.size),
        )
        
        if success:
            print(f"✓ Animation saved: {args.output.resolve()}")
            
            # Copy frames if requested
            if args.keep_frames:
                frames_dir = args.output.parent / f"{args.output.stem}_frames"
                frames_dir.mkdir(exist_ok=True)
                from shutil import copy2
                for fp in frame_paths:
                    copy2(fp, frames_dir / fp.name)
                print(f"  Frames saved to: {frames_dir}")
        else:
            print("Error: Failed to create GIF", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
