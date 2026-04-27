from dataclasses import dataclass
import math
from pathlib import Path
import re


HEADING_PATTERN = re.compile(r"^(#{1,4})\s+(.+?)\s*#*\s*$")
BLANK_LINES_PATTERN = re.compile(r"\n{3,}")
FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")
DETAILS_BLOCK_PATTERN = re.compile(r"<details>.*?</details>", re.DOTALL | re.IGNORECASE)
IMAGE_LINE_PATTERN = re.compile(r"^\s*!\[[^\]]*]\([^)]+\)\s*$")
NUMBERING_PREFIX_PATTERN = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
SPACED_WORD_PATTERN = re.compile(r"^(?:[A-Za-z]\s+){2,}[A-Za-z]$")
IGNORED_SECTION_HEADINGS = {
    "article info",
    "contents",
    "table of contents",
    "references",
    "bibliography",
    "acknowledgements",
    "acknowledgments",
}
ABSTRACT_HEADINGS = {"abstract", "摘要"}


@dataclass(frozen=True)
class MarkdownChunk:
    chunk_index: int
    heading_path: str
    heading_text: str | None
    content: str
    char_count: int
    token_estimate: int
    source_path: str


@dataclass(frozen=True)
class MarkdownSection:
    heading_path: list[str]
    heading_text: str | None
    content: str


def build_markdown_chunks(
    markdown_path: str | Path,
    *,
    target_chars: int = 1000,
    max_chars: int = 1600,
    overlap_chars: int = 200,
) -> list[MarkdownChunk]:
    path = Path(markdown_path).expanduser()
    text = path.read_text(encoding="utf-8", errors="replace")
    cleaned_text = clean_markdown_text(text)
    sections = filter_paper_sections(split_markdown_sections(cleaned_text))

    chunks: list[MarkdownChunk] = []
    for section in sections:
        section_chunks = split_section_into_chunks(
            section,
            source_path=str(path),
            start_index=len(chunks),
            target_chars=target_chars,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
        chunks.extend(section_chunks)

    return chunks


def clean_markdown_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    without_details = DETAILS_BLOCK_PATTERN.sub("", normalized)
    lines = [
        line.rstrip()
        for line in without_details.split("\n")
        if not IMAGE_LINE_PATTERN.match(line)
    ]
    compacted = BLANK_LINES_PATTERN.sub("\n\n", "\n".join(lines))
    return compacted.strip()


def split_markdown_sections(text: str) -> list[MarkdownSection]:
    if not text:
        return []

    sections: list[MarkdownSection] = []
    heading_stack: list[str] = []
    current_lines: list[str] = []
    current_path: list[str] = []
    current_heading: str | None = None
    in_code_fence = False

    def flush_current() -> None:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(
                MarkdownSection(
                    heading_path=current_path.copy(),
                    heading_text=current_heading,
                    content=content,
                )
            )

    for line in text.split("\n"):
        if FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence

        heading_match = HEADING_PATTERN.match(line) if not in_code_fence else None
        if heading_match:
            flush_current()
            level = len(heading_match.group(1))
            heading_text = normalize_heading_text(heading_match.group(2))
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(heading_text)
            current_path = heading_stack.copy()
            current_heading = heading_text
            current_lines = [f"{heading_match.group(1)} {heading_text}"]
            continue

        current_lines.append(line)

    flush_current()
    return sections


def filter_paper_sections(sections: list[MarkdownSection]) -> list[MarkdownSection]:
    if not sections:
        return []

    abstract_index = next(
        (
            index
            for index, section in enumerate(sections)
            if section_heading_key(section) in ABSTRACT_HEADINGS
        ),
        None,
    )
    candidate_sections = sections[abstract_index:] if abstract_index is not None else sections

    filtered_sections: list[MarkdownSection] = []
    for section in candidate_sections:
        heading_key = section_heading_key(section)
        if heading_key in IGNORED_SECTION_HEADINGS:
            continue
        filtered_sections.append(section)

    return filtered_sections


def split_section_into_chunks(
    section: MarkdownSection,
    *,
    source_path: str,
    start_index: int,
    target_chars: int,
    max_chars: int,
    overlap_chars: int,
) -> list[MarkdownChunk]:
    if is_abstract_section(section) and len(section.content) <= max_chars:
        return [
            make_chunk(
                section=section,
                source_path=source_path,
                chunk_index=start_index,
                content=section.content,
            )
        ]

    paragraphs = split_paragraphs(section.content)
    chunks: list[MarkdownChunk] = []
    current_parts: list[str] = []

    def current_text() -> str:
        return join_parts(current_parts)

    def append_chunk(content: str) -> None:
        stripped = content.strip()
        if not stripped:
            return

        chunks.append(
            make_chunk(
                section=section,
                source_path=source_path,
                chunk_index=start_index + len(chunks),
                content=stripped,
            )
        )

    def flush_current() -> None:
        nonlocal current_parts
        append_chunk(current_text())
        current_parts = []

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current_parts:
                flush_current()

            for segment in hard_split_text(paragraph, max_chars, overlap_chars):
                append_chunk(segment)
            continue

        candidate = join_parts([*current_parts, paragraph])
        if current_parts and len(candidate) > max_chars:
            previous = current_text()
            flush_current()
            overlap = tail_overlap(previous, overlap_chars)
            current_parts = [overlap, paragraph] if overlap else [paragraph]
            continue

        if current_parts and len(current_text()) >= target_chars:
            previous = current_text()
            flush_current()
            overlap = tail_overlap(previous, overlap_chars)
            current_parts = [overlap, paragraph] if overlap else [paragraph]
            continue

        current_parts.append(paragraph)

    if current_parts:
        flush_current()

    return chunks


def split_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]


