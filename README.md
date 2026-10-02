# STE Documentation

Write clear documentation with **ASD-STE100 Simplified Technical English** guidance in ChatGPT, Codex, and Claude.

The skill helps an agent draft, edit, and review manuals, README files, procedures, reports, and help text. It preserves technical meaning, exact commands, UI labels, quantities, conditions, and evidence limits.

This independent project targets **Issue 9 (15 January 2025)**. It includes original guidance and a small review helper. It does not include the official standard or dictionary. A full conformity review needs the relevant standard, dictionary, and technical-term checks. The project does not claim ASD approval or certification. See the [official overview](https://www.asd-ste100.org/about_STE.html) and [software guidance](https://www.asd-ste100.org/STEsoftware.html).

## Install

### ChatGPT

For a workspace with GitHub plugin import, an admin can:

1. Open **Admin → Plugins → Add → Import marketplace**.
2. Set **Source** to `https://github.com/MarcoDotIO/ste-skill`.
3. Leave **Path** empty. Select `v1.0.0` to use this release, or `main` to receive updates.
4. Import the marketplace and review the result.
5. Make the plugin available to the intended users. Install it, then start a new chat.

Select **STE Documentation** with an `@` mention and give it a document task. GitHub publication and workspace import are separate steps. Availability depends on the workspace. See [OpenAI's import guide](https://learn.chatgpt.com/docs/enterprise/plugin-management).

### Codex

With a CLI that supports plugin commands:

```sh
codex plugin marketplace add MarcoDotIO/ste-skill --ref v1.0.0
codex plugin add ste-skill@ste-skill-marketplace
```

Start a new session, then invoke `$asd-ste100`. You can also install the plugin from its marketplace in the desktop app. See [OpenAI's plugin guide](https://developers.openai.com/plugins/build/plugins).

For a skill-only installation, copy `skills/asd-ste100/` from this repository into your user skill directory, such as `~/.codex/skills/asd-ste100/`. Preserve an existing installation before replacing it.

### Claude Code

```sh
claude plugin marketplace add MarcoDotIO/ste-skill
claude plugin install ste-skill@ste-skill
```

Start a new session and invoke `/ste-skill:asd-ste100`. To test a local checkout, start `claude --plugin-dir /path/to/ste-skill`. See the [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference).

### Claude.ai

Download `asd-ste100-1.0.0.zip` from the [release page](https://github.com/MarcoDotIO/ste-skill/releases/latest). In **Customize → Skills**, select **+ Create skill → Upload a skill**. Upload the ZIP and enable the skill. The archive contains one `asd-ste100/` folder with `SKILL.md` and its resources. See [Claude's custom skill guide](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).

## Use

Example prompts:

> Use the ASD-STE100 skill for all documentation you create or change in this task. Preserve code, commands, identifiers, and technical meaning.

> Rewrite this installation guide in Simplified Technical English. Keep the existing headings and exact command examples.

> Review this report against ASD-STE100 Issue 9. Identify changes in meaning, uncertain terms, and checks that need the official dictionary.

For full rule and vocabulary review, provide an authorized copy of the required standard and any approved domain terminology. The agent must distinguish verified terms from unresolved ones. Without the full reference, it delivers an STE-oriented draft and identifies the outstanding review.

The skill can be selected automatically for matching document tasks. Installation does not force every answer into STE. Set the scope in your prompt or your own project instructions when you want that behavior throughout a task.

## Optional prose check

Python 3.10 or later is sufficient. No Python packages or API keys are needed.

```sh
python3 skills/asd-ste100/scripts/check_ste.py document.md --mode procedure
python3 skills/asd-ste100/scripts/check_ste.py report.md --mode description --json
```

The helper flags long sentences, likely contractions, and possible passive constructions in text or Markdown. Counts are approximate. Code blocks, headings, comments, and frontmatter are excluded. Inline literals receive special handling. Review mixed documents section by section.

The helper does not verify dictionary meanings, technical-term eligibility, complete grammar, or technical accuracy. Its tokenizer does not implement the standard's full word-count rules. An empty finding list means only that these limited checks found no candidates.

Exit codes: `0` means no candidates; `1` means review candidates; `2` means an input error. The helper does not change files or send document content over the network.

## Test and build

```sh
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py
```

The build produces two reproducible ZIP files and `SHA256SUMS` in `dist/`:

- `ste-skill-1.0.0.zip`: plugin manifests and the shared skill.
- `asd-ste100-1.0.0.zip`: the standalone skill for Claude.ai or manual installation.

See [TESTING.md](TESTING.md) for the behavior tests and validation limits. GitHub Actions runs package checks and unit tests on Python 3.10 and 3.13. Packaging tests do not establish ASD-STE100 conformity or hosted product installation.

## Package layout

```text
plugin.json                         Portable Agent Plugins manifest
.codex-plugin/plugin.json           Codex compatibility manifest
.agents/plugins/marketplace.json    ChatGPT/Codex marketplace
.claude-plugin/                     Claude plugin and marketplace manifests
skills/asd-ste100/                  Shared skill, references, and helper
scripts/                           Package checks and archive builder
tests/                             Helper and packaging tests
```

The [MIT license](LICENSE) covers this project's original material. The ASD-STE100 standard and dictionary have their own rights and are not redistributed here. The skill works without an MCP server, external account connection, or background hook.
