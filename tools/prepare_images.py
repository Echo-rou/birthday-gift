"""Create WebP copies and tiny previews without touching the original JPEGs.

Requires Pillow (``python -m pip install Pillow``).
Run from any directory:
    python tools/prepare_images.py --manifest ../ref/image-manifest.json

The manifest can be embedded in index.html; no runtime request is necessary.
"""

import argparse
import base64
import io
import json
import re
from pathlib import Path

from PIL import Image, ImageOps, features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--quality", type=int, default=78)
    parser.add_argument("--max-edge", type=int, default=1600)
    parser.add_argument("--cover-quality", type=int, default=76)
    parser.add_argument("--cover-max-edge", type=int, default=1280)
    parser.add_argument("--embed", action="store_true", help="Update the marked IMAGE_ASSETS block in index.html")
    args = parser.parse_args()
    if not features.check("webp"):
        parser.error("This Pillow installation does not support WebP")
    if not (1 <= args.quality <= 100 and 1 <= args.cover_quality <= 100) or min(args.max_edge, args.cover_max_edge) < 32:
        parser.error("quality must be 1–100; max-edge must be at least 32")

    root = args.root.resolve()
    paths = [root / "assets" / name for name in ("cover.jpg", "video-poster.jpg")]
    paths += sorted((root / "photos").glob("*.jpg"))
    manifest = {}
    original_bytes = selected_bytes = 0
    for path in paths:
        with Image.open(path) as source:
            # Bake EXIF orientation into pixels and leave metadata out of public copies.
            image = ImageOps.exif_transpose(source).convert("RGB")
        is_cover = path == root / "assets" / "cover.jpg"
        edge = args.cover_max_edge if is_cover else args.max_edge
        image.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        webp = path.with_suffix(".webp")
        webp_buffer = io.BytesIO()
        image.save(webp_buffer, "WEBP", quality=args.cover_quality if is_cover else args.quality, method=6)
        before = path.stat().st_size
        # Already-compressed high-detail JPEGs can be smaller. Keep using those.
        use_webp = is_cover or len(webp_buffer.getvalue()) < before
        if use_webp:
            webp.write_bytes(webp_buffer.getvalue())
        elif webp.exists():
            webp.unlink()  # Only this script's derived sibling, never the source JPEG.

        preview = image.copy()
        preview.thumbnail((32, 32), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        preview.save(buffer, "JPEG", quality=45, optimize=True)
        key = path.relative_to(root).as_posix()
        manifest[key] = {
            "webp": (webp if use_webp else path).relative_to(root).as_posix(),
            "width": image.width,
            "height": image.height,
            "preview": "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii"),
        }
        after = webp.stat().st_size if use_webp else before
        original_bytes += before
        selected_bytes += after
        print(f"{key}: {before:,} -> {after:,} bytes ({100 * (1 - after / before):.1f}% smaller; {'WebP' if use_webp else 'original JPEG'})")

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest_json = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
    args.manifest.write_text(manifest_json + "\n", encoding="utf-8")
    if args.embed:
        index = root / "index.html"
        html = index.read_text(encoding="utf-8")
        pattern = r"(// IMAGE_MANIFEST:[^\n]*\n).*?(// END_IMAGE_MANIFEST)"
        html, count = re.subn(pattern, lambda match: match[1] + "const IMAGE_ASSETS = " + manifest_json + ";\n" + match[2], html, flags=re.S)
        if count != 1:
            raise SystemExit("Expected exactly one IMAGE_MANIFEST block in index.html; HTML was not changed")
        cover_preview = manifest["assets/cover.jpg"]["preview"]
        html = re.sub(
            r"(#cover\{background-size:cover;background-position:46% 36%;background-image:url\()[^)]*(\)\})",
            lambda match: match[1] + cover_preview + match[2], html,
        )
        index.write_text(html, encoding="utf-8")
        print(f"Embedded manifest in {index}")
    print(f"TOTAL: {original_bytes:,} -> {selected_bytes:,} bytes ({100 * (1 - selected_bytes / original_bytes):.1f}% smaller)")
    print(f"Manifest: {args.manifest.resolve()} ({args.manifest.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
