# BlueShare Repository Audit

Date: 2026-07-24
Branch: `main`
Audit baseline: commit `72c3ebe` (`blueshare`)

## Scope

This audit records the repository state before structural cleanup. It does not
claim that the legacy network, payment, Bluetooth, privacy, or desktop features
are implemented.

## Current directory map

```text
acceptance/       deterministic spatial acceptance model, tests, and reports
blueshare/        BPETS research, vision documents, PDFs, pruning work, and audio
blueshare2go/     legacy C/Python demonstrations and shell scripts
images/           handwritten topology reference images
LICENSE.md        project licence
README.md         repository overview
```

The root also contains an empty `.agents/` directory. During this audit,
temporary PDF renders exist only under `tmp/pdfs/` and must be removed before
the cleanup is complete.

## Duplicate and near-duplicate files

### Exact duplicates

| Files | Evidence | Decision |
| --- | --- | --- |
| `blueshare/blueshare_implementation.sh` and `blueshare/blueshare/blueshare_implementation.sh` | Both are 17,954 bytes; SHA-256 `3F632203DCF89B78EEAAE3B366B500CC3C0C5F39C3CC7B20C67F26FA6A45627C` | Keep one historical bootstrap generator under `scripts/build/`; remove the byte-identical duplicate and record it. |
| `blueshare/pruning/pruning_operator.py` and `blueshare/pruning/test_pruning.py` | SHA-256 `C8039A269F104C62652AF9F0C311D81CF3790A7659B84BA62F8967CB22514C7B` | Keep `pruning_operator.py`; remove the misleading duplicate `test_pruning.py`. It contains no test functions. |

### Similar but distinct

| Files | Finding |
| --- | --- |
| The two 4D tensor framework Markdown documents | Different hashes and a substantial content diff (90 insertions, 141 deletions). Preserve both as research. |
| `blueshare/blueshare/Vision_Docs/blueshare_overview.md` and `blueshare2go/overview.md` | Different hashes and purposes: the first is a detailed implementation/vision document; the second is a short service overview. Preserve both with descriptive destinations. |
| Root `README.md`, `blueshare/README.md`, and `blueshare2go/README.md` | Distinct documents. The root describes this repository, `blueshare/README.md` is a BPETS vision, and `blueshare2go/README.md` describes the legacy product concept. |

## Generated files present

- Eight untracked `*.pyc` files across three `__pycache__/` directories under
  `acceptance/`.
- Temporary PDF inspection files under `tmp/pdfs/` created for this audit.
- No generated Python cache file is tracked by Git.

The four files in `acceptance/reports/` are untracked but are retained as
timestamped acceptance evidence. They will not be ignored automatically.

## Path and naming inconsistencies

- Product, research, and reference material are mixed under `blueshare/`.
- `blueshare/blueshare/` is an unnecessary nested directory.
- `derivate_tracing` is a directory spelling error; the intended term is
  `derivative-tracing`.
- Native C sources and public headers are split between
  `blueshare2go/blueshare/` and `blueshare2go/src/`.
- Python modules live under two different legacy subdirectories and do not form
  an importable package.
- Images are at the root and audio is under `blueshare/sound/`.
- The GitHub Actions workflow is outside `.github/workflows/` and refers to a
  nonexistent `bpets/core/dimension_control/pruning` tree.
- Documentation filenames use mixed case, spaces, underscores, and duplicate
  naming conventions.
- The root README still refers to an old `blueshare-polyglot-exosketelon/`
  path and incorrectly labels the now-tracked `blueshare2go/` tree as untracked.

## Build entry points

| Entry point | Current condition |
| --- | --- |
| `blueshare2go/CMakeLists.txt` | Broken. It requires unavailable `gosi-lang`, `node-zero`, and `libpolycall` pkg-config packages and references nine missing C sources/targets. |
| `blueshare2go/scripts/build.sh` | WSL/Linux-oriented; assumes the broken CMake project and a missing `blueshare_test` executable. |
| `blueshare2go/blueshare/build.sh` | WSL/Linux-oriented; expects filenames that are not present (`blueshare_core.c`, `blueshare_nodezero.c`, and an optional prototype filename). |
| `blueshare2go/release.sh` | Preserves evidence that BlueShare2Go is intended as a public package name, but cannot run because `package.json`, `CHANGELOG.md`, and an npm package are absent. It can commit, tag, push, and publish, so it must not be executed during cleanup. |
| `blueshare/blueshare_implementation.sh` | Historical repository generator. It writes a separate service tree and embeds obsolete paths; it is not a normal build command. |

The three C files are independent demonstrations with their own `main()`
functions. `blueshare.c` is a self-contained session simulation, `zero.c`
requires OpenSSL, and `nsiggi.c` requires the Linux `getrandom()` API. The public
header declares a library API that none of these files implements.

## Test entry points

| Entry point | Current condition |
| --- | --- |
| `python -m unittest discover -s acceptance/tests -v` | Real automated acceptance tests; previously observed passing. Must be rerun after cleanup. |
| `python acceptance/run_spatial_acceptance.py` | Real deterministic evidence generator; explicitly does not validate hardware ranging. |
| `blueshare/pruning/test_pruning.py` | Not a test; byte-identical to the implementation module. |
| `blueshare2go/tests/constitutional/test_constitutional_compliance.sh` | Test driver only; cannot run because the expected `build/blueshare_test` executable is missing. |
| `blueshare/pruning-ci.yml` | Structurally a GitHub Actions workflow, but its paths, test directory, and `consciousness-check.py` dependency do not exist in this repository. |

## Documentation groups

- **Vision:** BlueShare overview/deployment Markdown and the BPETS vision.
- **Specifications:** BPETS specification and pruning formal definition.
- **Architecture/research:** NLM Atlas, derivative tracing, infinite derivative,
  freedom-of-dexterity, and graph-pruning material.
- **Reference:** BlueShare Service Overview and Deployment Guide PDFs.
- **Legacy product:** BlueShare2Go README and overview.
- **Acceptance:** the spatial MVP README and timestamped reports.

PDF inspection confirmed that the NLM Atlas PDF is a technical implementation
specification, the two derivative PDFs are mathematical research, and the two
BlueShare Service PDFs are product reference/deployment documents. No PDF was
modified.

## Unclear or external ownership

- BlueShare2Go is referenced as a GitHub/NPM product name by the release script.
  The name must retain a compatibility path even after source consolidation.
- `gosi-lang`, `node-zero`, and `libpolycall` are named external dependencies,
  but their required versions and local integration contracts are absent.
- `consciousness-check.py`, `git-subdex`, and the described BPETS package tree
  are referenced by documents/CI but are not in this repository.
- The declared functions in `blueshare_core.h` have no matching implementation.
- The root `.agents/` directory is empty; no ownership information is present.

## Files requiring conservative treatment

- Acceptance reports, PDFs, images, and audio are evidence/reference assets and
  must be moved without content changes.
- Both distinct 4D tensor documents must remain separate.
- `release.sh` must be retained but documented as non-runnable and potentially
  mutating.
- The pruning manifest must not be presented as a desktop/NW.js manifest.
- The legacy public headers must keep their public symbol names during cleanup.
- Research contents must not be rewritten merely to normalize terminology.

## Audit conclusion

The repository contains useful acceptance code, independent C/Python
demonstrations, and substantial research, but no complete native library,
desktop application, Bluetooth transport, hotspot implementation, payment
system, or Android package. Cleanup should normalize ownership and make the
existing demos build where practical without turning design claims into
implemented features.
