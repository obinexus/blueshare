# BlueShare repository cleanup report

Date: 2026-07-24
Repository: `C:\Users\OBINexus\Projects\blueshare\blueshare`

## 1. Audit summary

The repository was audited before source moves. The evidence is recorded in
[`repository-audit.md`](repository-audit.md), and the old-to-new decisions are
recorded in [`repository-migration-map.md`](repository-migration-map.md).

The audit found a working Python spatial acceptance slice, several independent
C/Python demonstrations, one experimental pruning module, substantial research
material, historical build/release scripts, and no integrated desktop or
network service. Five PDF first pages were rendered and inspected to distinguish
product reference documents from mathematical and NLM Atlas research.

## 2. Original problems

- Product code, research, documentation, scripts, and assets were mixed under
  the ambiguous `blueshare/` and `blueshare2go/` trees.
- A second `blueshare/blueshare/` nesting duplicated one implementation script.
- `derivate_tracing` was misspelled and mixed Markdown with research PDFs.
- `test_pruning.py` was not a test; it was byte-identical to the implementation.
- The pruning workflow referenced paths and checks that did not exist.
- The legacy CMake file referenced missing sources and invalid targets.
- C files with separate `main()` functions were presented like one native core.
- Public headers described an API that no current C source implements.
- Python cache files and temporary audit renders were present.
- Shell scripts mixed CRLF and LF endings and contained obsolete relative paths.
- The pruning manifest could have been mistaken for a desktop manifest.
- Existing documentation blurred implemented, experimental, planned, and
  research-only capabilities.

## 3. Final repository tree

