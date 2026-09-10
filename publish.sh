#!/usr/bin/env bash
# this_file: publish.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

die() { printf '%s\n' "$*" >&2; exit 1; }
command -v uv >/dev/null
command -v uvx >/dev/null
[[ "$(git rev-parse --show-prefix)" == "" ]] || die 'Run from the package Git root.'
git symbolic-ref --quiet HEAD >/dev/null || die 'Release from a branch, not detached HEAD.'
version_file=src/vexy_pdf3md/__version__.py
git check-ignore --no-index -q "$version_file" || die "$version_file must be gitignored."

# Remove generated version files from the index if an older checkout tracked them.
# Source dirt is retained for gitnextver to commit; no reset/restore or broad git clean.
git rm --cached --ignore-unmatch -- "$version_file"
git clean -fX -- "$version_file" .DS_Store
uv sync --frozen --all-extras --reinstall-package vexy-pdf3md
UV_FROZEN=1 ./test.sh
git clean -fX -- "$version_file" .DS_Store

# gitnextver stages all nonignored changes, commits, tags, and pushes configured remotes.
# A separate commit here would leave it nothing to tag.
uvx gitnextver --directory "$PWD"
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || die 'gitnextver left uncommitted changes.'
release_tag=$(git describe --exact-match --tags --match 'v[0-9]*' HEAD) ||
    die 'gitnextver did not tag HEAD. It needs source changes, or an existing tagged release to retry.'
[[ "$release_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "Not a release tag: $release_tag"

# Revalidate after gitnextver, which can pull new upstream changes before tagging.
uv sync --frozen --all-extras --reinstall-package vexy-pdf3md
UV_FROZEN=1 ./test.sh
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || die 'Validation dirtied the release tree.'

# gitnextver/GitPython may not propagate a rejected push. Check it directly, also on retries.
remote=$(git remote | head -n 1)
if git remote get-url origin >/dev/null 2>&1; then remote=origin; fi
if [[ -n "$remote" ]]; then
    branch=$(git symbolic-ref --short HEAD)
    git push "$remote" "HEAD:refs/heads/$branch" "refs/tags/$release_tag"
    remote_head=$(git ls-remote "$remote" "refs/heads/$branch" | cut -f1)
    remote_tag=$(git ls-remote "$remote" "refs/tags/$release_tag" | cut -f1)
    [[ "$remote_head" == "$(git rev-parse HEAD)" ]] || die 'Remote branch does not match HEAD.'
    [[ "$remote_tag" == "$(git rev-parse "refs/tags/$release_tag")" ]] || die 'Remote tag mismatch.'
fi

# Build into a fresh directory: old dist/ artifacts can never join this upload.
release_dist=$(mktemp -d "${TMPDIR:-/tmp}/vexy-pdf3md-release.XXXXXX")
trap 'rm -rf -- "$release_dist"' EXIT
uv build --out-dir "$release_dist"
uv run --frozen python - "$release_tag" "$release_dist" <<'PY'
import email
from pathlib import Path
import sys
import tarfile
import zipfile

expected, folder = sys.argv[1].removeprefix("v"), Path(sys.argv[2])
wheels, sdists = list(folder.glob("*.whl")), list(folder.glob("*.tar.gz"))
assert len(wheels) == len(sdists) == 1, "Expected one wheel and one sdist"
with zipfile.ZipFile(wheels[0]) as wheel:
    metadata = wheel.read(next(n for n in wheel.namelist() if n.endswith(".dist-info/METADATA")))
    assert email.message_from_bytes(metadata)["Version"] == expected, "Wheel/tag version mismatch"
    generated = {}
    exec(wheel.read("vexy_pdf3md/__version__.py"), generated)
    assert generated["__version__"] == expected, "Generated version/tag mismatch"
with tarfile.open(sdists[0]) as sdist:
    member = next(m for m in sdist.getmembers() if m.name.endswith("/PKG-INFO"))
    metadata = sdist.extractfile(member).read()
    assert email.message_from_bytes(metadata)["Version"] == expected, "Sdist/tag version mismatch"
print(f"Verified wheel, sdist, and generated __version__.py: {expected}")
PY
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || die 'Build dirtied the release tree.'
mkdir -p dist
cp "$release_dist"/*.whl "$release_dist"/*.tar.gz dist/
if [[ "${PUBLISH_SKIP_UPLOAD:-0}" == 1 ]]; then
    printf 'Validated %s; PUBLISH_SKIP_UPLOAD=1 skips only the package upload.\n' "$release_tag"
else
    uv publish "$release_dist"/*.whl "$release_dist"/*.tar.gz "$@"
    printf 'Published %s.\n' "$release_tag"
fi
