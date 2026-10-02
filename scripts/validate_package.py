#!/usr/bin/env python3
"""Check this repository's package invariants; not an ASD-STE100 validator."""

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    def read_json(path):
        return json.loads((root / path).read_text(encoding="utf-8"))

    portable = read_json("plugin.json")
    assert portable["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert portable["name"] == "ste-skill"
    assert re.fullmatch(r"\d+\.\d+\.\d+", portable["version"])
    for path in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
        manifest = read_json(path)
        assert manifest["name"] == portable["name"], path
        assert manifest["version"] == portable["version"], path
    codex = read_json(".codex-plugin/plugin.json")
    assert codex["skills"] == "./skills/"
    for path in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
        marketplace = read_json(path)
        assert len(marketplace["plugins"]) == 1, path
        entry = marketplace["plugins"][0]
        assert entry["name"] == portable["name"], path
        source = entry["source"]
        local = source["path"] if isinstance(source, dict) else source
        assert local == "./", path
        assert (root / local / "plugin.json").is_file(), path

    skill = root / "skills/asd-ste100"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    # This package deliberately uses only single-line string fields.
    assert text.startswith("---\n")
    header = text.split("---", 2)[1].strip()
    fields = dict(line.split(": ", 1) for line in header.splitlines())
    assert set(fields) == {"name", "description", "license"}
    assert fields["name"] == skill.name
    assert 1 <= len(fields["description"]) <= 200
    assert fields["license"] == "MIT"
    assert "TODO" not in text and "[INSERT" not in text
    for page in skill.rglob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            target_path = (page.parent / target.split("#")[0]).resolve()
            assert target_path.is_relative_to(skill.resolve()), (page, target)
            assert target_path.is_file(), (page, target)
    assert (skill / "scripts/check_ste.py").is_file()
    assert (skill / "agents/openai.yaml").is_file()


if __name__ == "__main__":
    validate()
    print("Package invariants passed. This is not an STE conformity assessment.")
