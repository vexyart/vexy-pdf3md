# this_file: src/vexy_pdf3md/paths.py
"""Plan paths once, rejecting collisions before any conversion writes."""

from dataclasses import dataclass
from pathlib import Path

from .models import Options


@dataclass(frozen=True)
class Job:
    source: Path
    output: Path
    requested: str


def plan(input: str | Path, output: str | Path | None, options: Options) -> list[Job]:
    source = Path(input).expanduser().resolve(strict=True)
    destination = Path(output).expanduser().absolute() if output is not None else None
    if source.is_file():
        if source.suffix.lower() != ".pdf":
            raise ValueError("input file must have a .pdf extension")
        target = destination or source.with_suffix(".md")
        if target.is_dir():
            target /= source.with_suffix(".md").name
        if target.suffix.lower() != ".md":
            raise ValueError("single-file output must be an .md file or an existing directory")
        pairs = [(source, target)]
    elif source.is_dir():
        target = destination or source
        if target.exists() and not target.is_dir():
            raise ValueError("directory input requires a directory output")
        files = sorted(
            p
            for p in source.rglob("*")
            if p.is_file() and not p.is_symlink() and p.suffix.lower() == ".pdf"
        )
        pairs = [(p, target / p.relative_to(source).with_suffix(".md")) for p in files]
    else:
        raise ValueError("input must be a regular PDF file or directory")
    if not pairs:
        raise ValueError("input directory contains no PDF files")
    jobs = []
    for pdf, md in pairs:
        for strategy in options.strategies:
            out = md.with_name(f"{md.stem}.{strategy}.md") if len(options.strategies) > 1 else md
            jobs.append(Job(pdf, out, strategy))
    _check_collisions(jobs, options)
    return jobs


def _check_collisions(jobs: list[Job], options: Options) -> None:
    occupied: dict[str, Path] = {}
    sources = {str(j.source.resolve()).casefold() for j in jobs}
    for job in jobs:
        paths = [job.output]
        if options.media != "none":
            paths.append(job.output.with_suffix(""))
        for path in paths:
            key = str(path.resolve()).casefold()
            if key in occupied or key in sources:
                raise ValueError(f"output collision: {path}")
            if path.is_symlink():
                raise ValueError(f"output cannot be a symlink: {path}")
            occupied[key] = path
    for key, path in occupied.items():
        if any(str(parent).casefold() in occupied for parent in Path(key).parents):
            raise ValueError(f"output file/directory collision: {path}")
