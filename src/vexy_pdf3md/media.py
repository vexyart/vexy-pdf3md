# this_file: src/vexy_pdf3md/media.py
"""Backend-independent media export, linked relative to the final Markdown file."""

from pathlib import Path
from urllib.parse import quote

import pymupdf


def export_media(pdf: Path, folder: Path, basename: str, options: dict, pages: list[int]) -> str:
    """Render raster placements, or complete pages including vector artwork."""
    if options["media"] == "none":
        return ""
    assets = folder / basename
    assets.mkdir(parents=True)
    links = []
    with pymupdf.open(pdf) as doc:
        for index, page in enumerate(doc):
            regions = (
                [page.rect]
                if options["media"] == "pages"
                else [
                    (pymupdf.Rect(i["bbox"]) * page.rotation_matrix) & page.rect
                    for i in page.get_image_info()
                ]
            )
            for number, region in enumerate(regions, 1):
                if region.is_empty or region.is_infinite:
                    continue
                name = f"page-{pages[index] + 1:04d}-{number:03d}.png"
                page.get_pixmap(dpi=options["dpi"], clip=region, alpha=False).save(assets / name)
                url = quote(f"{basename}/{name}", safe="/")
                links.append(f"![Page {pages[index] + 1}, image {number}]({url})")
    return "\n\n## Media\n\n" + "\n\n".join(links) if links else ""
