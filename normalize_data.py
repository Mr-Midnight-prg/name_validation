import re
from ftfy import fix_text

CHAR_TO_REMOVE = [")", "(", ".", "|", "[", "]", "{", "}", "'", "!", ";"]

# ── Regex compilées pour la performance ──────────────────────────────────────

# Suffixes légaux entreprises (word boundary + fin de chaîne ou espace)
_LEGAL_SUFFIXES = [
    r"\bcorporation\b", r"\bcorp\b", r"\bholdings\b", r"\bholding\b",
    r"\bincorporated\b", r"\blimited\b", r"\bltd\b", r"\bllc\b", r"\bllp\b",
    r"\bcompanies\b", r"\bcompany\b", r"\bco\b", r"\binc\b",
    r"\bunited[\s\-]states\b", r"\bus\b", r"\binternational\b",
    r"\bpublic\s+co\b", r"\bplc\b",
    # Suffixes étrangers
    r"\bs\.a\.\b", r"\bsa\b", r"\bag\s*&\s*co\b", r"\bag\b",
    r"\bab\b", r"\bsab\b", r"\bpjsc\b", r"\boyj\b", r"\ba/s\b", r"\bnv\b",
    r"\btouchetohmatsu\b",
]
_LEGAL_RE = re.compile(
    r"(?i)\s*(?:" + "|".join(_LEGAL_SUFFIXES) + r")\s*"
)

_MFG_RE    = re.compile(r"(?i)\bmfg\.?\b")
_AMP_RE    = re.compile(r"&")
_MULTI_SP  = re.compile(r" +")
_BD_RE     = re.compile(r"[,\-./]|\sBD")
_DIGI_AL   = re.compile(r"(?<=\d)(?=[a-zA-Z])|(?<=[a-zA-Z])(?=\d)")

# Abréviations géographiques — ordre important : plus long en premier
_GEO_SUBS = [
    (re.compile(r"(?i)\bsaint\b"),  "saint"),   # déjà complet, pas de changement
    (re.compile(r"(?i)\bste\.\b"),  "saint"),
    (re.compile(r"(?i)\bste\b"),    "saint"),
    (re.compile(r"(?i)\bst\.\b"),   "saint"),
    (re.compile(r"(?i)\bst\b"),     "saint"),
    (re.compile(r"(?i)\bmount\b"),  "mount"),
    (re.compile(r"(?i)\bmt\.\b"),   "mount"),
    (re.compile(r"(?i)\bmt\b"),     "mount"),
    (re.compile(r"(?i)\bfort\b"),   "fort"),
    (re.compile(r"(?i)\bft\.\b"),   "fort"),    # ← corrigé : était 'saint'
    (re.compile(r"(?i)\bft\b"),     "fort"),
]

# Points cardinaux — word boundary strict pour éviter n→North dans "saint"
_CARDINAL_SUBS = [
    (re.compile(r"(?i)\bnorth\b"),  "North"),   # déjà complet
    (re.compile(r"(?i)\bsouth\b"),  "South"),
    (re.compile(r"(?i)\beast\b"),   "East"),
    (re.compile(r"(?i)\bwest\b"),   "West"),
    (re.compile(r"\bN\b"),          "North"),   # abréviations majuscules seulement
    (re.compile(r"\bS\b"),          "South"),
    (re.compile(r"\bE\b"),          "East"),
    (re.compile(r"\bW\b"),          "West"),
]

_CHARS_RE = re.compile('[' + re.escape(''.join(CHAR_TO_REMOVE)) + ']')


# ── Fonctions ────────────────────────────────────────────────────────────────

def clean_cpy_name(string: str) -> str:
    string = fix_text(string)
    string = string.encode("ascii", errors="ignore").decode()
    string = string.lower().strip()
    string = " " + string + " "

    # Suppression des suffixes légaux
    string = _LEGAL_RE.sub(" ", string)

    # mfg → Manufacturing
    string = _MFG_RE.sub("Manufacturing", string)

    # Nettoyage des caractères spéciaux
    string = _CHARS_RE.sub("", string)
    string = _AMP_RE.sub("and", string)
    string = re.sub(r"[,\-]", " ", string)
    string = re.sub(r"\.", "", string)

    string = string.title()
    string = _MULTI_SP.sub(" ", string).strip()
    string = _BD_RE.sub("", string)
    string = _DIGI_AL.sub(" ", string)
    return string.strip()


