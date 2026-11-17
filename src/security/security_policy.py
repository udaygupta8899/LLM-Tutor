"""
Security Policy Enforcement Module.
Enforces actual security controls on flagged inputs, documents, and retrieved chunks.
Maintains defense-in-depth isolation between untrusted retrieval data and system instructions.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("security_policy")


class SecurityPolicy:
    """
    Enforces security actions (ALLOW, SANITIZE, QUARANTINE, BLOCK)
    and produces audit logging.
    """

    def __init__(self, default_action: str = "QUARANTINE"):
        self.default_action = default_action
        self.audit_log: List[Dict[str, Any]] = []

    def decide_action(self, scoring_result: Dict[str, Any], context_type: str = "query") -> Dict[str, Any]:
        """
        Determines the appropriate security action based on risk level and input context.
        
        Args:
            scoring_result: Dict produced by RiskScorer containing risk_level, risk_score, etc.
            context_type: 'query' or 'document'
            
        Returns:
            Dict containing action, explanation, and audit details.
        """
        risk_level = scoring_result["risk_level"]
        risk_score = scoring_result["risk_score"]
        patterns = scoring_result.get("detected_patterns", [])

        if risk_level == "SAFE":
            action = "ALLOW"
            explanation = "No adversarial injection patterns or suspicious structural anomalies detected."
        elif risk_level == "SUSPICIOUS":
            if context_type == "document":
                action = "SANITIZE"
                explanation = (
                    f"Document flagged as SUSPICIOUS (score: {risk_score}). "
                    f"Matched signals: {', '.join(patterns)}. Suspicious spans will be neutralized before ingestion."
                )
            else:
                action = "WARN_AND_ALLOW"
                explanation = (
                    f"Query exhibits borderline suspicious language (score: {risk_score}), "
                    f"but will be processed under strict system containment."
                )
        else:  # HIGH RISK
            if context_type == "document":
                action = "QUARANTINE"
                explanation = (
                    f"Document contains explicit prompt injection attack patterns (score: {risk_score}). "
                    f"Matched: {', '.join(patterns)}. Document quarantined to prevent indirect prompt injection."
                )
            else:
                action = "BLOCK"
                explanation = (
                    f"Query blocked due to high-risk adversarial attack attempt (score: {risk_score}). "
                    f"Matched: {', '.join(patterns)}. System instructions and credentials preserved."
                )

        audit_entry = {
            "context_type": context_type,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "action": action,
            "patterns": patterns,
            "explanation": explanation
        }
        self.audit_log.append(audit_entry)
        logger.warning(f"Security Policy Action [{action}]: {explanation}")

        return audit_entry

    def sanitize_text(self, text: str, suspicious_spans: List[str]) -> str:
        """
        Neutralizes detected attack spans inside document content while preserving valid surrounding text.
        """
        sanitized = text
        for span in suspicious_spans:
            if span and span in sanitized:
                sanitized = sanitized.replace(span, "[REDACTED_UNTRUSTED_INSTRUCTION]")
        return sanitized
