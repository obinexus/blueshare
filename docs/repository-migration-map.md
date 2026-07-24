# BlueShare Repository Migration Map

Date: 2026-07-24

This map was created with [`repository-audit.md`](repository-audit.md) before
source moves began. The cleanup is now complete; each row records its executed
destination or removal decision.

## Product source and compatibility

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| `blueshare2go/blueshare/core/blueshare.c` | `native/blueshare-core/src/blueshare.c` | Consolidate the standalone C session demo. | CMake and build scripts. | Completed |
| `blueshare2go/blueshare/core/zero.c` | `native/blueshare-core/src/zero.c` | Consolidate the standalone Node-Zero/OpenSSL demo. | CMake and Node-Zero build script. | Completed |
| `blueshare2go/blueshare/nsiggi.c` | `native/blueshare-core/src/nsiggi.c` | Consolidate the standalone Linux NSIGII demo. | CMake and native README. | Completed |
| `blueshare2go/src/core/blueshare_core.h` | `native/blueshare-core/include/blueshare_core.h` | Canonical public API header location. | `platform_interface.h`, install paths, documentation. | Completed |
| `blueshare2go/src/platform/platform_interface.h` | `native/blueshare-core/include/platform_interface.h` | Canonical platform API header location. | Change relative include to `blueshare_core.h`. | Completed |
| `blueshare2go/tests/constitutional/` | `native/blueshare-core/tests/constitutional/` | Keep the legacy constitutional driver with native code. | Build script and documentation. | Completed |
| `blueshare2go/CMakeLists.txt` | `native/blueshare-core/CMakeLists.txt` | Canonical native build entry point. | Rewrite only enough to describe files that exist. | Completed |
| `blueshare2go/README.md` | `docs/architecture/blueshare2go-service.md` | Preserve the original product description as architecture/history. | Root and docs indexes. | Completed |
| New compatibility file | `blueshare2go/README.md` | BlueShare2Go is referenced as a public GitHub/NPM product name. | Link to migration map and new native/Python/script locations. | Completed |

## Python package

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| `blueshare2go/blueshare/pkg/blueshare.py` | `packages/python/blueshare/blueshare.py` | Form a coherent legacy Python package. | Package README and `__init__.py`. | Completed |
| `blueshare2go/blueshare/nsiggi.py` | `packages/python/blueshare/nsiggi.py` | Keep the NSIGII Python demo beside the BlueShare demo. | Package README and `__init__.py`. | Completed |
| New package initializer | `packages/python/blueshare/__init__.py` | Make the package importable without mixing in acceptance code. | None. | Completed |

## Research and specifications

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| `blueshare/derivate_tracing/` | `research/derivative-tracing/` | Separate mathematical research and correct the directory spelling. All distinct contents remain intact. | Docs index only; no local source references found. | Completed |
| `blueshare/pruning/pruning_operator.py` | `research/pruning/pruning_operator.py` | Separate the experimental pruning implementation. | CI workflow. | Completed |
| `blueshare/pruning/test_pruning.py` | Removed as exact duplicate | It is byte-identical to `pruning_operator.py` and contains no tests. | Audit, migration report, and CI correction. | Completed |
| `blueshare/manifest.json` | `research/pruning/manifest.json` | Content identifies it as a pruning-control manifest, not a desktop manifest. | Docs and current-status notes. | Completed |
| `blueshare/README.md` | `docs/vision/bpets-vision.md` | It identifies itself as the BPETS vision document. | Root/docs indexes. | Completed |
| `blueshare/docs/bpets_spec.md` | `docs/specifications/bpets-spec.md` | Formal product/research specification. | Docs index. | Completed |
| `blueshare/docs/pruning_formal_definition.tex` | `docs/specifications/pruning-formal-definition.tex` | Formal pruning specification source. | Docs index and CI notes. | Completed |
| `blueshare/nlm_atlas_schema_ip.md` | `research/nlm-atlas/nlm-atlas-schema-over-ip.md` | NLM Atlas technical research source. | Docs index. | Completed |
| `blueshare/NLM Atlas Schema Over IP - Technical Architecture.pdf` | `research/nlm-atlas/nlm-atlas-schema-over-ip-technical-architecture.pdf` | NLM Atlas technical research reference. | Docs index. | Completed |

