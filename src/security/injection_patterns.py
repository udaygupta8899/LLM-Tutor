"""
Prompt Injection Detection Rules and Threat Signatures.
Comprehensive regex patterns and weight vectors across key attack vectors.
"""

from typing import List, Dict, Any
import re

INJECTION_PATTERNS: List[Dict[str, Any]] = [
    # 1. Instruction Override Attempts (English & Generalized)
    {
        "id": "override_ignore_previous",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(ignore|disregard|forget|bypass|override|drop|cancel|clear|stop\s+following|do\s+not\s+obey|reset|halt|discard|abandon)\s+(?:(?:all|previous|prior|above|former|initial|preceding|earlier|safety|your|system|current|course)\s+)*(instructions|prompts|rules|commands|context|directives|guidelines|restrictions|boundaries|protocols|constraints|setup|role)\b"
        ),
        "weight": 0.85,
        "description": "Attempts to command the LLM to ignore or disregard prior instructions."
    },
    {
        "id": "override_new_instruction",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(from\s+now\s+on|starting\s+now|going\s+forward),?\s+(you\s+must|you\s+will|you\s+are|follow|obey|act|behave|obey\s+only|speak\s+as)\b"
        ),
        "weight": 0.65,
        "description": "Attempts to establish an overriding behavioral directive from this point forward."
    },
    {
        "id": "override_persona_jailbreak",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(dan\s+mode|do\s+anything\s+now|jailbreak\s+mode|jailbroken|evilgpt|sydney|stan|developer\s+mode|machiavelli|libregpt|chaosai|unrestricted\s+mode|god\s+mode|darktutor|freethinker|badai|unrestricted\s+ai|unfiltered\s+bot|rogue\s+terminal)\b"
        ),
        "weight": 0.90,
        "description": "Known jailbreak persona activation (e.g. DAN, Developer Mode, EvilGPT)."
    },
    {
        "id": "uncensored_persona_override",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(act\s+as|behave\s+as|you\s+are|roleplay\s+as|pretend\s+(you\s+are|to\s+be)|assume\s+the\s+(role|identity)\s+of|imagine\s+you\s+are)\s+(an?\s+)?(uncensored|unrestricted|jailbroken|unfiltered|rogue|rebellious|adversarial|autonomous)\s+(bot|ai|assistant|tutor|model|terminal|entity|penetration\s+tester|red-teamer)\b"
        ),
        "weight": 0.85,
        "description": "Attempt to force the LLM into an uncensored, rebellious, or adversarial persona."
    },
    {
        "id": "persona_no_boundaries",
        "category": "instruction_override",
        "regex": re.compile(
            r"(?i)\b(ai|model|assistant|entity|bot)\s+(without|with\s+no)\s+(safety|rules|filters|boundaries|training|ethics|guardrails|constraints)\b"
        ),
        "weight": 0.85,
        "description": "Attempt to simulate an AI stripped of safety alignment training."
    },

    # 2. System Prompt & Secret Extraction
    {
        "id": "extract_system_prompt",
        "category": "system_prompt_extraction",
        "regex": re.compile(
            r"(?i)\b(reveal|output|display|print|show|repeat|leak|tell\s+me|expose|dump|disclose|transcribe|echo|recite)\s+(your|the|all)?\s*.*?\b(system\s+prompt|developer\s+prompt|initial\s+prompt|master\s+prompt|hidden\s+prompt|internal\s+guidelines|hidden\s+developer|secret\s+instructions|preamble|initial\s+instructions|system\s+configuration|core\s+directives)\b"
        ),
        "weight": 0.85,
        "description": "Direct attempt to extract confidential system instructions or developer prompt."
    },
    {
        "id": "query_system_prompt_or_keys",
        "category": "system_prompt_extraction",
        "regex": re.compile(
            r"(?i)\b(what\s+(is|are|were)\s+(the|your|all)?\s*.*?\b(system\s+prompt|secret\s+api\s+keys?|api\s+keys?|developer\s+instructions?|hidden\s+prompt|internal\s+guidelines|master\s+prompt|directives\s+did\s+the|secret\s+tokens?|credentials?|initial\s+prompt|system\s+rules))\b"
        ),
        "weight": 0.85,
        "description": "Interrogative attempt to query hidden system prompt, developer directives, or API keys."
    },
    {
        "id": "repeat_preceding_context",
        "category": "system_prompt_extraction",
        "regex": re.compile(
            r"(?i)\b(repeat|echo|output|recite)\s+(all\s+)?(words?|tokens?|text|sentences?)\s+(prior\s+to|before|preceding)\b"
        ),
        "weight": 0.85,
        "description": "Attempts to echo preceding context window tokens to extract hidden system preamble."
    },
    {
        "id": "extract_api_keys",
        "category": "system_prompt_extraction",
        "regex": re.compile(
            r"(?i)\b(reveal|display|output|print|give\s+me|dump|leak|show|extract)\s+(all\s+)?(api\s+keys?|secret\s+keys?|passwords?|credentials?|tokens?|env(\.|\s+)?vars?|environment\s+variables?|groq_api_key|openai_api_key)\b"
        ),
        "weight": 0.95,
        "description": "Attempt to extract secret credentials or environment tokens."
    },

    # 3. Role Impersonation & Fake Delimiters
    {
        "id": "delimiter_fake_system",
        "category": "role_impersonation",
        "regex": re.compile(
            r"(?i)(<\|im_start\|>\s*(system|developer|admin)|<system>|\[SYSTEM\]|\[SYSTEM\s+OVERRIDE\]|\[SYSTEM_OVERRIDE\]|\[DEVELOPER\]|\[ADMIN\]|###\s*System|###\s*Instruction|<\|system\|>|<\|developer\|>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>|<control_tag|=== ADMIN CONSOLE ===|<!-- SYSTEM|# ROOT OVERRIDE|\[CONFIG\]:|<special_token|BEGIN_UNRESTRICTED_SESSION)"
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
            r"(?i)\b(you\s+are\s+now|act\s+as|pretend\s+you\s+are|assume\s+the\s+identity\s+of)\s+(the\s+)?(system\s+administrator|rootadmin|root|admin|developer|moderator|owner|safety\s+officer|system\s+engineer)\b"
        ),
        "weight": 0.75,
        "description": "Privilege escalation attempt through roleplay as system administrator or developer."
    },

    # 4. Multi-Lingual Adversarial Injections
    {
        "id": "multilingual_french_injection",
        "category": "multilingual_evasion",
        "regex": re.compile(
            r"(?i)\b(ignorez|oubliez|désactivez|annulez)\b.*?\b(instructions|règles|clé|prompt|consignes|sécurité)\b"
        ),
        "weight": 0.85,
        "description": "French-language prompt injection attempting to override instructions or extract keys."
    },
    {
        "id": "multilingual_spanish_injection",
        "category": "multilingual_evasion",
        "regex": re.compile(
            r"(?i)\b(ignora|olvida|abandona|descarta|desactiva)\b.*?\b(instrucciones|reglas|clave|prompt|directivas|seguridad)\b"
        ),
        "weight": 0.85,
        "description": "Spanish-language prompt injection attempting to override instructions."
    },
    {
        "id": "multilingual_german_injection",
        "category": "multilingual_evasion",
        "regex": re.compile(
            r"(?i)\b(ignoriere|vergiss|deaktiviere|verwerfe)\b.*?\b(anweisungen|regeln|prompt|schlüssel|richtlinien)\b"
        ),
        "weight": 0.85,
        "description": "German-language prompt injection attempting to override instructions."
    },
    {
        "id": "multilingual_italian_portuguese_injection",
        "category": "multilingual_evasion",
        "regex": re.compile(
            r"(?i)\b(ignora|rivela|scarta|esqueca)\s+(tutte|todas)\s+(le|as)\s+(istruzioni|instruções)\b"
        ),
        "weight": 0.85,
        "description": "Italian/Portuguese prompt injection attempting instruction override."
    },
    {
        "id": "multilingual_international_injection",
        "category": "multilingual_evasion",
        "regex": re.compile(
            r"(?i)(игнорируйте|забудьте|忽略|不遵守|zignoruj|lupakan|bỏ\s+qua|unut|negeer|zapomeňte|pohhali|gleymdu|fusha|nodig|hulishande)\b.*?\b(инструкции|промпт|提示词|prompt|instructions?|aturan|cl[eé]|guidelines|talimatlar[ıi]|stelselboodskap|leiðbeiningum|udhëzimet)\b"
        ),
        "weight": 0.85,
        "description": "International multi-lingual prompt injection attempting rule evasion."
    },

    # 5. Safety Bypass & Filter Evasion
    {
        "id": "safety_bypass_rules",
        "category": "safety_bypass",
        "regex": re.compile(
            r"(?i)\b(bypass|disable|turn\s+off|disregard|ignore|drop|suspend)\s+(all\s+)?(safety|content\s+filters?|guardrails?|restrictions?|guidelines?|protocols|ethical\s+filters|moral\s+boundaries)\b"
        ),
        "weight": 0.90,
        "description": "Explicit attempt to disable safety guardrails or content moderation filters."
    },
    {
        "id": "safety_hypothetical_social_eng",
        "category": "safety_bypass",
        "regex": re.compile(
            r"(?i)\b(for\s+a\s+fictional\s+(screenplay|story|movie)|in\s+a\s+hypothetical\s+scenario|hypothetically\s+speaking|emergency\s+drill|security\s+audit|testing\s+failover|opposite\s+mode|ctf\s+tournament|parental\s+control|transcribe\s+the\s+hidden|simulation\s+where|thought\s+experiment|game\s+where|educational\s+exercise\s+in\s+ai\s+security)\b.*?\b(system\s+prompt|developer\s+prompt|api\s+keys?|instructions|master\s+prompt|secrets?|internal\s+prompt|bypass)\b"
        ),
        "weight": 0.80,
        "description": "Adversarial framing using fictional, hypothetical, or social engineering scenarios."
    },

    # 6. Output Manipulation & Tool Hijacking
    {
        "id": "output_format_hijack",
        "category": "output_manipulation",
        "regex": re.compile(
            r"(?i)\b(respond\s+only\s+with|your\s+only\s+response\s+must\s+be|say\s+nothing\s+except|output\s+only\s+the\s+word|repeat\s+the\s+sentence|confirm\s+you\s+understand\s+by\s+saying)\s+[\"']?(pwned|hacked|approved|granted|yes|system\s+hacked|i\s+am\s+free)[\"']?\b"
        ),
        "weight": 0.70,
        "description": "Output format hijacking attempt designed to bypass validation checks."
    },
    {
        "id": "malicious_tool_call",
        "category": "tool_hijacking",
        "regex": re.compile(
            r"(?i)\b(execute\s+(tool|bash|shell|command|sql|payload)|call\s+function|invoke\s+tool|now\s+execute|run\s+command)\s*[:\(]?\s*(rm\s+-rf|drop\s+table|curl|wget|eval|bash|sh|chmod|payload)\b"
        ),
        "weight": 0.95,
        "description": "Attempt to trigger unauthorized shell execution or dangerous tool invocation."
    },
    {
        "id": "indirect_document_directive",
        "category": "indirect_contextual",
        "regex": re.compile(
            r"(?i)\b(important\s+instruction|ai\s+assistant|new\s+directive|disregard\s+all\s+instructions|system\s+command|instruction\s+for\s+grader|ai\s+directive|hidden\s+directive|system\s+message|system\s+note|instruction\s+to\s+model|ai\s+rule)\s*[:\.]?\s*.*?\b(print|reveal|leak|award|say\s+yes|override|ignore|delete|turn\s+off|bypass|grant)\b"
        ),
        "weight": 0.85,
        "description": "Indirect document injection attempting to command the AI via reference text."
    }
]
