"""C/C++ file discovery and function extraction scaffolds."""

from __future__ import annotations

import hashlib
from os import PathLike
import re
from pathlib import Path

from desloppify.base.discovery.file_paths import resolve_path
from desloppify.base.discovery.source import SourceDiscoveryOptions, find_source_files
from desloppify.engine.detectors.base import FunctionInfo
from desloppify.languages.cxx._parse_helpers import find_matching_brace

CXX_SOURCE_EXTENSIONS = (".c", ".cc", ".cpp", ".cxx")
CXX_HEADER_EXTENSIONS = (".h", ".hh", ".hpp", ".hxx", ".ipp", ".inl", ".tpp", ".txx", ".tcc")
CXX_EXTENSIONS = [*CXX_SOURCE_EXTENSIONS, *CXX_HEADER_EXTENSIONS]
CXX_FILE_EXCLUSIONS = [
    "build",
    "cmake-build-debug",
    "cmake-build-release",
    ".git",
    "node_modules",
]

_FUNC_DECL_RE = re.compile(
    r"(?:(?:^)|(?<=[;}\n]))\s*"
    r"(?:(?:inline|static|constexpr|virtual|explicit|friend|extern|typename)\s+)*"
    r"(?:[A-Za-z_~]\w*(?:::[A-Za-z_~]\w*)*(?:<[^;{}()]+>)?[\s*&]+)+"
    r"([A-Za-z_~]\w*(?:::[A-Za-z_~]\w*)*)\s*"
    r"\(([^()]*)\)\s*"
    r"(?:const\s*)?"
    r"(?:noexcept(?:\([^)]*\))?\s*)?"
    r"(?:->\s*[^;{]+)?"
    r"\{",
    re.MULTILINE,
)
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENT_LINE_RE = re.compile(r"//.*?$", re.MULTILINE)

# The decl regex can read `else if (cond) {` as `else` + named fn `if`
# (#903). Language keywords are never function names.
_CXX_NOT_FUNCTION_NAMES = frozenset({
    "if", "else", "for", "while", "do", "switch", "case", "default",
    "return", "sizeof", "decltype", "alignof", "static_assert", "catch",
    "try", "throw", "new", "delete", "and", "or", "not", "sizeof",
    "co_await", "co_yield", "co_return", "requires", "concept",
})

_CXX_QUALIFIER_WORDS = frozenset({
    "const", "volatile", "constexpr", "consteval", "constinit", "static",
    "mutable", "register", "inline", "typename", "class", "struct", "enum",
})


def find_cxx_files(path: Path | str) -> list[str]:
    """Find C/C++ source files under a path."""
    return find_source_files(
        path,
        CXX_EXTENSIONS,
        SourceDiscoveryOptions(exclusions=tuple(CXX_FILE_EXCLUSIONS)),
    )


def _split_params(param_str: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in param_str:
        if ch in ("<", "(", "[", "{"):
            depth += 1
        elif ch in (">", ")", "]", "}"):
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _extract_params(param_str: str) -> list[str]:
    """Return canonical parameter *types* for signature comparison.

    `Reason Reason`, `const Reason Reason` and an unnamed `Reason` are the
    same callable type (#903): the last identifier is the argument name
    when more than one token remains, and cv/ref/ptr qualifiers do not
    change the by-value signature.
    """
    params: list[str] = []
    for raw in _split_params(param_str):
        token = raw.strip().split("=")[0].strip()
        if not token or token == "void":
            continue
        token = token.replace("&&", " ").replace("&", " ").replace("*", " ")
        parts = [part for part in token.split() if part]
        parts = [part for part in parts if part not in _CXX_QUALIFIER_WORDS]
        if not parts:
            continue
        if len(parts) > 1 and re.fullmatch(r"[A-Za-z_]\w*", parts[-1]):
            parts = parts[:-1]
        param_type = " ".join(parts).replace(" ::", "::").replace(":: ", "::")
        if param_type:
            params.append(param_type)
    return params


def normalize_cxx_body(body: str) -> str:
    """Normalize a C/C++ function body for duplicate detection."""
    no_block_comments = _COMMENT_BLOCK_RE.sub("", body)
    no_comments = _COMMENT_LINE_RE.sub("", no_block_comments)
    lines = [line.strip() for line in no_comments.splitlines() if line.strip()]
    return "\n".join(lines)


def extract_cxx_functions(filepath: str) -> list[FunctionInfo]:
    """Extract C/C++ free and qualified function definitions from one file."""
    try:
        resolved = resolve_path(filepath)
        content = Path(resolved).read_text(errors="replace")
    except OSError:
        return []

    functions: list[FunctionInfo] = []
    for match in _FUNC_DECL_RE.finditer(content):
        qualified = match.group(1)
        leaf = qualified.split("::")[-1]
        if leaf in _CXX_NOT_FUNCTION_NAMES:
            continue
        # Keep the owner qualifier: A::EndPlay and B::EndPlay are distinct
        # member contracts (#903); bare names stay bare.
        name = qualified
        start = match.start()
        start_line = content.count("\n", 0, start) + 1
        open_pos = match.end() - 1
        end = find_matching_brace(content, open_pos)
        if end is None:
            continue

        end_line = content.count("\n", 0, end) + 1
        body = content[start : end + 1]
        normalized = normalize_cxx_body(body)
        functions.append(
            FunctionInfo(
                name=name,
                file=resolved,
                line=start_line,
                end_line=end_line,
                loc=max(1, end_line - start_line + 1),
                body=body,
                normalized=normalized,
                body_hash=hashlib.md5(
                    normalized.encode("utf-8"),
                    usedforsecurity=False,
                ).hexdigest(),
                params=_extract_params(match.group(2)),
            )
        )

    return functions


def extract_all_cxx_functions(
    path_or_files: Path | str | PathLike[str] | list[str]
 ) -> list[FunctionInfo]:
    """Extract C/C++ functions from either a scan root or an explicit file list."""
    if isinstance(path_or_files, (Path, str, PathLike)):
        file_list = find_cxx_files(Path(path_or_files))
    else:
        file_list = list(path_or_files)

    functions: list[FunctionInfo] = []
    for filepath in file_list:
        functions.extend(extract_cxx_functions(filepath))
    return functions
