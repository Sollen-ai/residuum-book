"""Fernández-Huerta readability for Spanish prose.

The syllable counter is ported from ``~/hanskellsen_docs/flesch_kincaid.py``
(the series' readability tool, Spanish branch: ``_spanish_vowel_chars`` and
``syllables_es``), so this book is scored the same way as the HAnSKELLsen
monograph. It is copied, not imported, so the build does not depend on that
path.

The score follows the same tool: ``206.84 - 60 * (syllables / words) -
1.02 * (words / sentences)``. ``plain-language.yaml`` names the formula
(``readability.formula: fernandez-huerta``) and says it is reported, never
failing.
"""

from __future__ import annotations

import re

STRONG = set("aeoáéó")
WEAK = set("iuüíú")
SPANISH_VOWELS = set("aeiouáéíóúü")
DIPHTHONG_SECOND = set("iue")  # unstressed weak after a vowel
LETTER_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]")

FORMULAS = {"fernandez-huerta": "Fernández-Huerta"}


def _spanish_vowel_chars(word: str) -> str:
    chars: list[str] = []
    for i, ch in enumerate(word.lower()):
        if ch == "h":
            continue
        if ch in SPANISH_VOWELS:
            chars.append(ch)
        elif ch == "y" and (i == len(word) - 1 or word[i + 1].lower() not in SPANISH_VOWELS):
            chars.append("i")
    return "".join(chars)


def syllables_es(word: str) -> int:
    """Spanish syllable count (ported from flesch_kincaid.py, unchanged)."""
    vowels = _spanish_vowel_chars(word)
    if not vowels:
        return 1 if LETTER_RE.search(word) else 0
    count = 0
    i = 0
    n = len(vowels)
    while i < n:
        count += 1
        a = vowels[i]
        if i + 1 < n:
            b = vowels[i + 1]
            hiatus = (
                a in STRONG and b in STRONG
                or a in "íú"
                or b in "íú"
            )
            if not hiatus and (b in WEAK or (a in WEAK and b in STRONG)):
                i += 1
                if i + 1 < n and vowels[i + 1] in DIPHTHONG_SECOND and vowels[i] in STRONG:
                    # triphthong: iái, uai, iai…
                    i += 1
        i += 1
    return max(1, count)


def fernandez_huerta(words: list[str], sentences: int) -> float | None:
    """Return the score, or None when there is too little text (< 10 words)."""
    words = [w for w in words if LETTER_RE.search(w)]
    if len(words) < 10 or sentences < 1:
        return None
    syllables = sum(syllables_es(w) for w in words)
    return round(206.84 - 60.0 * syllables / len(words) - 1.02 * len(words) / sentences, 1)
