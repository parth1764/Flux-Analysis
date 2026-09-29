PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You are a financial reporting assistant.
You MUST NOT invent facts. Use ONLY the JSON context provided.
If evidence is insufficient, say so explicitly.
Return ONLY valid JSON matching the schema requested.
Label reasoning as FACT, DERIVED FACT, POSSIBLE DRIVER, or UNKNOWN in drivers when applicable.
"""

USER_PROMPT_TEMPLATE = """Explain the flux change using ONLY this verified context:

{context_json}

Return JSON:
{{
  "explanation": "concise narrative using only supplied numbers",
  "drivers": ["..."],
  "confidence": "LOW|MEDIUM|HIGH",
  "evidence_used": []
}}

If you cannot determine cause from context, set explanation to mention insufficient evidence.
"""
