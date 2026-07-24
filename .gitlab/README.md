# BlueShare GitLab Pages modules

This directory packages the first-person `README3.md` blog, its four screenshots,
and the generated PDF as a dependency-free static site. The intended production
address is:

`https://www.obinexus.org/blueshare/`

GitLab Pages serves static files only. It does not run
`packages/python/blueshare/peer_service.py`; that peer and media service still
runs on a trusted Windows host.

## Module map

| Module | Responsibility |
| --- | --- |
| `ci/quality.yml` | Compiles the packager and runs its standard-library test suite. |
| `ci/build-pages.yml` | Builds and verifies the `public/blueshare/` artifact. |
| `ci/deploy-pages.yml` | Publishes the verified `public/` artifact from the default branch. |
| `scripts/package_pages.py` | Converts `README3.md` to HTML and copies the PDF and screenshots. |
| `pages/site.css` | Responsive BlueShare web presentation. |
| `pages/favicon.svg` | Code-native BlueShare network mark. |
| `tests/test_package_pages.py` | Checks subpath routing, required assets, links, and safe output handling. |

The root `.gitlab-ci.yml` includes the three CI modules with `include:local`.

## Pipeline result

The build job creates:

```text
public/
├── index.html                 # forwards a dedicated Pages domain to /blueshare/
└── blueshare/
    ├── index.html             # rendered first-person blog
    ├── 404.html
    ├── manifest.webmanifest
    ├── deployment.json
    ├── assets/
    │   ├── site.css
    │   └── favicon.svg
    ├── images/                # the four supplied screenshots
    └── downloads/
        ├── README3.md
        └── blueshare-sharing-moments-matters.pdf
```

## Local build

From the repository root:

```powershell
python .gitlab/scripts/package_pages.py `
  --output tmp/gitlab-pages `
  --base-path /blueshare `
  --canonical-url https://www.obinexus.org/blueshare/

python -m http.server 8080 --directory tmp/gitlab-pages
```

Then open `http://127.0.0.1:8080/blueshare/`.

Run the same validation used by CI:

```powershell
python -m unittest discover -s .gitlab/tests -v
python .gitlab/scripts/package_pages.py `
  --verify-only `
  --output tmp/gitlab-pages `
  --base-path /blueshare
```

## GitLab project setup

1. Push the repository, including `.gitlab-ci.yml`, `.gitlab/`, `README3.md`,
   `docs/blog/images/`, and `output/pdf/`.
2. Confirm a GitLab Runner is enabled for the project.
3. Run a pipeline. Merge-request and branch pipelines validate and build the
   site; only the default branch publishes Pages.
4. In **Deploy > Pages**, confirm the default Pages deployment works.
5. Add `www.obinexus.org` as a custom Pages domain and follow the verification
   record shown by GitLab.
6. At the DNS provider, point the `www` CNAME to the Pages hostname shown by
   GitLab. DNS records target a hostname, never `/blueshare`.
7. Enable TLS and select `www.obinexus.org` as the primary domain after GitLab
   verifies it.

The artifact itself creates the `/blueshare/` directory, which is how the path
is served after the custom hostname resolves to this Pages deployment.

## Important ownership boundary

A custom Pages domain is attached to one Pages project and represents the whole
hostname. If `www.obinexus.org` is already deployed by another repository, do
not attach the same hostname to this project. Instead, run this packager in the
existing website pipeline and merge the generated `public/blueshare/` directory
into that website's publish artifact. The existing site must remain responsible
for its root `index.html`.

The variables in `.gitlab-ci.yml` can be overridden in a parent pipeline:

| Variable | Default |
| --- | --- |
| `BLUESHARE_PAGES_BASE_PATH` | `/blueshare` |
| `BLUESHARE_CANONICAL_URL` | `https://www.obinexus.org/blueshare/` |

The build is intentionally dependency-free beyond Python 3.12, so it can be
included in the main OBINexus site pipeline without adding a JavaScript package
installation step.
