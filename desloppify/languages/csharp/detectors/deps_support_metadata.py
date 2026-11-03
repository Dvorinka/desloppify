"""Source-file metadata parsing helpers for C# dependency graph building."""

from __future__ import annotations

import re
from pathlib import Path

from desloppify.base.discovery.file_paths import rel, resolve_path

_USING_RE = re.compile(
    r"(?m)^\s*(?:global\s+)?using\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;"
)
_USING_ALIAS_RE = re.compile(
    r"(?m)^\s*(?:global\s+)?using\s+[A-Za-z_]\w*\s*=\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;"
)
_USING_STATIC_RE = re.compile(
    r"(?m)^\s*(?:global\s+)?using\s+static\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;"
)
_NAMESPACE_RE = re.compile(
    r"(?m)^\s*namespace\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*(?:;|\{)"
)
_NON_CODE_RE = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/'
    r'|(?P<raw_quotes>"{3,})[\s\S]*?(?P=raw_quotes)'
    r'|@"(?:""|[^"])*"'
    r'|"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
)
_TYPE_DECLARATION_RE = re.compile(
    r"\b(?:class|struct|interface|enum|record(?:\s+(?:class|struct))?)\s+"
    r"@?([A-Za-z_]\w*)"
)
_EXTENSION_METHOD_RE = re.compile(
    r"\b([A-Za-z_]\w*)\s*(?:<[^{}();]+>)?\s*\(\s*this\b"
)
_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_QUALIFIED_REF_RE = re.compile(r"\b(?:[A-Z]\w*\.)+[A-Z]\w*\b")
_MAIN_METHOD_RE = re.compile(r"(?m)\bstatic\s+(?:async\s+)?(?:void|int)\s+Main\s*\(")
_MAUI_APP_FACTORY_RE = re.compile(r"(?m)\bCreateMauiApp\s*\(")
_PLATFORM_BASE_RE = re.compile(
    r"(?m)^\s*(?:public\s+)?(?:partial\s+)?class\s+\w+\s*:\s*"
    r".*\b(?:MauiUIApplicationDelegate|UIApplicationDelegate|UISceneDelegate|MauiWinUIApplication)\b"
)
_PLATFORM_REGISTER_RE = re.compile(r'(?m)\[Register\("AppDelegate"\)\]')

_ENTRY_FILE_HINTS = {
    "Program.cs",
    "Startup.cs",
    "Main.cs",
    "MauiProgram.cs",
    "MainActivity.cs",
    "AppDelegate.cs",
    "SceneDelegate.cs",
    "WinUIApplication.cs",
    "App.xaml.cs",
}
_ENTRY_PATH_HINTS = (
    "/Platforms/Android/",
    "/Platforms/iOS/",
    "/Platforms/MacCatalyst/",
    "/Platforms/Windows/",
)


def is_entrypoint_file(filepath: Path, content: str) -> bool:
    """Best-effort bootstrap detection for app delegates and platform entry files."""
    rel_path = rel(str(filepath)).replace("\\", "/")
    if filepath.name in _ENTRY_FILE_HINTS:
        return True
    is_platform_path = any(hint in rel_path for hint in _ENTRY_PATH_HINTS)
    if is_platform_path and (
        _PLATFORM_BASE_RE.search(content) or _PLATFORM_REGISTER_RE.search(content)
    ):
        return True
    if _MAIN_METHOD_RE.search(content):
        return True
    if _MAUI_APP_FACTORY_RE.search(content):
        return True
    if _PLATFORM_BASE_RE.search(content):
        return True
    if _PLATFORM_REGISTER_RE.search(content):
        return True
    return False


def parse_file_metadata(filepath: str) -> tuple[str | None, set[str], bool]:
    """Return (namespace, using_namespaces, is_entrypoint) for one C# file."""
    abs_path = Path(resolve_path(filepath))
    try:
        content = abs_path.read_text()
    except (OSError, UnicodeDecodeError):
        return None, set(), False

    namespace = None
    ns_match = _NAMESPACE_RE.search(content)
    if ns_match:
        namespace = ns_match.group(1)

    usings: set[str] = set()
    usings.update(_USING_RE.findall(content))
    usings.update(_USING_ALIAS_RE.findall(content))
    usings.update(_USING_STATIC_RE.findall(content))
    return namespace, usings, is_entrypoint_file(abs_path, content)


