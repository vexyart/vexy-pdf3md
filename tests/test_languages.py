# this_file: tests/test_languages.py
"""One --lang list feeds Tesseract, Docling, and pdf22md; missing models are fetched."""

from pathlib import Path

import pytest

from vexy_pdf3md import languages
from vexy_pdf3md.models import Options
from vexy_pdf3md.process import ConversionError


def test_parse_when_iso_and_tesseract_codes_mixed_then_unique_tesseract_order_kept():
    assert languages.parse("pl, en,pol,zh,de+fra") == ["pol", "eng", "chi_sim", "deu", "fra"]


def test_parse_when_unknown_code_then_passed_through_for_custom_models():
    assert languages.parse("script/Latin,xyz,PL") == ["script/Latin", "xyz", "pol"]


def test_parse_when_empty_then_value_error():
    with pytest.raises(ValueError, match="lang must name"):
        languages.parse(" , ")


def test_vision_codes_when_tesseract_codes_then_two_letter_tags():
    assert languages.vision_codes("pol,eng,chi_tra") == "pl,en,zh-Hant"


def test_options_when_lang_blank_then_rejected():
    with pytest.raises(ValueError, match="lang must name"):
        Options(lang="+")


def test_tessdata_dir_when_model_missing_then_downloaded_beside_system_copies(
    tmp_path, monkeypatch
):
    system = tmp_path / "system"
    (system / "configs").mkdir(parents=True)
    (system / "configs" / "tsv").write_text("tessedit_create_tsv 1\n")
    (system / "eng.traineddata").write_bytes(b"eng")
    (system / "osd.traineddata").write_bytes(b"osd")
    cache = tmp_path / "cache"
    fetched = []
    monkeypatch.setattr(languages, "CACHE", cache)
    monkeypatch.setattr(languages, "_system_tessdata", lambda tesseract: system)
    monkeypatch.setattr(
        languages,
        "_download",
        lambda code, target: fetched.append(code) or target.write_bytes(b"dl"),
    )
    result = languages.tessdata_dir("tesseract", ["eng", "pol"])
    assert result == cache, "all models must live in one directory for --tessdata-dir"
    assert fetched == ["pol"], "only the missing model is downloaded; osd is never fetched"
    assert (cache / "eng.traineddata").read_bytes() == b"eng"
    assert (cache / "osd.traineddata").exists(), "osd is copied when the system has it"
    assert (cache / "configs" / "tsv").exists(), "output configs must follow --tessdata-dir"
    languages.tessdata_dir("tesseract", ["pol"])
    assert fetched == ["pol"], "cached models are not downloaded twice"


def test_tessdata_dir_when_no_system_configs_then_tsv_config_written(tmp_path, monkeypatch):
    monkeypatch.setattr(languages, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(languages, "_system_tessdata", lambda tesseract: None)
    monkeypatch.setattr(languages, "_download", lambda code, target: target.write_bytes(b"dl"))
    result = languages.tessdata_dir("tesseract", ["eng"])
    assert (result / "configs" / "tsv").read_text().startswith("tessedit_create_tsv 1")


def test_download_when_network_fails_then_conversion_error_and_no_partial(tmp_path, monkeypatch):
    def broken(url, timeout):
        raise OSError("offline")

    monkeypatch.setattr(languages.urllib.request, "urlopen", broken)
    target = tmp_path / "pol.traineddata"
    with pytest.raises(ConversionError, match="download failed"):
        languages._download("pol", target)
    assert not target.exists() and not target.with_suffix(".part").exists()


def test_system_tessdata_when_list_langs_names_dir_then_parsed(monkeypatch):
    class Done:
        stdout = 'List of available languages in "/opt/x/tessdata/" (2):\neng\nosd\n'
        stderr = ""

    monkeypatch.setattr(languages.subprocess, "run", lambda *a, **k: Done())
    assert languages._system_tessdata("tesseract") == Path("/opt/x/tessdata")
