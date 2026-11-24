"""Normalización y tokenización para los retrievers léxicos (BM25 / TF-IDF)."""
import re
import unicodedata

# Stopwords mínimas es+en (las slides mezclan ambos idiomas por el libro OSTEP).
STOPWORDS = set("""
a al algo algunas algunos ante antes como con contra cual cuales cuando de del desde donde
dos e el ella ellas ellos en entre era es esa esas ese eso esos esta estas este esto estos
fue ha hace hay la las le les lo los mas me mi mismo muy no nos o otra otro para pero por
porque que qué se ser si sin sobre son su sus tambien también tiene tienen todo todos tu un
una uno unos y ya cómo cuál dónde qué cuándo
the of and to in is are be for on with as by that this it an or from at which can not we
what how why when does do
""".split())


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


TOKEN_RE = re.compile(r"[a-z0-9_]+")


def tokenize(text: str) -> list[str]:
    text = strip_accents(text.lower())
    toks = TOKEN_RE.findall(text)
    return [_light_stem(t) for t in toks if t not in STOPWORDS and len(t) > 1]


def _light_stem(t: str) -> str:
    """Stemming muy liviano (plural es/en). Suficiente para slides; mejorable con Snowball."""
    if len(t) > 4 and t.endswith("es") and not t.endswith("ses"):
        return t[:-2]
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t
