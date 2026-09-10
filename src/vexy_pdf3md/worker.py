# this_file: src/vexy_pdf3md/worker.py
"""Private stdin/file protocol. Native crashes remain confined to this process."""

import json
import sys
from pathlib import Path

from .backends import convert_backend
from .inspection import inspect, prepared_pdf
from .media import export_media


def execute(request: dict, folder: Path) -> dict:
    options = request["options"]
    if request["action"] == "inspect":
        return inspect(request["source"], options)
    pdf = prepared_pdf(request["source"], options, folder)
    text = convert_backend(request["strategy"], pdf, folder, options, request["profile"])
    (folder / "result.md").write_text(text, encoding="utf-8")
    return {"characters": len(text)}


def main() -> None:
    response = Path(sys.argv[1])
    try:
        request = json.load(sys.stdin)
        if request["action"] == "media":
            pdf = prepared_pdf(request["source"], request["options"], response.parent)
            result = {
                "markdown": export_media(
                    pdf,
                    response.parent / "media",
                    request["basename"],
                    request["options"],
                    request["profile"]["pages"],
                )
            }
        else:
            result = execute(request, response.parent)
    except Exception as exc:  # noqa: BLE001 - serialize errors across the process boundary.
        result = {"error": f"{type(exc).__name__}: {exc}"}
    response.write_text(json.dumps(result), encoding="utf-8")


if __name__ == "__main__":
    main()
