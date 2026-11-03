"""Line-level TypeScript security checks."""

from __future__ import annotations

import re
from pathlib import Path

from desloppify.base.signal_patterns import SERVICE_ROLE_TOKEN_RE
from desloppify.languages.typescript.detectors.security.entries import _make_security_entry
from desloppify.languages.typescript.detectors.security.patterns import (
    _ATOB_JWT_RE,
    _CREATE_CLIENT_RE,
    _DANGEROUS_HTML_RE,
    _DEV_CRED_RE,
    _EVAL_PATTERNS,
    _INNER_HTML_RE,
    _JWT_PAYLOAD_RE,
    _OPEN_REDIRECT_RE,
)

# Sanitizer calls that make an HTML sink safe by construction.
_SANITIZER_CALL_RE = re.compile(
    r"(?:DOMPurify\.sanitize|sanitize[Hh]tml|sanitize|xss|purify)\s*\("
)
# __html operand capture: literal, call, or identifier.
_HTML_OPERAND_RE = re.compile(r"__html\s*:\s*(.+?)\s*[,}]")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_$][\w$]*$")
_COMMENT_PREFIX_RE = re.compile(r"^\s*(?://|\*|/\*)")


def _is_static_string_literal(expr: str) -> bool:
    """True when *expr* is a quoted literal with no ``${`` interpolation."""
    expr = expr.strip().rstrip(",)}")
    return (
        len(expr) >= 2
        and expr[0] in ("'", '"', "`")
        and expr[-1] == expr[0]
        and "${" not in expr
    )


def _identifier_is_static_literal(lines: list[str], ident: str) -> bool:
    """True when *ident* is defined in-file as a pure string literal.

    Covers the local-SVG pattern: ``const ICON = `<svg>...</svg>` `` feeding
    ``dangerouslySetInnerHTML={{ __html: ICON }}`` or ``el.innerHTML = ICON``.
    A ``${`` anywhere in the literal means interpolated data — not static.
    """
    pattern = re.compile(
        rf"\b(?:const|let|var)\s+{re.escape(ident)}\s*=\s*(['\"`])"
    )
    text = "\n".join(lines)
    match = pattern.search(text)
    if not match:
        return False
    quote = match.group(1)
    i = match.end()
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == quote:
            return "${" not in text[match.start() : i + 1]
        i += 1
    return False


def _html_sink_is_safe(lines: list[str], line: str) -> bool:
    """Whether an innerHTML/dangerouslySetInnerHTML use is safe on this line.

    Safe means: commented out, empty-literal clears (``__html: ''`` /
    ``innerHTML = ''``), sanitizer-wrapped values, or statically defined
    markup (inline literal or in-file literal constant with no interpolation).
    """
    if _COMMENT_PREFIX_RE.match(line):
        return True
    if _SANITIZER_CALL_RE.search(line):
        return True

    operand_match = _HTML_OPERAND_RE.search(line)
    if operand_match:
        operand = operand_match.group(1)
    else:
        assign = re.search(r"\.innerHTML\s*=\s*(.+?);?\s*$", line)
        operand = assign.group(1) if assign else ""
    if _is_static_string_literal(operand):
        return True
    if _IDENTIFIER_RE.match(operand.strip()):
        return _identifier_is_static_literal(lines, operand.strip())
    return False


def _line_security_issues(
    *,
    filepath: str,
    normalized_path: str,
    lines: list[str],
    line_num: int,
    line: str,
    is_server_only: bool,
    has_dev_guard: bool,
) -> list[dict[str, object]]:
    """Detect per-line security patterns and return issues."""
    line_issues: list[dict[str, object]] = []

    if _CREATE_CLIENT_RE.search(line):
        context = "\n".join(lines[max(0, line_num - 3) : min(len(lines), line_num + 3)])
        if SERVICE_ROLE_TOKEN_RE.search(context) and not is_server_only:
            line_issues.append(
                _make_security_entry(
                    filepath,
                    line_num,
                    line,
                    check_id="service_role_on_client",
                    summary="Supabase service role key used in client code",
                    severity="critical",
                    confidence="high",
                    remediation="Never use SERVICE_ROLE key outside server-only code - use anon key + RLS on clients",
                )
            )

    if _EVAL_PATTERNS.search(line):
        line_issues.append(
            _make_security_entry(
                filepath,
                line_num,
                line,
                check_id="eval_injection",
                summary="eval() or new Function() - potential code injection",
                severity="critical",
                confidence="high",
                remediation="Avoid eval/new Function - use safer alternatives (JSON.parse, Map, etc.)",
            )
        )

    if _DANGEROUS_HTML_RE.search(line) and not _html_sink_is_safe(lines, line):
        line_issues.append(
            _make_security_entry(
                filepath,
                line_num,
                line,
                check_id="dangerously_set_inner_html",
                summary="dangerouslySetInnerHTML - XSS risk if data is untrusted",
                severity="high",
                confidence="medium",
                remediation="Sanitize HTML with DOMPurify before using dangerouslySetInnerHTML",
            )
        )

    if _INNER_HTML_RE.search(line) and not _html_sink_is_safe(lines, line):
        line_issues.append(
            _make_security_entry(
                filepath,
                line_num,
                line,
                check_id="innerHTML_assignment",
                summary="Direct .innerHTML assignment - XSS risk",
                severity="high",
                confidence="medium",
                remediation="Use textContent for text or sanitize HTML with DOMPurify",
            )
        )

    if _DEV_CRED_RE.search(line):
        is_dev_file = "/dev/" in normalized_path or "dev." in Path(filepath).name
        if not (is_dev_file and has_dev_guard):
            line_issues.append(
                _make_security_entry(
                    filepath,
                    line_num,
                    line,
                    check_id="dev_credentials_env",
                    summary="Sensitive credential exposed via VITE_ environment variable",
                    severity="medium",
                    confidence="medium",
                    remediation="Sensitive credentials should never be in client-accessible VITE_ env vars",
                )
            )

    if _OPEN_REDIRECT_RE.search(line):
        line_issues.append(
            _make_security_entry(
                filepath,
                line_num,
                line,
                check_id="open_redirect",
                summary="Potential open redirect: user-controlled data assigned to window.location",
                severity="medium",
                confidence="medium",
                remediation="Validate redirect URLs against an allowlist before redirecting",
            )
        )

    if _ATOB_JWT_RE.search(line):
        context = "\n".join(lines[max(0, line_num - 3) : min(len(lines), line_num + 3)])
        if _JWT_PAYLOAD_RE.search(context):
            line_issues.append(
                _make_security_entry(
                    filepath,
                    line_num,
                    line,
                    check_id="unverified_jwt_decode",
                    summary="JWT decoded with atob() without signature verification",
                    severity="critical",
                    confidence="high",
                    remediation="Use auth.getUser() or a JWT library that verifies signatures",
                )
            )

    return line_issues


__all__ = ["_line_security_issues"]
