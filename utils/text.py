import re

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Common emoji / symbol ranges that render as double-width in most terminals.
_WIDE_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "]"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    return _ANSI_RE.sub("", text)


def visible_width(text: str) -> int:
    """
    Compute the on-screen column width of a string, ignoring ANSI escape
    codes and treating common emoji as double-width (as most terminals
    render them). Using len() directly on strings containing emoji or
    ANSI codes produces misaligned boxes/tables - this fixes that.
    """
    plain = strip_ansi(text)
    width = 0
    for ch in plain:
        width += 2 if _WIDE_RE.match(ch) else 1
    return width


def pad_right(text: str, target_width: int) -> str:
    """Pad a (possibly ANSI/emoji-containing) string with spaces so its
    visible width matches target_width."""
    padding = max(0, target_width - visible_width(text))
    return text + (" " * padding)