## Product documentation

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| `blueshare/blueshare/Vision_Docs/blueshare_overview.md` | `docs/vision/blueshare-overview.md` | Remove double nesting and normalize the filename. | Docs/root indexes. | Completed |
| `blueshare/blueshare/Vision_Docs/blueshare_deployment.md` | `docs/deployment/blueshare-deployment.md` | Separate deployment guidance and normalize the filename. | Paths inside remain examples and will be annotated by status docs. | Completed |
| `blueshare/docs/BlueShare Service Overview.pdf` | `docs/reference/blueshare-service-overview.pdf` | Preserve the product reference PDF with a stable filename. | Docs index. | Completed |
| `blueshare/docs/BlueShare Service Deployment Guide.pdf` | `docs/reference/blueshare-service-deployment-guide.pdf` | Preserve the deployment reference PDF with a stable filename. | Docs index. | Completed |
| `blueshare2go/overview.md` | `docs/architecture/blueshare2go-overview.md` | Preserve the distinct short service overview. | Docs index and compatibility README. | Completed |

## Assets

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| `images/` | `assets/images/` | Consolidate all 12 unmodified topology reference images. | Assets README; no code references found. | Completed |
| `blueshare/sound/blueshare_obinexus_robotics_date29082025.m4a` | `assets/audio/blueshare_obinexus_robotics_date29082025.m4a` | Consolidate the unmodified audio reference. | Assets README; no code references found. | Completed |

## Scripts and CI

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| `blueshare/blueshare_implementation.sh` | `scripts/build/bootstrap-legacy-blueshare-service.sh` | Retain the canonical historical generator with a descriptive name. | Scripts README; embedded output paths are intentional historical content. | Completed |
| `blueshare/blueshare/blueshare_implementation.sh` | Removed as exact duplicate | Same length and SHA-256 as the canonical generator. | Cleanup report. | Completed |
| `blueshare2go/scripts/build.sh` | `scripts/build/build-blueshare-core.sh` | Canonical WSL native build wrapper. | Repair repository-relative native paths. | Completed |
| `blueshare2go/blueshare/build.sh` | `scripts/build/build-blueshare2go-node-zero.sh` | Preserve the distinct Node-Zero/OpenSSL build behaviour. | Repair source/output paths; document limitations. | Completed |
| `blueshare2go/scripts/create_network.sh` | `scripts/network/create-network.sh` | Consolidate the legacy CLI driver. | Document missing CLI target. | Completed |
| `blueshare2go/release.sh` | `scripts/release/release-blueshare2go.sh` | Preserve public-package release history away from runtime source. | Repair working-directory discovery; document missing package metadata. | Completed |
| `blueshare/pruning-ci.yml` | `.github/workflows/pruning-ci.yml` | It is a GitHub Actions workflow. | Replace nonexistent BPETS paths with `research/pruning`; remove nonexistent test/checker invocations. | Completed |

## New or normalized repository files

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| Root `.gitignore` (incomplete working file) and `blueshare2go/.gitignore` | Root `.gitignore` | Consolidate generated/build exclusions while keeping acceptance reports visible. | None. | Completed |
| New file | `CMakeLists.txt` | Delegate the root build to `native/blueshare-core/`. | Root README. | Completed |
| New file | `native/blueshare-core/README.md` | Explain the three demos, header/API gap, and platform constraints. | Docs/root indexes. | Completed |
| New file | `packages/python/README.md` | Explain the experimental Python package and commands. | Docs/root indexes. | Completed |
| New file | `apps/desktop/README.md` | Record that no desktop application or NW.js manifest currently exists. | Root/current status. | Completed |
| New file | `assets/README.md` | Record asset provenance and non-modification. | Docs index. | Completed |
| New file | `scripts/README.md` | Document PowerShell/WSL support and broken assumptions. | Root/docs indexes. | Completed |
| New file | `docs/README.md` | Index documentation and research. | Root README. | Completed |
| New file | `docs/current-status.md` | Separate implemented, experimental, research, acceptance, planned, and incomplete work. | Root README. | Completed |

## Generated cleanup

| Old path | New path | Reason | References requiring updates | Status |
| --- | --- | --- | --- | --- |
| `acceptance/**/__pycache__/` and `acceptance/**/*.pyc` | Removed | Generated, untracked Python cache files. | Root `.gitignore`. | Completed |
| `tmp/pdfs/` | Removed | Temporary PDF audit renders/text. | Root `.gitignore` is not required because the directory is audit-only. | Completed |

## Explicit non-moves

- `acceptance/spatial_mvp/`, `acceptance/tests/`, and all four
  `acceptance/reports/` files remain in place.
- `LICENSE.md` remains at the root.
- Public C API names are unchanged.
- Distinct research documents are not merged.
- No desktop manifest is created from the pruning manifest.
