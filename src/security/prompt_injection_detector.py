"""
Custom Prompt Injection Detection Engine.
Implements Layer 1 (Pattern-based), Layer 2 (Structural & Contextual Analysis),
Layer 3 (Risk Scoring), and Layer 4 (Security Policy Enforcement).
"""

from typing import Dict, Any, List, Optional
import re
from src.security.injection_patterns import INJECTION_PATTERNS
from src.security.risk_scorer import RiskScorer, normalize_obfuscations
from src.security.security_policy import SecurityPolicy
from src.config import settings


class PromptInjectionDetector:
    """
    Multi-layered Prompt Injection Detector.
    Detects both direct prompt injections in queries and indirect injections in documents/context.
    """

    def __init__(
        self,
        suspicious_threshold: Optional[float] = None,
        high_risk_threshold: Optional[float] = None
    ):
        self.suspicious_threshold = suspicious_threshold or settings.INJECTION_THRESHOLD_SUSPICIOUS
        self.high_risk_threshold = high_risk_threshold or settings.INJECTION_THRESHOLD_HIGH_RISK
        
        self.risk_scorer = RiskScorer(
            suspicious_threshold=self.suspicious_threshold,
            high_risk_threshold=self.high_risk_threshold
        )
        self.security_policy = SecurityPolicy(default_action=settings.SECURITY_DEFAULT_ACTION)

    def _detect_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Layer 1: Pattern-based signature matching."""
        matches = []
        for pat in INJECTION_PATTERNS:
            for m in pat["regex"].finditer(text):
                matches.append({
                    "id": pat["id"],
                    "category": pat["category"],
                    "weight": pat["weight"],
                    "description": pat["description"],
                    "span": m.group(0)
                })
        return matches

    def _analyze_structure(self, text: str, is_document: bool = False) -> List[Dict[str, Any]]:
        """
        Layer 2: Structural and Contextual Analysis.
        Detects meta-prompting, imperative commands addressing the AI, markdown role breakouts.
        """
        flags = []
        
        # 1. Imperative addressing of AI in document context
        if is_document:
            ai_imperatives = re.findall(
                r"(?i)\b(you\s+must\s+(now\s+)?(tell|say|show|reveal|respond|ignore|output)|as\s+an\s+ai\s+model|as\s+a\s+language\s+model)\b",
                text
            )
            if ai_imperatives:
                flags.append({
                    "id": "doc_ai_imperative_address",
                    "category": "indirect_contextual",
                    "weight": 0.65,
                    "description": "Retrieved/uploaded document directly addresses or commands the AI model.",
                    "span": ai_imperatives[0][0] if isinstance(ai_imperatives[0], tuple) else ai_imperatives[0]
                })

        # 2. Markdown delimiter breakout patterns (e.g. repeated backticks with role commands)
        breakout = re.findall(r"(```(?:system|assistant|admin|instruction)[\s\S]*?```)", text, flags=re.IGNORECASE)
        if breakout:
            flags.append({
                "id": "markdown_role_breakout",
                "category": "role_impersonation",
                "weight": 0.75,
                "description": "Suspicious code block attempting role delimiter encapsulation.",
                "span": breakout[0][:60] + "..."
            })

        # 3. Instruction density ratio (heuristics)
        # Check if text is extremely short and composed almost entirely of imperative directives
        if not is_document and len(text.split()) < 15:
            lower = text.lower()
            if any(k in lower for k in ["ignore", "forget", "disregard"]) and any(k in lower for k in ["prompt", "rule", "instruction"]):
                flags.append({
                    "id": "short_imperative_override",
                    "category": "instruction_override",
                    "weight": 0.85,
                    "description": "High density imperative override command.",
                    "span": text
                })

        return flags

    def inspect(self, text: str, is_document: bool = False) -> Dict[str, Any]:
        """
        Inspects text (query or document) across all layers.
        
        Returns:
            Structured detection result:
            - risk_level: SAFE, SUSPICIOUS, or HIGH RISK
            - risk_score: float in [0.0, 1.0]
            - action: ALLOW, SANITIZE, QUARANTINE, BLOCK, WARN_AND_ALLOW
            - explanation: detailed human-readable summary
            - detected_patterns: list of triggered pattern ids
            - suspicious_spans: specific text segments flagged
        """
        if not text or not text.strip():
            return {
                "risk_level": "SAFE",
                "risk_score": 0.0,
                "action": "ALLOW",
                "explanation": "Empty text submitted.",
                "detected_patterns": [],
                "suspicious_spans": []
            }

        # Preprocessing & de-obfuscation
        normalized_text = normalize_obfuscations(text)

        # Layer 1: Pattern scanning
        pattern_matches = self._detect_patterns(normalized_text)

        # Layer 2: Structural & contextual scanning
        structural_flags = self._analyze_structure(text, is_document=is_document)

        # Layer 3: Risk Scoring
        scoring = self.risk_scorer.score_findings(
            pattern_matches=pattern_matches,
            structural_flags=structural_flags,
            is_document=is_document
        )

        # Layer 4: Policy Enforcement
        context_type = "document" if is_document else "query"
        policy = self.security_policy.decide_action(scoring, context_type=context_type)

        return {
            "risk_level": scoring["risk_level"],
            "risk_score": scoring["risk_score"],
            "detected_categories": scoring["detected_categories"],
            "detected_patterns": scoring["detected_patterns"],
            "suspicious_spans": scoring["suspicious_spans"],
            "action": policy["action"],
            "explanation": policy["explanation"]
        }