def clean_cpy_address(string: str) -> str:
    """Normalise une adresse selon le standard USPS (sans dépendance externe)."""
    string = fix_text(string)
    string = string.strip()
    string = normalize_street_abbreviations(string)
    string = re.sub(r",", " ", string)
    string = _MULTI_SP.sub(" ", string).strip()
    return string


def clean_cpy_city(string: str) -> str:
    string = fix_text(string)
    string = string.strip()

    # Abréviations géographiques (st. → saint, mt. → mount, ft. → fort)
    for pattern, replacement in _GEO_SUBS:
        string = pattern.sub(replacement, string)

    # Points cardinaux — uniquement abréviations isolées (N, S, E, W)
    for pattern, replacement in _CARDINAL_SUBS:
        string = pattern.sub(replacement, string)

    # Nettoyage
    string = _CHARS_RE.sub("", string)
    string = _AMP_RE.sub("and", string)
    string = re.sub(r",", " ", string)
    string = re.sub(r"\.", "", string)

    string = _MULTI_SP.sub(" ", string).strip()
    string = _BD_RE.sub("", string)
    string = _DIGI_AL.sub(" ", string)
    return string.strip().title()


def clean_cpy_state(string: str) -> str:
    return string.upper().strip()   # ← corrigé : était x.upper()


# ── Remplacement de normalizer_usps ─────────────────────────────────────────
# Dictionnaire USPS standard des abréviations de types de voies
STREET_ABBR = {
    r"\bavenue\b":      "Ave",   r"\bave\b":        "Ave",
    r"\bboulevard\b":  "Blvd",  r"\bblvd\b":       "Blvd",
    r"\bcircle\b":     "Cir",   r"\bcir\b":        "Cir",
    r"\bcourt\b":      "Ct",    r"\bct\b":         "Ct",
    r"\bdrive\b":      "Dr",    r"\bdr\b":         "Dr",
    r"\bexpressway\b": "Expy",  r"\bexpy\b":       "Expy",
    r"\bfreeway\b":    "Fwy",   r"\bfwy\b":        "Fwy",
    r"\bhighway\b":    "Hwy",   r"\bhwy\b":        "Hwy",
    r"\blane\b":       "Ln",    r"\bln\b":         "Ln",
    r"\bparkway\b":    "Pkwy",  r"\bpkwy\b":       "Pkwy",
    r"\bplace\b":      "Pl",    r"\bpl\b":         "Pl",
    r"\broad\b":       "Rd",    r"\brd\b":         "Rd",
    r"\bsquare\b":     "Sq",    r"\bsq\b":         "Sq",
    r"\bstreet\b":     "St",    r"\bst\b":         "St",
    r"\bterrace\b":    "Ter",   r"\bter\b":        "Ter",
    r"\btrail\b":      "Trl",   r"\btrl\b":        "Trl",
    r"\bway\b":        "Way",
    # Directions
    r"\bnorth\b":      "N",     r"\bsouth\b":      "S",
    r"\beast\b":       "E",     r"\bwest\b":       "W",
    r"\bnortheast\b":  "NE",    r"\bnorthwest\b":  "NW",
    r"\bsoutheast\b":  "SE",    r"\bsouthwest\b":  "SW",
}

_STREET_RE = {re.compile(k, re.IGNORECASE): v for k, v in STREET_ABBR.items()}

def normalize_street_abbreviations(string: str) -> str:
    """Normalise les types de voies et directions selon le standard USPS."""
    for pattern, replacement in _STREET_RE.items():
        string = pattern.sub(replacement, string)
    return string

def clean_cpy_category(string: str) -> str:
    string = _MULTI_SP.sub(" ", string).strip()
    return string.title()   # ← corrigé : était x.upper()


def clean_cpy_description(string: str) -> str:
    string = _MULTI_SP.sub(" ", string).strip()
    return string  # ← corrigé : était x.upper()

def clean_cpy_zip(code) -> str:
    string = str(code)
    return string.zfill(5)

def clean_cpy_sic(code) -> str:
    string = str(code)
    return string.zfill(4)

def clean_cpy_website(string) -> str:
    return string.lower().strip()

def clean_cpy_email(string) -> str:
    return string.lower().strip()