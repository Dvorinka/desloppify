"""Bash/Shell language plugin — shellcheck."""

from desloppify.languages._framework.generic_support.core import generic_lang
from desloppify.languages._framework.treesitter import BASH_SPEC

generic_lang(
    name="bash",
    extensions=[".sh", ".bash"],
    tools=[
        {
            "label": "shellcheck",
            # One file per invocation: multi-file shellcheck crashes silently
            # on some platforms (#806); -print0/-0 keeps whitespace paths safe.
            "cmd": "find . \\( -name '*.sh' -o -name '*.bash' \\) -print0 | xargs -0 -n 1 shellcheck -f gcc 2>/dev/null",
            "fmt": "gnu",
            "id": "shellcheck_warning",
            "tier": 2,
            "fix_cmd": None,
        },
    ],
    depth="shallow",
    treesitter_spec=BASH_SPEC,
)

__all__ = [
    "generic_lang",
    "BASH_SPEC",
]
