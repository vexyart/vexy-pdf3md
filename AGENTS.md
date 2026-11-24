---
this_file: AGENTS.md
---
# Documentation site

Edit pages in `src_docs/md/` and configure the site in `src_docs/mkdocs.yml`.
Run `./build.sh docs` to rebuild the tracked `docs/` directory in strict mode.
`src_docs/build.sh` pins the docs dependencies for Python 3.13, including
fly-january 0.2.1. Keep `extra.fly.chrome` set to `none` for this unofficial site.
