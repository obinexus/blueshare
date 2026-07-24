# BlueShare GitHub automation

This directory packages and publishes the static BlueShare article to GitHub Pages. It does not deploy the Windows peer service; GitHub Pages can host only the generated HTML, CSS, images, downloads, and other static files.

## Modules

| File | Responsibility |
| --- | --- |
| `workflows/pages.yml` | Builds and deploys the Pages artifact after relevant changes reach `main`, or when run manually. |
| `actions/build-pages/action.yml` | Reusable local action that tests, builds, and verifies the artifact. |
| `workflows/pruning-ci.yml` | Existing graph-pruning verification; it remains independent of Pages. |

The local action deliberately reuses `.gitlab/scripts/package_pages.py`. GitLab and GitHub therefore render the same source article and enforce the same asset checks. GitLab builds a `/blueshare` subdirectory for `www.obinexus.org`; GitHub uploads the article at the artifact root because GitHub already mounts the project at `/blueshare/`.

## First deployment

The workflow requests Pages enablement with `enablement: true`. GitHub's configure-pages action does not permit first-time enablement with the workflow's default `GITHUB_TOKEN`, so choose one of these setup paths:

### Option A: enable Pages in the UI

1. Open **Settings > Pages > Build and deployment** in `https://github.com/obinexus/blueshare`.
2. Set **Source** to **GitHub Actions** and save it.
3. Push the workflow change to `main`, or rerun **Actions > Publish BlueShare to GitHub Pages**.

### Option B: allow automatic enablement

1. Create a fine-grained personal access token for this repository with Pages write permission, or another token satisfying GitHub's configure-pages enablement requirements.
2. Save it under **Settings > Secrets and variables > Actions** as the repository secret `PAGES_ENABLEMENT_TOKEN`.
3. Push the workflow change to `main`, or rerun **Actions > Publish BlueShare to GitHub Pages**.

The workflow uses `PAGES_ENABLEMENT_TOKEN` when it exists and otherwise falls back to `GITHUB_TOKEN` for repositories already enabled through the UI. After deployment succeeds, open `https://obinexus.github.io/blueshare/`.

GitHub creates the `github-pages` deployment environment automatically. Keep its deployment branch protection restricted to `main`. If both setup paths are rejected, an administrator must allow Pages at the organization level before the workflow can continue.

## Test the site locally

From the repository root on Windows PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m unittest discover -s .gitlab/tests -v
python .gitlab/scripts/package_pages.py `
  --output _site `
  --base-path / `
  --canonical-url https://obinexus.github.io/blueshare/
python .gitlab/scripts/package_pages.py `
  --output _site `
  --base-path / `
  --verify-only
python -m http.server 8080 --directory _site
```

Then visit `http://127.0.0.1:8080/`. Stop the local server with `Ctrl+C`. The generated `_site/` directory is ignored by Git.

## Custom domain later

Do not add a `CNAME` file until the DNS owner has chosen the final hostname. To serve this Pages deployment from `www.obinexus.org` or another subdomain, configure that domain in **Settings > Pages**, update its DNS records, and then change the workflow's `canonical-url`. GitHub's Pages settings—not a repository `CNAME` file alone—activate the custom domain.