def make_chunk(
    *,
    section: MarkdownSection,
    source_path: str,
    chunk_index: int,
    content: str,
) -> MarkdownChunk:
    stripped = content.strip()
    return MarkdownChunk(
        chunk_index=chunk_index,
        heading_path=" > ".join(section.heading_path),
        heading_text=section.heading_text,
        content=stripped,
        char_count=len(stripped),
        token_estimate=estimate_tokens(stripped),
        source_path=source_path,
    )


def join_parts(parts: list[str]) -> str:
    return "\n\n".join(part for part in parts if part).strip()


def hard_split_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if max_chars <= 0:
        return [text]

    stride = max(max_chars - max(overlap_chars, 0), 1)
    segments: list[str] = []
    start = 0
    while start < len(text):
        segment = text[start : start + max_chars].strip()
        if segment:
            segments.append(segment)
        if start + max_chars >= len(text):
            break
        start += stride
    return segments


def tail_overlap(text: str, overlap_chars: int) -> str:
    if overlap_chars <= 0:
        return ""

    last_paragraph = text.split("\n\n")[-1].strip()
    if len(last_paragraph) <= overlap_chars:
        return last_paragraph
    return ""


def estimate_tokens(text: str) -> int:
    if not text:
        return 0

    return max(1, math.ceil(len(text) / 4))


def normalize_heading_text(text: str) -> str:
    stripped = text.strip()
    if SPACED_WORD_PATTERN.match(stripped):
        joined = stripped.replace(" ", "").lower()
        if joined == "abstract":
            return "Abstract"
        return joined
    return stripped


def section_heading_key(section: MarkdownSection) -> str:
    heading = section.heading_text or ""
    heading = normalize_heading_text(heading)
    heading = NUMBERING_PREFIX_PATTERN.sub("", heading)
    heading = re.sub(r"\s+", " ", heading).strip().lower()
    return heading


def is_abstract_section(section: MarkdownSection) -> bool:
    return section_heading_key(section) in ABSTRACT_HEADINGS
