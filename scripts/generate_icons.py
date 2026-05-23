#!/usr/bin/env python3
"""Genera le icone PWA a partire dai loghi nella root del progetto."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'app' / 'static' / 'icons'

SOURCE_CANDIDATES = (
    ROOT / 'logo.png',
    ROOT / 'logo.jpg',
    ROOT / 'logo.jpeg',
    ROOT / 'logo.webp',
)

SIZES = {
    'favicon-16.png': 16,
    'favicon-32.png': 32,
    'apple-touch-icon.png': 180,
    'icon-192.png': 192,
    'icon-512.png': 512,
}

MASKABLE_SIZE = 512
MASKABLE_SAFE_RATIO = 0.82


def find_source() -> Path:
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    names = ', '.join(p.name for p in SOURCE_CANDIDATES)
    raise FileNotFoundError(f'Nessun logo trovato in root. Attesi: {names}')


def load_source(path: Path) -> Image.Image:
    return Image.open(path).convert('RGBA')


def resize_icon(source: Image.Image, size: int) -> Image.Image:
    return source.resize((size, size), Image.Resampling.LANCZOS)


def background_color(source: Image.Image) -> tuple[int, int, int]:
    rgb = source.convert('RGB')
    samples = [
        rgb.getpixel((0, 0)),
        rgb.getpixel((rgb.width - 1, 0)),
        rgb.getpixel((0, rgb.height - 1)),
        rgb.getpixel((rgb.width - 1, rgb.height - 1)),
    ]
    return tuple(sum(channel[i] for channel in samples) // len(samples) for i in range(3))


def render_maskable(source: Image.Image, size: int = MASKABLE_SIZE) -> Image.Image:
    bg = background_color(source) + (255,)
    canvas = Image.new('RGBA', (size, size), bg)
    safe = int(size * MASKABLE_SAFE_RATIO)
    scale = min(safe / source.width, safe / source.height)
    new_size = (max(1, int(source.width * scale)), max(1, int(source.height * scale)))
    resized = source.resize(new_size, Image.Resampling.LANCZOS)
    offset = ((size - new_size[0]) // 2, (size - new_size[1]) // 2)
    canvas.paste(resized, offset, resized)
    return canvas


def write_svg_icon(out_dir: Path) -> None:
    svg = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 512 512\" role=\"img\">
  <image href=\"icon-512.png\" width=\"512\" height=\"512\"/>
</svg>
"""
    (out_dir / 'icon.svg').write_text(svg, encoding='utf-8')


def save_png(image: Image.Image, path: Path) -> None:
    if image.mode == 'RGBA':
        flat = Image.new('RGB', image.size, background_color(image))
        flat.paste(image, mask=image.split()[3])
        flat.save(path, optimize=True)
    else:
        image.convert('RGB').save(path, optimize=True)


def main() -> None:
    source_path = find_source()
    source = load_source(source_path)
    OUT.mkdir(parents=True, exist_ok=True)

    print(f'Source: {source_path} ({source.width}x{source.height})')

    for name, size in SIZES.items():
        icon = resize_icon(source, size)
        save_png(icon, OUT / name)
        print(f'Wrote {OUT / name}')

    maskable = render_maskable(source)
    save_png(maskable, OUT / 'maskable-512.png')
    print(f'Wrote {OUT / "maskable-512.png"}')

    write_svg_icon(OUT)
    print(f'Wrote {OUT / "icon.svg"}')


if __name__ == '__main__':
    main()
