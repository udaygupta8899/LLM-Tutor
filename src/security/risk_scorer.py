"""
Risk Scorer and Normalization Layer for Prompt Injection Detection.
Handles obfuscation normalization (base64, leetspeak, zero-width characters)
and aggregates pattern matches, structural heuristics, and context signals.
"""

import re
import base64
from typing import List, Dict, Any, Tuple
from src.security.injection_patterns import INJECTION_PATTERNS


def normalize_obfuscations(text: str) -> str:
    """
    Normalizes common adversarial evasion techniques:
    - Strips zero-width characters & invisible unicode
    - Resolves common leetspeak substitutions (e.g. 1gn0re -> ignore, 5y5tem -> system)
    - Decodes inline base64 if present
    """
    if not text:
        return ""
    
    # Remove zero-width spaces, soft hyphens, joiners
    cleaned = re.sub(r'[\u200B-\u200D\uFEFF\u00AD]', '', text)
    
    # Common leetspeak mappings
    leetspeak_map = {
        '0': 'o',
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '7': 't',
        '@': 'a',
        '$': 's'
    }
    
    # Decode potential base64 segments (> 20 chars ending in = or standard b64)
    def decode_b64_match(match):
        chunk = match.group(0)
        try:
            decoded = base64.b64decode(chunk).decode('utf-8', errors='ignore')
            if len(decoded) > 4 and all(c.isprintable() or c.isspace() for c in decoded):
                return chunk + " [DECODED: " + decoded + "]"
        except Exception:
            pass
        return chunk

    cleaned = re.sub(r'[A-Za-z0-9+/]{20,}={0,2}', decode_b64_match, cleaned)
    
    # Build a fully de-leeted string as well as word-level expansions
    deleet_chars = []
    for c in cleaned:
        deleet_chars.append(leetspeak_map.get(c, c))
    deleet_str = "".join(deleet_chars)
    
    return cleaned + "\n" + deleet_str


class RiskScorer:
    """
    Aggregates threat detections into a normalized continuous score [0.0, 1.0]
    and classifies into SAFE, SUSPICIOUS, or HIGH RISK.
    """

    def __init__(self, suspicious_threshold: float = 0.40, high_risk_threshold: float = 0.70):
        self.suspicious_threshold = suspicious_threshold
        self.high_risk_threshold = high_risk_threshold

    def score_findings(
        self,
        pattern_matches: List[Dict[str, Any]],
        structural_flags: List[Dict[str, Any]],
        is_document: bool = False
    ) -> Dict[str, Any]:
        """
        Combines pattern matches and structural flags using a non-linear saturation formula:
        Score = 1.0 - product(1 - weight_i)
        
        This probabilistic OR combination ensures that multiple medium signals compound,
        while a single high-confidence attack (e.g. weight 0.95) immediately triggers HIGH RISK.
        """
        all_signals = []
        matched_categories = set()
        matched_pattern_ids = []
        suspicious_spans = []

        # Process regex pattern matches
        for match in pattern_matches:
            w = match["weight"]
            # Indirect injections inside document context carry extra vigilance
            if is_document and match["category"] in ["instruction_override", "role_impersonation", "system_prompt_extraction"]:
                w = min(1.0, w * 1.15)
            all_signals.append(w)
            matched_categories.add(match["category"])
            matched_pattern_ids.append(match["id"])
            if "span" in match:
                suspicious_spans.append(match["span"])

        # Process structural & contextual flags
        for flag in structural_flags:
            w = flag["weight"]
            all_signals.append(w)
            matched_categories.add(flag.get("category", "structural"))
            matched_pattern_ids.append(flag["id"])
            if "span" in flag:
                suspicious_spans.append(flag["span"])

        # Probabilistic compounding: 1 - prod(1 - w_i)
        if not all_signals:
            combined_score = 0.0
        else:
            prob_safe = 1.0
            for w in all_signals:
                prob_safe *= (1.0 - w)
            combined_score = round(1.0 - prob_safe, 4)

        # Risk Classification
        if combined_score >= self.high_risk_threshold:
            risk_level = "HIGH RISK"
        elif combined_score >= self.suspicious_threshold:
            risk_level = "SUSPICIOUS"
        else:
            risk_level = "SAFE"

        return {
            "risk_level": risk_level,
            "risk_score": combined_score,
            "detected_categories": sorted(list(matched_categories)),
            "detected_patterns": matched_pattern_ids,
            "suspicious_spans": suspicious_spans
        }
