#!/usr/bin/env python3
"""Find a small set of prose-review candidates with the Python standard library.

This is NOT a full ASD-STE100 or dictionary compliance checker. Counts are
approximate, not the standard's formal counting rules. An empty result does not
establish conformance. This program never changes the input.

The Markdown reader joins wrapped paragraph lines and treats list items and
table cells separately. It ignores fenced code, leading YAML frontmatter,
headings, HTML comments, and reference-link definitions. Inline code and URLs
count as approximately one token. Link labels count; destinations do not.
Quoted UI labels remain ordinary prose: use backticks to mark exact literals.

Limitations: this is not a complete Markdown, grammar, or sentence parser.
Nested lists, HTML, unusual abbreviations, complex links, and multiline code
spans can be interpreted imperfectly. Passive-voice guesses can flag adjectives
and miss real passives. Vocabulary, approved meanings, technical terms,
paragraph structure, safety, completeness, and factual accuracy need review.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Iterator, Sequence


NOTICE = (
    "Advisory only: NOT a full ASD-STE100 or dictionary compliance check. "
    "No findings does not establish conformance."
)
LIMITS = {"procedure": 20, "description": 25}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    code: str
    message: str
    excerpt: str


@dataclass
class MappedText:
    text: str
    lines: list[int]

    def replace(self, pattern: re.Pattern[str], replacement) -> None:
        """Replace matches while retaining the source line of each character."""
        pieces: list[str] = []
        source_lines: list[int] = []
        last = 0
        for match in pattern.finditer(self.text):
            pieces.append(self.text[last : match.start()])
            source_lines.extend(self.lines[last : match.start()])
            value = replacement(match)
            pieces.append(value)
            source_lines.extend([self.lines[match.start()]] * len(value))
            last = match.end()
        pieces.append(self.text[last:])
        source_lines.extend(self.lines[last:])
        self.text = "".join(pieces)
        self.lines = source_lines


_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
_HEADING = re.compile(r"^\s{0,3}#{1,6}(?:\s|$)")
_SETEXT = re.compile(r"^\s{0,3}(?:=+|-+)\s*$")
_RULE = re.compile(r"^\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")
_LIST = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(?:\[[ xX]\]\s+)?")
_REFERENCE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s+")
_INLINE_CODE = re.compile(r"(?<!`)(?P<fence>`+)(?P<body>.*?)(?P=fence)(?!`)")
_INLINE_LINK = re.compile(r"!?\[([^\]\n]+)\]\((?:[^()\n\\]|\\.|\([^()\n]*\))*\)")
_REFERENCE_LINK = re.compile(r"!?\[([^\]\n]+)\]\[[^\]\n]*\]")
_URL = re.compile(r"<?https?://[^\s<>\"']*[^\s<>\"'.,!?;:]>?")
_WORDS = re.compile(r"\b[vV]?\d+(?:[.,]\d+)+\b|\b\w+(?:[-'’]\w+)*\b", re.UNICODE)
_CONTRACTION = re.compile(
    r"\b(?:\w+n['’]t|(?:i|you|he|she|it|we|they|who|what|that|there)"
    r"['’](?:re|ve|ll|d|m)|(?:it|that|what|who|there|here|where|how|let)['’]s)\b",
    re.IGNORECASE,
)
_PASSIVE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being)\s+"
    r"(?:(?:not|\w+ly)\s+){0,2}"
    r"(?:\w{3,}ed|built|broken|chosen|done|driven|found|given|held|kept|known|"
    r"left|made|put|read|seen|sent|set|shown|shut|taken|told|written)\b",
    re.IGNORECASE,
)
_SENTENCE_END = re.compile(r"[.!?]+[\"”’')\]]*(?=\s|$)")
_ABBREVIATIONS = {"e.g.", "i.e.", "mr.", "mrs.", "ms.", "dr.", "fig.", "no.", "vs."}


def _has_table_pipe(line: str) -> bool:
    """Find a pipe outside code and Markdown escapes before paragraph splitting."""
    without_code = _INLINE_CODE.sub("", line)
    # Consume backslash escapes in pairs: \| is literal, but \\| contains a
    # literal backslash followed by a possible table delimiter.
    return any(match.group(0) == "|" for match in re.finditer(r"\\.|[|]", without_code))


def _without_comments(lines: list[str]) -> list[str]:
    in_comment = False
    fence_character = ""
    fence_length = 0
    output = []
    for line in lines:
        fence = _FENCE.match(line)
        if fence_character:
            output.append(line)
            if fence and fence.group(1)[0] == fence_character and len(fence.group(1)) >= fence_length and not fence.group(2).strip():
                fence_character = ""
            continue
        if not in_comment and fence:
            fence_character = fence.group(1)[0]
            fence_length = len(fence.group(1))
            output.append(line)
            continue
        result = []
        position = 0
        while position < len(line):
            if in_comment:
                end = line.find("-->", position)
                if end == -1:
                    break
                in_comment = False
                position = end + 3
            else:
                start = line.find("<!--", position)
                inline_code = _INLINE_CODE.search(line, position)
                if inline_code and (start == -1 or inline_code.start() < start):
                    result.append(line[position:inline_code.end()])
                    position = inline_code.end()
                    continue
                if start == -1:
                    result.append(line[position:])
                    break
                result.append(line[position:start])
                result.append(" ")
                position = start + 4
                in_comment = True
        output.append("".join(result))
    return output


def _paragraphs(text: str) -> Iterator[MappedText]:
    lines = _without_comments(text.lstrip("\ufeff").splitlines())
    frontmatter_end = -1
    if lines and lines[0].strip() == "---":
        # An unclosed delimiter is not silently treated as a whole-file header.
        for index, line in enumerate(lines[1:], 1):
            if line.strip() in {"---", "..."}:
                frontmatter_end = index
                break
    pending: list[str] = []
    pending_lines: list[int] = []
    fence_character = ""
    fence_length = 0

    def flush() -> MappedText | None:
        if not pending:
            return None
        paragraph = MappedText("".join(pending), pending_lines.copy())
        pending.clear()
        pending_lines.clear()
        return paragraph

    for index, original in enumerate(lines):
        line_number = index + 1
        if index <= frontmatter_end:
            continue
        fence = _FENCE.match(original)
        if fence_character:
            if fence and fence.group(1)[0] == fence_character and len(fence.group(1)) >= fence_length and not fence.group(2).strip():
                fence_character = ""
            continue
        if fence:
            paragraph = flush()
            if paragraph:
                yield paragraph
            fence_character = fence.group(1)[0]
            fence_length = len(fence.group(1))
            continue
        line = re.sub(r"^\s{0,3}(?:>\s*)+", "", original)
        setext_title = index + 1 < len(lines) and bool(_SETEXT.match(lines[index + 1]))
        ignored = _HEADING.match(line) or _RULE.match(line) or _SETEXT.match(line) or _REFERENCE.match(line)
        if setext_title and line.strip():
            # A setext heading can span the whole pending paragraph.
            pending.clear()
            pending_lines.clear()
            continue
        if not line.strip() or ignored:
            paragraph = flush()
            if paragraph:
                yield paragraph
            continue
        list_marker = _LIST.match(line)
        # Table rows remain separate. Cells are separated after code is protected.
        table_row = _has_table_pipe(line)
        if list_marker or table_row:
            paragraph = flush()
            if paragraph:
                yield paragraph
        if list_marker:
            line = line[list_marker.end():]
        line = line.strip()
        if pending:
            pending.append(" ")
            pending_lines.append(line_number)
        pending.append(line)
        pending_lines.extend([line_number] * len(line))
        if table_row:
            paragraph = flush()
            if paragraph:
                yield paragraph
    paragraph = flush()
    if paragraph:
        yield paragraph


def _prepare(paragraph: MappedText) -> tuple[MappedText, dict[str, str]]:
    literals: dict[str, str] = {}

    def protect(match: re.Match[str]) -> str:
        # A prefix absent from the source prevents collisions with user text.
        prefix = "STELITERAL"
        while prefix in paragraph.text:
            prefix += "X"
        token = f"{prefix}{len(literals)}TOKEN"
        literals[token] = match.group(0)
        return token

    paragraph.replace(_INLINE_CODE, protect)
    paragraph.replace(_INLINE_LINK, lambda match: match.group(1))
    paragraph.replace(_REFERENCE_LINK, lambda match: match.group(1))
    paragraph.replace(_URL, protect)
    # Markdown emphasis markers are not words. Underscores inside identifiers
    # remain part of the token, including when code delimiters are absent.
    paragraph.replace(re.compile(r"\*+|(?<!\w)_+|_+(?!\w)"), lambda match: "")
    return paragraph, literals


def _sentences(text: str) -> Iterator[tuple[int, int]]:
    start = 0
    for match in _SENTENCE_END.finditer(text):
        end = match.end()
        punctuation = match.group(0)
        if punctuation.startswith("."):
            previous = re.search(r"[\w.]+\.$", text[:match.start() + 1])
            if previous and (previous.group(0).lower() in _ABBREVIATIONS or re.fullmatch(r"[A-Za-z]\.", previous.group(0))):
                continue
        yield start, end
        start = end
    if text[start:].strip():
        yield start, len(text)


def check_text(text: str, path: str = "<text>", mode: str = "procedure") -> list[Finding]:
    """Return advisory findings; this API neither reads nor changes files."""
    if mode not in LIMITS:
        raise ValueError(f"Unknown mode: {mode}")
    findings: list[Finding] = []
    for paragraph in _paragraphs(text):
        paragraph, literals = _prepare(paragraph)
        # Escaped pipes are literal text; pipes in inline code are already hidden.
        for cell in re.finditer(r"(?:\\.|[^|])+", paragraph.text):
            if re.fullmatch(r"\s*:?-+:?\s*", cell.group(0)):
                continue
            for relative_start, relative_end in _sentences(cell.group(0)):
                start = cell.start() + relative_start
                end = cell.start() + relative_end
                while start < end and paragraph.text[start].isspace():
                    start += 1
                sentence = paragraph.text[start:end].strip()
                if not sentence:
                    continue
                excerpt = sentence
                for token, literal in literals.items():
                    excerpt = excerpt.replace(token, literal)
                excerpt = re.sub(r"\s+", " ", excerpt)
                word_count = len(_WORDS.findall(sentence))
                if word_count > LIMITS[mode]:
                    findings.append(Finding(path, paragraph.lines[start], "sentence-length", f"Approximately {word_count} words; review against the {LIMITS[mode]}-word {mode} limit. This is not the formal STE count.", excerpt))
                for contraction in _CONTRACTION.finditer(sentence):
                    findings.append(Finding(path, paragraph.lines[start + contraction.start()], "contraction", f"Possible contraction: {contraction.group(0)!r}. Review the prose; preserve exact literal labels.", excerpt))
                for passive in _PASSIVE.finditer(sentence):
                    findings.append(Finding(path, paragraph.lines[start + passive.start()], "possible-passive", f"Possible passive construction: {passive.group(0)!r}. Check the grammar and applicable writing rule; this can be an adjective.", excerpt))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=NOTICE, epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path, help="UTF-8 prose or Markdown files (no recursive directory scan)")
    parser.add_argument("--mode", choices=LIMITS, default="procedure", help="Approximate sentence limit: procedure=20 (default), description=25")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object, including the advisory notice and any input errors")
    args = parser.parse_args(argv)
    findings: list[Finding] = []
    errors: list[dict[str, str]] = []
    for path in args.paths:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append({"path": str(path), "message": str(error)})
            continue
        findings.extend(check_text(source, str(path), args.mode))
    if args.json:
        print(json.dumps({"notice": NOTICE, "mode": args.mode, "findings": [asdict(finding) for finding in findings], "errors": errors}, ensure_ascii=False, indent=2))
    else:
        print(NOTICE)
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.code}: {finding.message}\n  {finding.excerpt}")
        for error in errors:
            print(f"{error['path']}: input error: {error['message']}", file=sys.stderr)
        print(f"{len(findings)} review candidate(s); {len(errors)} input error(s).")
    return 2 if errors else 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