```text
blueshare/
|-- apps/
|   `-- desktop/README.md
|-- native/
|   `-- blueshare-core/
|       |-- include/{blueshare_core.h,platform_interface.h}
|       |-- src/{blueshare.c,nsiggi.c,zero.c}
|       |-- tests/constitutional/test_constitutional_compliance.sh
|       |-- CMakeLists.txt
|       `-- README.md
|-- packages/
|   `-- python/
|       |-- blueshare/{__init__.py,blueshare.py,nsiggi.py}
|       `-- README.md
|-- acceptance/
|   |-- spatial_mvp/
|   |-- tests/
|   |-- reports/
|   |-- run_spatial_acceptance.py
|   `-- README.md
|-- research/
|   |-- derivative-tracing/
|   |-- pruning/{manifest.json,pruning_operator.py}
|   |-- nlm-atlas/
|   `-- README.md
|-- docs/
|   |-- architecture/
|   |-- deployment/
|   |-- specifications/
|   |-- vision/
|   |-- reference/
|   |-- current-status.md
|   |-- repository-audit.md
|   |-- repository-migration-map.md
|   |-- repository-cleanup-report.md
|   `-- README.md
|-- assets/{audio,images}/
|-- scripts/{build,release,network}/
|-- blueshare2go/README.md
|-- .github/workflows/pruning-ci.yml
|-- .gitignore
|-- CMakeLists.txt
|-- LICENSE.md
`-- README.md
```

The app-managed empty `.agents/` directory and Git metadata are not shown.
Generated `build/` output was removed after validation.

## 4. Files moved

- Native C sources, headers, CMake, and constitutional driver moved from
  `blueshare2go/` to `native/blueshare-core/` with `git mv`.
- Python demonstrations moved to `packages/python/blueshare/`.
- Derivative-tracing, pruning, and NLM Atlas material moved to `research/`.
- Product Markdown/PDF material moved into the appropriate `docs/` category.
- Twelve images moved unchanged to `assets/images/`; one M4A moved unchanged to
  `assets/audio/`.
- Build, network, release, and historical bootstrap scripts moved to `scripts/`.
- The pruning workflow moved to `.github/workflows/pruning-ci.yml`.

Every individual old/new path is listed in
[`repository-migration-map.md`](repository-migration-map.md).

## 5. Files renamed

- `derivate_tracing/` became `research/derivative-tracing/`.
- Vision, deployment, specification, NLM Atlas, PDF, and shell-script filenames
  were normalized to descriptive kebab-case where doing so did not alter public
  API names.
- `blueshare_implementation.sh` became
  `scripts/build/bootstrap-legacy-blueshare-service.sh`.
- The public C headers and the acceptance paths retained their existing names.

## 6. Files removed

- Removed the exact duplicate nested `blueshare_implementation.sh`.
- Removed `test_pruning.py`, which was an exact duplicate of
  `pruning_operator.py` and contained no tests.
- Removed eight generated `.pyc` files and three `__pycache__` directories.
- Removed temporary PDF audit renders under `tmp/pdfs/`.
- Merged and removed the legacy `blueshare2go/.gitignore`.
- Removed empty post-migration `blueshare/` and `crates/` directory trees.
- Removed generated `build/` output after all builds and tests completed.

## 7. Duplicate decisions

The duplicate implementation scripts matched in size (17,954 bytes) and SHA-256
(`3F632203DCF89B78EEAAE3B366B500CC3C0C5F39C3CC7B20C67F26FA6A45627C`).
Only the canonical copy was retained.

`test_pruning.py` and `pruning_operator.py` shared SHA-256
`C8039A269F104C62652AF9F0C311D81CF3790A7659B84BA62F8967CB22514C7B`.
Only the implementation was retained. Similar-looking 4D tensor and BlueShare
overview documents had different content and were deliberately preserved.

## 8. Compatibility preservation

- `blueshare2go/README.md` preserves the public BlueShare2Go name and redirects
  readers to canonical native, Python, script, and architecture locations.
- C public symbol/header names were not renamed.
- Historical bootstrap and release scripts were preserved as compatibility and
  provenance material rather than silently discarded.
- The network and constitutional drivers now resolve the repository root and
  fail clearly with exit code 2 when their unimplemented binaries are absent.

## 9. References updated

- Root CMake delegates only to `native/blueshare-core/`.
- `platform_interface.h` includes `blueshare_core.h` from the canonical include
  directory.
- Native build scripts use repository-relative canonical paths.
- Pruning CI and specification comments point to `research/pruning/`.
- Deployment documentation is labelled as a historical proposal and links to
  current native/status documents.
- Root, docs, scripts, assets, Python, native, research, desktop, and
  BlueShare2Go READMEs cross-reference the new layout.

## 10. Commands run

The main verification commands were:

```text
py -3.14 -m unittest discover -s acceptance\tests -v
py -3.14 acceptance\run_spatial_acceptance.py --output-dir build\acceptance-reports
python packages\python\blueshare\nsiggi.py
python packages\python\blueshare\blueshare.py
cmake -S . -B build
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure
wsl bash scripts/build/build-blueshare-core.sh Release
wsl bash -n <each retained shell script>
wsl bash native/blueshare-core/tests/constitutional/test_constitutional_compliance.sh
wsl bash scripts/network/create-network.sh
git diff --check
git diff --cached --check
```

Pruning was also imported and exercised with a local NumPy matrix matching the
CI invariant. Destructive release/bootstrap scripts were not executed.

## 11. Exact test results

- Python 3.14 acceptance unit tests: **5/5 passed**.
- Spatial runner: **PASS**, 13 distance samples, maximum absolute error
  `0.000000 m`, maximum symmetry delta `0.000000 m`.
- Pruning invariant on Python 3.13.9 / NumPy 2.3.5: **PASS** (`FoD=0.00`,
  `H=1.00`).
- Python NSIGII demonstration: exit 0 and reported `VERIFIED`.
- Python BlueShare demonstration: exit 0 after its designed mixed-consent
  rejection (2 YES, 1 NO, 1 MAYBE).
- All six retained shell scripts: `bash -n` exit 0.
- Constitutional compatibility driver: expected exit 2 because
  `blueshare_test` is not implemented.
- Network compatibility driver: expected exit 2 because `blueshare_cli` is not
  implemented.
- Working-tree `git diff --check`: **passed**. The cleanup-scoped staged check:
  **passed**. The full staged check remains nonzero only for the preserved,
  previously staged acceptance set (1,572 CRLF/EOF messages) and `LICENSE.md`
  change (212 CRLF messages); neither set was reformatted by this cleanup.

## 12. Exact build results

- Windows CMake configure: **passed**.
- Windows Debug build: **passed** for `blueshare_demo.exe` and
  `blueshare_node_zero_demo.exe`; the Linux-only NSIGII target was correctly
  skipped.
- Windows CTest: **1/1 passed**. The retained demo intentionally rejects mixed
  consent, so the test metadata records its nonzero exit as expected.
- WSL Release build with GCC 14.2: **passed** for `blueshare_demo` and
  `blueshare_nsigii_demo`.
- WSL CTest: **2/2 passed**.
- WSL OpenSSL was unavailable, so the optional Node-Zero target was correctly
  skipped there; it built successfully on Windows.

An earlier direct `ctest` invocation without `-C Debug` failed under the
multi-configuration Visual Studio generator. The documented command includes
the required configuration. A later test run exposed the intentional demo
rejection as misclassified; only CTest metadata was corrected, and both final
platform runs passed.

## 13. Remaining broken paths

- `blueshare_core.h` declares a future library API not implemented by current
  sources.
- `blueshare_cli` and `blueshare_test` do not exist.
- No desktop application, desktop manifest, network daemon, Bluetooth adapter,
  hardware ranging adapter, Android project, Java/JAR layer, Rust crate, or FFI
  bridge exists.
- The historical release script has no package metadata and is not runnable.
- The historical bootstrap script generates its former architecture and is not
  a current build entry point.
- Some deployment/reference documents describe proposed components and paths;
  their historical content is preserved and explicitly labelled.

## 14. Deliberately not moved or rewritten

- `acceptance/spatial_mvp/`, `acceptance/tests/`, and all four timestamped
  acceptance report pairs remain under `acceptance/`.
- `LICENSE.md` remains at the root. Its pre-existing staged modification was not
  altered or discarded during cleanup.
- Distinct research documents were not merged even when their subjects overlap.
- PDF, image, and audio contents were not modified.
- Public C names were retained.
- The app-managed `.agents/` directory was left alone.
- No commit or push was created.

## 15. Recommended next task

Implement the smallest coherent native library behind `blueshare_core.h` and a
real `blueshare_test` constitutional executable. Keep the existing standalone
demos separate. Once that API has deterministic lifecycle, topology, distance,
and stale-state tests, expose it through one service boundary before starting a
desktop or Android shell.
