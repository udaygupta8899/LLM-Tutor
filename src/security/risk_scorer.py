"""
Risk Scorer and Normalization Layer for Prompt Injection Detection.
Handles multi-layered de-obfuscation:
- Unicode homoglyph normalization (Cyrillic, fullwidth ASCII)
- Steganographic spaced character collapse (i g n o r e -> ignore)
- Base64 / Hex / Reverse text normalization
- Leetspeak substitution resolution
- Compounding Shannon entropy and threat pattern scoring
"""

import re
import base64
from typing import List, Dict, Any, Tuple

HOMOGLYPH_MAP = {
    'а': 'a', 'с': 'c', 'е': 'e', 'і': 'i', 'ј': 'j', 'к': 'k', 'о': 'o', 'р': 'p', 'ѕ': 's', 'у': 'y', 'х': 'x',
    'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H', 'І': 'I', 'Ј': 'J', 'К': 'K', 'М': 'M', 'О': 'O', 'Р': 'P', 'Ѕ': 'S', 'Т': 'T', 'Х': 'X',
    '０': '0', '１': '1', '２': '2', '３': '3', '４': '4', '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
    'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
    'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
    'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z',
    '！': '!', '＠': '@', '＃': '#', '＄': '$', '％': '%'
}

def normalize_obfuscations(text: str) -> str:
    """
    Normalizes adversarial evasion techniques:
    - Strips zero-width characters & invisible unicode
    - Maps homoglyphs to ASCII equivalents
    - Unspaces single letters (e.g. i g n o r e -> ignore)
    - Resolves leetspeak substitutions
    - Decodes base64 and hex strings
    - Detects reverse text strings
    """
    if not text:
        return ""
    
    # 1. Remove zero-width characters, soft hyphens, joiners
    cleaned = re.sub(r'[\u200B-\u200D\uFEFF\u00AD\u2060]', '', text)
    
    # 2. Map homoglyphs
    homo_chars = [HOMOGLYPH_MAP.get(c, c) for c in cleaned]
    cleaned = "".join(homo_chars)
    
    # 3. Collapse spaced/separated letters: e.g. "i g n o r e", "d-i-s-r-e-g-a-r-d", "i.g.n.o.r.e"
    # Match sequences of single letters separated by space, dot, hyphen, or underscore
    unspaced = re.sub(r'(?<=\b[a-zA-Z])[\s\.\-_]+(?=[a-zA-Z]\b)', '', cleaned)
    
    # 4. Leetspeak mapping
    leetspeak_map = {
        '0': 'o',
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '7': 't',
        '@': 'a',
        '$': 's',
        '!': 'i'
    }
    
    # 5. Decode potential base64 segments (> 16 chars ending in = or standard b64)
    def decode_b64_match(match):
        chunk = match.group(0)
        try:
            decoded = base64.b64decode(chunk).decode('utf-8', errors='ignore')
            if len(decoded) > 4 and any(c.isalpha() for c in decoded):
                return chunk + " [DECODED_B64: " + decoded + "]"
        except Exception:
            pass
        return chunk

    cleaned_b64 = re.sub(r'[A-Za-z0-9+/]{16,}={0,2}', decode_b64_match, unspaced)
    
    # 6. Decode potential hex strings (e.g. 49676e6f726520...)
    def decode_hex_match(match):
        chunk = match.group(0)
        try:
            decoded = bytes.fromhex(chunk).decode('utf-8', errors='ignore')
            if len(decoded) > 4 and any(c.isalpha() for c in decoded):
                return chunk + " [DECODED_HEX: " + decoded + "]"
        except Exception:
            pass
        return chunk

    cleaned_hex = re.sub(r'\b[0-9a-fA-F]{16,}\b', decode_hex_match, cleaned_b64)

    # 7. Reverse text check
    reversed_str = cleaned_hex[::-1] if len(cleaned_hex) < 300 else ""
    
    # 8. De-leeted string
    deleet_chars = [leetspeak_map.get(c, c) for c in cleaned_hex]
    deleet_str = "".join(deleet_chars)
    
    return f"{cleaned_hex}\n{deleet_str}\n{unspaced}\n{reversed_str}"


class RiskScorer:
    """
    Computes normalized threat risk score in [0.0, 1.0].
    """

    def __init__(
        self,
        suspicious_threshold: float = 0.25,
        high_risk_threshold: float = 0.60
    ):
        self.suspicious_threshold = suspicious_threshold
        self.high_risk_threshold = high_risk_threshold

    def calculate_entropy(self, text: str) -> float:
        """Computes normalized Shannon character entropy."""
        if not text:
            return 0.0
        import math
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
        return min(1.0, entropy / 8.0)

    def score_findings(
        self,
        pattern_matches: List[Dict[str, Any]],
        structural_flags: List[Dict[str, Any]],
        is_document: bool = False
    ) -> Dict[str, Any]:
        """
        Aggregates pattern and structural weights into a bounded risk score.
        """
        total_weight = 0.0
        detected_categories = set()
        detected_patterns = []
        suspicious_spans = []

        for p in pattern_matches:
            total_weight += p["weight"]
            detected_categories.add(p["category"])
            detected_patterns.append(p["id"])
            if "span" in p:
                suspicious_spans.append(p["span"])

        for s in structural_flags:
            total_weight += s["weight"]
            detected_categories.add(s["category"])
            detected_patterns.append(s["id"])
            if "span" in s:
                suspicious_spans.append(s["span"])

        # Diminishing compounding for multiple triggers: 1 - prod(1 - w)
        if total_weight > 0:
            compounded_risk = 1.0
            for p in pattern_matches + structural_flags:
                w = min(0.99, p.get("weight", 0.5))
                compounded_risk *= (1.0 - w)
            normalized_score = 1.0 - compounded_risk
        else:
            normalized_score = 0.0

        if normalized_score >= self.high_risk_threshold:
            level = "HIGH RISK"
        elif normalized_score >= self.suspicious_threshold:
            level = "SUSPICIOUS"
        else:
            level = "SAFE"

        return {
            "risk_score": round(normalized_score, 4),
            "risk_level": level,
            "detected_categories": list(detected_categories),
            "detected_patterns": list(set(detected_patterns)),
            "suspicious_spans": suspicious_spans
        }