def parse_file_symbols(filepath: str) -> tuple[set[str], set[str], set[str], set[str]]:
    """Return declared types, reference identifiers, extension method names
    and PascalCase qualified references (``Ns.Type`` or longer).

    Qualified references capture fully-qualified type usage that needs no
    ``using`` — e.g. ``Foo.Bar.Baz.Create()`` — which the dependency graph
    otherwise cannot see (#683). This remains lexical rather than full
    symbol binding.
    """
    try:
        content = Path(resolve_path(filepath)).read_text()
    except (OSError, UnicodeDecodeError):
        return set(), set(), set(), set()
    code = _NON_CODE_RE.sub(" ", content)
    references = _NAMESPACE_RE.sub(" ", code)
    for pattern in (_USING_RE, _USING_ALIAS_RE, _USING_STATIC_RE):
        references = pattern.sub(" ", references)
    return (
        set(_TYPE_DECLARATION_RE.findall(code)),
        set(_IDENTIFIER_RE.findall(references)),
        set(_EXTENSION_METHOD_RE.findall(code)),
        set(_QUALIFIED_REF_RE.findall(references)),
    )


_MEMBER_DECL_RE = re.compile(
    r"\b(?:public|internal|protected|private)\s+"
    r"(?:(?:static|readonly|sealed|virtual|override|new|required|abstract)\s+)*"
    r"([A-Z]\w*)\s+([A-Za-z_]\w*)\s*(?:\{|=|;)"
)
_VAR_NEW_RE = re.compile(
    r"\b(?:var\s+([A-Za-z_]\w*)\s*=|([A-Z]\w*)\s+([A-Za-z_]\w*)\s*=)\s*new\s+([A-Z]\w*)"
)


def parse_member_bindings(
    filepath: str,
) -> tuple[dict[str, set[str]], dict[str, str], dict[str, set[str]]]:
    """Return (member_types, var_types, member_accesses) for receiver binding.

    ``member_types`` maps a declared member name to the type names it returns
    (``public Inventory Items { get; }`` -> ``{"Items": {"Inventory"}}``).
    ``var_types`` maps a local to its constructed type (``var s = new Store()``
    or ``Store s = new()``).  ``member_accesses`` maps such a local to the
    member names touched on it (``store.Items.Add(...)`` -> ``{"Items"}``).

    Together they bind ``store.Items.Add`` to ``Inventory`` — a direct type
    dependency the identifier-level fallback cannot see (#893).  Lexical,
    not semantic: name collisions resolve to more candidate targets, never
    fewer.
    """
    try:
        content = Path(resolve_path(filepath)).read_text()
    except (OSError, UnicodeDecodeError):
        return {}, {}, {}
    code = _NON_CODE_RE.sub(" ", content)

    member_types: dict[str, set[str]] = {}
    for type_name, member_name in _MEMBER_DECL_RE.findall(code):
        member_types.setdefault(member_name, set()).add(type_name)

    var_types: dict[str, str] = {}
    for var_name, _decl_type, explicit_var, new_type in _VAR_NEW_RE.findall(code):
        var_types[var_name or explicit_var] = new_type

    member_accesses: dict[str, set[str]] = {}
    for var_name in var_types:
        member_accesses[var_name] = set(
            re.findall(rf"\b{re.escape(var_name)}\.([A-Za-z_]\w*)\b", code)
        )

    return member_types, var_types, member_accesses


def expand_namespace_matches(
    using_ns: str,
    namespace_to_files: dict[str, set[str]],
) -> set[str]:
    """Resolve one using namespace to candidate target files."""
    out: set[str] = set()
    for namespace, files in namespace_to_files.items():
        if (
            namespace == using_ns
            or namespace.startswith(using_ns + ".")
            or using_ns.startswith(namespace + ".")
        ):
            out.update(files)
    return out
