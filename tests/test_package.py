import hashlib
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackageTests(unittest.TestCase):
    def test_package_resolves(self):
        load_script("validate_package").validate()

    def test_release_archives_are_complete_and_reproducible(self):
        builder = load_script("build_release")
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            outputs = builder.build(Path(first))
            repeats = builder.build(Path(second))
            for output, repeat in zip(outputs, repeats):
                self.assertEqual(output.read_bytes(), repeat.read_bytes())
                with zipfile.ZipFile(output) as archive:
                    names = archive.namelist()
                    self.assertEqual(len(names), len(set(names)))
                    self.assertFalse(any(".." in Path(n).parts for n in names))
                    self.assertFalse(any(n.startswith("/") for n in names))
                    self.assertFalse(any("__pycache__" in n or n.endswith(".pdf") for n in names))
                    prefix = "asd-ste100/" if output.name.startswith("asd-") else "skills/asd-ste100/"
                    self.assertEqual(
                        archive.read(prefix + "SKILL.md"),
                        (ROOT / "skills/asd-ste100/SKILL.md").read_bytes(),
                    )
                    for member in ("references/writing-guide.md", "references/examples.md", "scripts/check_ste.py"):
                        self.assertIn(prefix + member, names)
                    if output.name.startswith("asd-"):
                        self.assertTrue(all(n.startswith("asd-ste100/") for n in names))
                        self.assertIn("asd-ste100/LICENSE", names)
                    else:
                        self.assertIn("plugin.json", names)
                        self.assertIn(".claude-plugin/plugin.json", names)
                        self.assertIn(".agents/plugins/marketplace.json", names)
                        self.assertIn("TESTING.md", names)
                        self.assertIn("evals/scenarios.md", names)
                        extracted = Path(first) / "extracted"
                        archive.extractall(extracted)
                        result = subprocess.run(
                            [sys.executable, "scripts/validate_package.py"],
                            cwd=extracted, capture_output=True, text=True,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
            sums = (Path(first) / "SHA256SUMS").read_text().splitlines()
            for output, line in zip(outputs, sums):
                digest, name = line.split("  ")
                self.assertEqual(name, output.name)
                self.assertEqual(digest, hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
