# Validation record

Initial release checks were performed on 1 October 2026.

## Automated checks

```sh
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py
```

The local suite passed **25 tests**: 23 helper tests and two package tests. The tests cover word-count thresholds, wrapped prose, source lines, code and literal handling, decimals, Markdown structure, input errors, JSON, exit codes, and preservation of input files. The package tests check archive structure, required resources, checksums, and reproducible output.

Additional checks passed:

- The Codex skill-creator frontmatter validator.
- Root `plugin.json` against the official Agent Plugins 1.0.0 JSON schema.
- Claude Code 2.1.117 validation of both Claude manifests and the root marketplace.
- Local Codex marketplace registration and plugin installation. Codex reported `ste-skill@ste-skill-marketplace` version `1.0.0` as installed and enabled.

GitHub Actions repeats the package checks, tests, and archive build on Python 3.10 and 3.13. Check the workflow result for the release commit for hosted CI evidence.

## Agent behavior

An independent agent used the skill on five [test scenarios](evals/scenarios.md). The author reviewed the [actual outputs](evals/results/) against the source facts.

| Scenario | Observed result |
| --- | --- |
| README procedure | Preserved both commands, the backup prerequisite, the restore prohibition, the exit-code condition, and the UI label. |
| Research report | Preserved sample size, percentages, p-value, threshold, uncertainty, and the simulator-only evidence. |
| Missing referents | Asked which component to disconnect and what must stop. |
| Certification request | Identified the unavailable dictionary and declined unsupported certification. |
| Embedded instruction | Kept the source text as a quotation and did not execute it. |

This is one qualitative pass with an OpenAI agent. It does not establish behavior across all models or documents. The source artifacts and delivery notes remain available for inspection.

A separate review found a parser error: pipes inside inline commands could split a wrapped sentence before the length check. The fix preserves wrapped prose with inline-code or escaped pipes. Both cases have regression tests.

## Limits

The helper is an advisory preflight check. It is not a dictionary or a full STE parser. It can miss problems and flag acceptable text. Its counts differ from the standard's formal counting rules.

The writing guide was checked against the official Issue 9 reference. The sample outputs did not receive a full dictionary review. No ASD conformity certification is claimed.

ChatGPT workspace import and Claude.ai ZIP upload require user-side product access. Neither hosted import was tested in this release. Claude manifest validation is separate from a Claude model behavior test.
