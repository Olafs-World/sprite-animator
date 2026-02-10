"""Generate sprite sheet templates and parse output sheets into frames."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_template(
    cols: int = 4,
    rows: int = 1,
    cell_size: int = 256,
    labels: list[str] | None = None,
) -> Image.Image:
    """Create a sprite sheet template with labeled grid cells.
    
    Returns a template image with numbered/labeled cells that guides
    the AI model to place each animation frame in the right spot.
    """
    width = cols * cell_size
    height = rows * cell_size
    img = Image.new("RGB", (width, height), (200, 200, 200))
    draw = ImageDraw.Draw(img)

    # Draw grid lines
    for c in range(cols + 1):
        x = c * cell_size
        draw.line([(x, 0), (x, height)], fill=(100, 100, 100), width=3)
    for r in range(rows + 1):
        y = r * cell_size
        draw.line([(0, y), (width, y)], fill=(100, 100, 100), width=3)

    # Label each cell
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if labels and idx < len(labels):
                label = labels[idx]
            else:
                label = f"Frame {idx + 1}"
            
            cx = c * cell_size + cell_size // 2
            cy = r * cell_size + cell_size // 2
            
            # Draw label text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except (OSError, IOError):
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((cx - tw // 2, cy - th // 2), label, fill=(80, 80, 80), font=font)

    return img


def extract_frames(
    sheet: Image.Image,
    cols: int = 4,
    rows: int = 1,
) -> list[Image.Image]:
    """Split a sprite sheet into individual frames based on grid layout."""
    w, h = sheet.size
    cell_w = w // cols
    cell_h = h // rows
    
    frames = []
    for r in range(rows):
        for c in range(cols):
            left = c * cell_w
            top = r * cell_h
            right = left + cell_w
            bottom = top + cell_h
            frame = sheet.crop((left, top, right, bottom))
            frames.append(frame)
    
    return frames


if __name__ == "__main__":
    # Quick test
    labels = ["Stand", "Arm up", "Wave right", "Arm down"]
    tpl = create_template(cols=4, rows=1, labels=labels)
    tpl.save("/tmp/sprite_template_test.png")
    print(f"Template saved: /tmp/sprite_template_test.png ({tpl.size})")
