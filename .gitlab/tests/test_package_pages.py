from __future__ import annotations

import importlib.util
import shutil
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".gitlab" / "scripts" / "package_pages.py"
SPEC = importlib.util.spec_from_file_location("package_pages", MODULE_PATH)
assert SPEC and SPEC.loader
package_pages = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package_pages)


class PackagePagesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output = ROOT / "tmp" / "gitlab-pages-test"
        if self.output.exists():
            shutil.rmtree(self.output)

    def tearDown(self) -> None:
        if self.output.exists():
            shutil.rmtree(self.output)

    def test_normalize_base_path(self) -> None:
        self.assertEqual(package_pages.normalize_base_path("blueshare/"), "/blueshare")
        self.assertEqual(package_pages.normalize_base_path("/"), "")
        with self.assertRaises(ValueError):
            package_pages.normalize_base_path("/../outside")

    def test_builds_complete_subpath_bundle(self) -> None:
        site = package_pages.build_site(
            self.output,
            "/blueshare",
            "https://www.obinexus.org/blueshare/",
        )
        package_pages.verify_bundle(self.output, "/blueshare")
        self.assertEqual(site, self.output / "blueshare")
        page = (site / "index.html").read_text(encoding="utf-8")
        self.assertIn('rel="canonical" href="https://www.obinexus.org/blueshare/"', page)
        self.assertIn("Provider boundary", page)
        self.assertIn("How I start BlueShare on Windows", page)
        self.assertNotIn("docs/blog/images/", page)
        root = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn("./blueshare/", root)

    def test_builds_article_at_artifact_root_for_github_pages(self) -> None:
        site = package_pages.build_site(
            self.output,
            "/",
            "https://obinexus.github.io/blueshare/",
        )
        package_pages.verify_bundle(self.output, "/")
        self.assertEqual(site, self.output)
        page = (site / "index.html").read_text(encoding="utf-8")
        self.assertIn("BlueShare - Sharing Moments Matters", page)
        self.assertIn(
            'rel="canonical" href="https://obinexus.github.io/blueshare/"',
            page,
        )
        self.assertNotIn("http-equiv=\"refresh\"", page)

    def test_refuses_repository_root_as_output(self) -> None:
        with self.assertRaises(ValueError):
            package_pages.output_path(ROOT)


if __name__ == "__main__":
    unittest.main()
