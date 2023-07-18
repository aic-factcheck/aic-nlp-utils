import unicodedata

def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)