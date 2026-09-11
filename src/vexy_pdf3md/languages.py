# this_file: src/vexy_pdf3md/languages.py
"""Map one --lang list onto backend codes and fetch missing Tesseract models."""

import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from loguru import logger

from .process import ConversionError

TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/{code}.traineddata"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "vexy-pdf3md" / "tessdata"

# ISO 639-1 → Tesseract traineddata name. Tesseract mostly uses 639-2/T plus its own
# script-specific names; unknown codes pass through unchanged so any model can be named.
TESSERACT = {
    "ar": "ara",
    "bg": "bul",
    "bn": "ben",
    "ca": "cat",
    "cs": "ces",
    "cy": "cym",
    "da": "dan",
    "de": "deu",
    "el": "ell",
    "en": "eng",
    "es": "spa",
    "et": "est",
    "eu": "eus",
    "fa": "fas",
    "fi": "fin",
    "fr": "fra",
    "ga": "gle",
    "he": "heb",
    "hi": "hin",
    "hr": "hrv",
    "hu": "hun",
    "hy": "hye",
    "id": "ind",
    "is": "isl",
    "it": "ita",
    "ja": "jpn",
    "ka": "kat",
    "kk": "kaz",
    "ko": "kor",
    "lt": "lit",
    "lv": "lav",
    "mk": "mkd",
    "ms": "msa",
    "nb": "nor",
    "nl": "nld",
    "no": "nor",
    "pl": "pol",
    "pt": "por",
    "ro": "ron",
    "ru": "rus",
    "sk": "slk",
    "sl": "slv",
    "sq": "sqi",
    "sr": "srp",
    "sv": "swe",
    "ta": "tam",
    "te": "tel",
    "th": "tha",
    "tr": "tur",
    "uk": "ukr",
    "ur": "urd",
    "vi": "vie",
    "zh": "chi_sim",
    "zh-hans": "chi_sim",
    "zh-hant": "chi_tra",
    "zh-tw": "chi_tra",
    "zh-hk": "chi_tra",
}
VISION = {tess: iso for iso, tess in TESSERACT.items() if len(iso) == 2}


def parse(lang: str) -> list[str]:
    """Accept eng,pol / en,pl / eng+pol and return unique Tesseract codes in order."""
    codes = []
    for raw in lang.replace("+", ",").split(","):
        code = raw.strip()
        if code and (mapped := TESSERACT.get(code.lower(), code)) not in codes:
            codes.append(mapped)
    if not codes:
        raise ValueError("lang must name at least one language, e.g. eng,pol or en,pl")
    return codes


def tesseract_codes(lang: str) -> str:
    return "+".join(parse(lang))


def vision_codes(lang: str) -> str:
    """pdf22md's Vision expects BCP-47-ish tags; drop codes Vision cannot name."""
    return ",".join(
        VISION.get(c, c.replace("chi_sim", "zh-Hans").replace("chi_tra", "zh-Hant"))
        for c in parse(lang)
    )


def tessdata_dir(tesseract: str, codes: list[str]) -> Path:
    """Return one directory holding every requested model, downloading fast models on demand."""
    CACHE.mkdir(parents=True, exist_ok=True)
    system = _system_tessdata(tesseract)
    # --tessdata-dir also relocates output configs such as "tsv"; without them Tesseract
    # silently prints plain text, which breaks Docling's TSV parser.
    for name in ("configs", "tessconfigs"):
        if not (CACHE / name).exists():
            if system and (system / name).is_dir():
                shutil.copytree(system / name, CACHE / name, dirs_exist_ok=True)
            elif name == "configs":
                (CACHE / name).mkdir(exist_ok=True)
                (CACHE / name / "tsv").write_text("tessedit_create_tsv 1\n")
    for code in [*codes, "osd"]:
        target = CACHE / f"{code}.traineddata"
        if target.exists():
            continue
        if system and (system / target.name).exists():
            staged = target.with_name(f"{target.name}.{os.getpid()}.part")
            shutil.copy(system / target.name, staged)
            staged.replace(target)
        elif code != "osd":
            logger.info("downloading Tesseract model {} to {}", code, target)
            _download(code, target)
    return CACHE


def _system_tessdata(tesseract: str) -> Path | None:
    result = subprocess.run(
        [tesseract, "--list-langs"], capture_output=True, text=True, check=False
    )
    first = (result.stdout or result.stderr).splitlines()[:1]
    if first and '"' in first[0]:
        return Path(first[0].split('"')[1])
    return None


def _download(code: str, target: Path) -> None:
    """Fetch into a per-process temp file so parallel workers never read a torn model."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f"{target.name}.{os.getpid()}.part")
    try:
        with urllib.request.urlopen(TESSDATA_URL.format(code=code), timeout=60) as response:
            partial.write_bytes(response.read())
    except OSError as exc:
        partial.unlink(missing_ok=True)
        raise ConversionError(
            f"no Tesseract model for {code!r} and download failed: {exc}"
        ) from exc
    partial.replace(target)
