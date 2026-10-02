#!/usr/bin/env python3
"""Build reproducible plugin and standalone skill archives from an allowlist."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"__pycache__", ".DS_Store"}


def skill_files():
    for path in sorted((ROOT / "skills" / "asd-ste100").rglob("*")):
        if any(part in EXCLUDED for part in path.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing symlink: {path}")
        if path.is_file():
            yield path


def write_zip(destination, entries):
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    version = json.loads((ROOT / "plugin.json").read_text())["version"]
    files = list(skill_files())
    plugin_entries = [(p.relative_to(ROOT).as_posix(), p) for p in files]
    for name in (
        "plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json",
        "README.md", "LICENSE", "TESTING.md",
    ):
        plugin_entries.append((name, ROOT / name))
    for directory in ("scripts", "tests", "evals"):
        for path in sorted((ROOT / directory).rglob("*")):
            if any(part in EXCLUDED for part in path.parts) or path.suffix == ".pyc":
                continue
            if path.is_symlink():
                raise ValueError(f"Refusing symlink: {path}")
            if path.is_file():
                plugin_entries.append((path.relative_to(ROOT).as_posix(), path))
    skill_entries = [(p.relative_to(ROOT / "skills").as_posix(), p) for p in files]
    skill_entries.append(("asd-ste100/LICENSE", ROOT / "LICENSE"))
    archives = [
        (output / f"ste-skill-{version}.zip", plugin_entries),
        (output / f"asd-ste100-{version}.zip", skill_entries),
    ]
    lines = []
    for path, entries in archives:
        write_zip(path, entries)
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [path for path, _ in archives]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    for result in build(args.output):
        print(result)
