#!/usr/bin/env python3
# Generate favicon assets from a source image with simple posterization.
#
# Outputs:
#   - favicon.ico (multi-size 16, 32, 48, 64) at project root
#   - images/favicon.png (32x32 PNG) if images/ exists, otherwise next to ICO
#   - apple-touch-icon.png (180x180 PNG) at project root
#   - images/android-chrome-192x192.png and images/android-chrome-512x512.png
#     if images/ exists, otherwise at project root

import argparse
from pathlib import Path
from typing import List

from PIL import Image, ImageOps, ImagePalette


def posterize(img: Image.Image, bits: int = 4) -> Image.Image:
    """Reduce color depth to `bits` per channel and slightly boost contrast."""
    # Convert to RGB to avoid mode issues, then posterize
    img = img.convert("RGB")
    img = ImageOps.posterize(img, bits)
    # Optional mild autocontrast for better small-size clarity
    img = ImageOps.autocontrast(img, cutoff=1)
    return img


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _build_palette(colors_hex: list[str]) -> Image.Image:
    """Create a Pillow 'P' image carrying the desired palette (max 256)."""
    rgbs = [_hex_to_rgb(c) for c in colors_hex]
    if len(rgbs) == 0:
        raise ValueError("Palette must include at least one color")
    # Flatten and pad to 256 entries
    flat = []
    for r, g, b in rgbs:
        flat.extend([r, g, b])
    # Repeat last color to fill remaining slots
    last = flat[-3:]
    while len(flat) < 256 * 3:
        flat.extend(last)
    pal_img = Image.new('P', (1, 1))
    pal_img.putpalette(flat[:256*3])
    return pal_img


def reduce_colors(img: Image.Image, colors: int = 4, dither: bool = False,
                  palette_hex: list[str] | None = None) -> Image.Image:
    """Reduce to a fixed palette size.

    - If `palette_hex` provided, quantize to that exact palette.
    - Else, use median-cut to `colors` colors.
    """
    img = img.convert("RGB")
    d = Image.FLOYDSTEINBERG if dither else Image.NONE
    if palette_hex:
        pal_img = _build_palette(palette_hex)
        # Quantize using the custom palette
        q = img.quantize(palette=pal_img, dither=d)
        return q.convert("RGB")
    # Fallback: MEDIANCUT
    return img.quantize(colors=max(2, colors), method=Image.MEDIANCUT, dither=d).convert("RGB")


def fit_square(img: Image.Image, size: int, bg=(255, 255, 255)) -> Image.Image:
    """Center-fit the image into a square canvas of `size` x `size`."""
    img = img.convert("RGBA")
    canvas = Image.new("RGBA", (size, size), (*bg, 0))
    # Preserve aspect ratio
    img.thumbnail((size, size), Image.LANCZOS)
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.paste(img, (x, y), img)
    return canvas.convert("RGBA")


def save_ico(img: Image.Image, sizes: List[int], out_path: Path):
    imgs = [fit_square(img, s) for s in sizes]
    # Save as multi-resolution ICO
    # Pillow uses the first image as base; provide sizes via `sizes` arg.
    base = imgs[0].convert("RGBA")
    base.save(out_path, format="ICO", sizes=[(s, s) for s in sizes])


def main():
    parser = argparse.ArgumentParser(description="Generate favicon from source image")
    parser.add_argument("source", type=Path, help="Path to source image (png/jpg/svg*)")
    parser.add_argument("--bits", type=int, default=4, help="Bits per channel for posterize (1-8)")
    parser.add_argument("--sizes", type=int, nargs="*", default=[16, 32, 48, 64], help="ICO sizes")
    parser.add_argument("--png-size", type=int, default=32, help="PNG size for images/favicon.png")
    parser.add_argument("--apple-size", type=int, default=180, help="PNG size for apple-touch-icon.png")
    parser.add_argument("--android-sizes", type=int, nargs="*", default=[192, 512], help="Android Chrome PNG sizes")
    parser.add_argument("--colors", type=int, default=4, help="Palette colors after posterize (e.g., 4)")
    parser.add_argument("--dither", action="store_true", help="Enable dithering during color quantization")
    parser.add_argument("--palette", type=str, default="",
                        help="Comma-separated hex colors (e.g. #0F62FE,#12B886,#FF7A59,#FFD166)")
    parser.add_argument("--palette-preset", type=str, default="vibrant",
                        choices=["vibrant", "pastel", "mono"],
                        help="Preset palette if --palette not provided")
    args = parser.parse_args()

    src: Path = args.source
    if not src.exists():
        raise SystemExit(f"Source does not exist: {src}")

    # Load and process
    img = Image.open(src)
    img = posterize(img, bits=max(1, min(8, args.bits)))
    palette_hex: list[str] | None = None
    if args.palette:
        palette_hex = [c.strip() for c in args.palette.split(',') if c.strip()]
    else:
        if args.palette_preset == "vibrant":
            palette_hex = ["#0F62FE", "#12B886", "#FF7A59", "#FFD166"]
        elif args.palette_preset == "pastel":
            palette_hex = ["#A5D8FF", "#C3F0CA", "#FFD6A5", "#FFC6FF"]
        elif args.palette_preset == "mono":
            palette_hex = ["#111111", "#555555", "#AAAAAA", "#FFFFFF"]
    img = reduce_colors(img, colors=max(2, args.colors), dither=args.dither, palette_hex=palette_hex)

    # Output paths
    repo_root = Path(__file__).resolve().parents[1]
    ico_path = repo_root / "favicon.ico"

    images_dir = repo_root / "images"
    png_out_dir = images_dir if images_dir.exists() else repo_root
    png_path = png_out_dir / "favicon.png"

    # Save ICO (multi-size)
    save_ico(img, args.sizes, ico_path)

    # Save PNG (single size)
    png_img = fit_square(img, args.png_size)
    png_img.save(png_path, format="PNG")

    # Save Apple touch icon (180x180 by default) at root
    apple_path = repo_root / "apple-touch-icon.png"
    apple_img = fit_square(img, args.apple_size)
    apple_img.save(apple_path, format="PNG")

    # Save Android Chrome icons (192, 512 by default)
    android_paths = []
    for s in args.android_sizes:
        a_img = fit_square(img, s)
        a_path = png_out_dir / f"android-chrome-{s}x{s}.png"
        a_img.save(a_path, format="PNG")
        android_paths.append(a_path)

    print(f"Wrote: {ico_path}")
    print(f"Wrote: {png_path}")
    print(f"Wrote: {apple_path}")
    for p in android_paths:
        print(f"Wrote: {p}")


if __name__ == "__main__":
    main()
