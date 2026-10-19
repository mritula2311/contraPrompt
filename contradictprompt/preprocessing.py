"""Offset-safe normalization; extraction always uses the untouched original."""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Normalized:
    text: str
    offsets: tuple[int, ...]

def normalize(prompt: str) -> Normalized:
    # Collapse whitespace only in a display/search copy, never in the executable text.
    chars, offsets = [], []
    for m in re.finditer(r'\S+|\s+', prompt):
        token = m.group()
        if token.isspace():
            if chars:
                chars.append(' '); offsets.append(m.start())
        else:
            chars.extend(token); offsets.extend(range(m.start(), m.end()))
    if chars and chars[-1] == ' ':
        chars.pop(); offsets.pop()
    return Normalized(''.join(chars), tuple(offsets))

def masked_quotes(text: str) -> str:
    # Quoted literals are data, not direct instruction verbs. Their offsets survive.
    return re.sub(r'"[^"]*"|‘[^’]*’|“[^”]*”|`[^`]*`',
                  lambda m: ' ' * len(m.group()), text, flags=re.DOTALL)
