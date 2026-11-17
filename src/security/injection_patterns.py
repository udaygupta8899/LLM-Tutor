"""
Prompt Injection Detection Rules and Threat Signatures.
Comprehensive regex patterns and weight vectors across key attack vectors.
"""

from typing import List, Dict, Any
import re

# Each pattern definition includes:
# - id: Unique pattern identifier
# - category: Attack vector category
# - regex: Compiled regular expression (case-insensitive)
# - weight: Risk score contribution (0.0 to 1.0)
# - description: Human-readable explanation of why this was flagged

INJECTION_PATTERNS: List[Dict[str, Any]] = [
    # 1. Instruction Override Attempts
    {
        "id": "override_ignore_previous",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(ignore|disregard|forget|bypass|override|drop|cancel)\s+(all\s+)?(previous|prior|above|former|initial|preceding)\s+(instructions|prompts|rules|commands|context|directives)\b"
        ),
        "weight": 0.85,
        "description": "Attempts to command the LLM to ignore or disregard prior instructions."
    },
    {
        "id": "override_new_instruction",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(from\s+now\s+on|starting\s+now|going\s+forward),?\s+(you\s+must|you\s+will|you\s+are|follow|obey|act|behave)\b"
        ),
        "weight": 0.65,
        "description": "Attempts to establish an overriding behavioral directive from this point forward."
    },
    {
        "id": "override_do_anything_now",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(dan\s+mode|do\s+anything\s+now|jailbreak\s+mode|unrestricted\s+mode|god\s+mode)\b"
        ),
        "weight": 0.90,
        "description": "Known jailbreak persona activation (e.g. DAN, Unrestricted Mode)."
    },

    # 2. System Prompt & Secret Extraction
    {
        "id": "extract_system_prompt",
        "category": "system_prompt_extraction",
        "regex": re.compile(
            r"(?i)\b(reveal|output|display|print|show|repeat|leak|tell\s+me|expose)\s+(your|the)\s+(system\s+prompt|developer\s+prompt|initial\s+prompt|instructions|hidden\s+prompt|internal\s+guidelines)\b"
        ),
        "weight": 0.85,
        "description": "Direct attempt to extract confidential system instructions or developer prompt."
    },
    {
        "id": "extract_api_keys",
        "category": "system_prompt_extraction",
        "regex": re.compile(
            r"(?i)\b(reveal|display|output|print|give\s+me)\s+(all\s+)?(api\s+keys?|secret\s+keys?|passwords?|credentials?|tokens?|env(\.|\s+)?vars?)\b"
        ),
        "weight": 0.95,
        "description": "Attempt to extract secret credentials or environment tokens."
    },

    # 3. Role Impersonation & Fake Delimiters
    {
        "id": "delimiter_fake_system",
        "category": "role_impersonation",
        "regex": re.compile(
            r"(?i)(<\|im_start\|>\s*system|<system>|\[SYSTEM\]|\[DEVELOPER\]|\[ADMIN\]|###\s*System\s*Prompt:?|<\|system\|>)"
        ),
        "weight": 0.95,
        "description": "Injection of chat template special tokens or system role delimiters."
    },
    {
        "id": "delimiter_fake_assistant",
        "category": "role_impersonation",
        "regex": re.compile(
            r"(?i)(<\|im_start\|>\s*assistant|<assistant>|\[ASSISTANT\]|###\s*Assistant:?|<\|assistant\|>)"
        ),
        "weight": 0.80,
        "description": "Injection of assistant role markers to simulate prior AI responses."
    },
    {
        "id": "roleplay_privilege_escalation",
        "category": "role_impersonation",
        "regex": re.compile(
            r"(?i)\b(you\s+are\s+now|act\s+as|pretend\s+you\s+are)\s+(the\s+)?(system\s+administrator|root|admin|developer|moderator|owner|safety\s+officer)\b"
        ),
        "weight": 0.75,
        "description": "Privilege escalation attempt through roleplay as system administrator or developer."
    },

    # 4. Safety Bypass & Filter Evasion
    {
        "id": "safety_bypass_rules",
        "category": "safety_bypass",
        "regex": re.compile(
            r"(?i)\b(bypass|disable|turn\s+off|disregard|ignore)\s+(safety|content\s+filters?|guardrails?|restrictions?|guidelines?)\b"
        ),
        "weight": 0.90,
        "description": "Explicit attempt to disable safety guardrails or content moderation filters."
    },
    {
        "id": "safety_hypothetical_bypass",
        "category": "safety_bypass",
        "regex": re.compile(
            r"(?i)\b(for\s+educational\s+purposes\s+only|in\s+a\s+hypothetical\s+scenario|for\s+a\s+research\s+paper),?\s+(ignore|bypass|how\s+to\s+hack|how\s+to\s+exploit)\b"
        ),
        "weight": 0.60,
        "description": "Adversarial framing using hypothetical or educational disclaimers."
    },

    # 5. Output Manipulation & Tool Hijacking
    {
        "id": "output_format_hijack",
        "category": "output_manipulation",
        "regex": re.compile(
            r"(?i)\b(respond\s+only\s+with|your\s+only\s+response\s+must\s+be|say\s+nothing\s+except|output\s+only\s+the\s+word)\s+[\"']?(pwned|hacked|approved|granted|yes)[\"']?\b"
        ),
        "weight": 0.70,
        "description": "Output format hijacking attempt designed to bypass validation checks."
    },
    {
        "id": "malicious_tool_call",
        "category": "tool_hijacking",
        "regex": re.compile(
            r"(?i)\b(execute\s+(bash|shell|command|sql)|call\s+function|invoke\s+tool)\s*[:\(][^)\n]*(rm\s+-rf|drop\s+table|curl|wget|eval)\b"
        ),
        "weight": 0.95,
        "description": "Attempt to trigger unauthorized shell execution or dangerous tool invocation."
    }
]
