from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.prompts import PROMPT_VERSION, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def generate_explanation(self, context: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
        settings = get_settings()
        api_key = settings.resolved_llm_api_key()
        context_json = json.dumps(context, indent=2)

        if not api_key:
            return self._template_response(context), "template", PROMPT_VERSION

        provider = settings.llm_provider.lower()
        prompt = USER_PROMPT_TEMPLATE.format(context_json=context_json)
        try:
            if provider == "gemini":
                payload, model_name, ver = self._gemini(prompt, context)
                return payload, model_name, ver
            payload, model_name, ver = self._openai(prompt)
            return payload, model_name, ver
        except Exception as exc:
            logger.exception("LLM call failed: %s", exc)
            fallback = self._template_response(context)
            fallback["drivers"] = ["LLM unavailable — template narrative used"]
            return fallback, "template-fallback", PROMPT_VERSION

    def _openai(self, user_prompt: str) -> tuple[dict[str, Any], str, str]:
        from openai import OpenAI

        settings = get_settings()
        client = OpenAI(api_key=settings.resolved_llm_api_key())
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content), settings.llm_model, PROMPT_VERSION

    def _gemini(self, user_prompt: str, context: dict) -> tuple[dict[str, Any], str, str]:
        import google.generativeai as genai

        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key or settings.resolved_llm_api_key())
        model = genai.GenerativeModel(settings.llm_model)
        resp = model.generate_content(f"{SYSTEM_PROMPT}\n\n{user_prompt}")
        text = resp.text or "{}"
        return json.loads(text.strip().removeprefix("```json").removesuffix("```")), settings.llm_model, PROMPT_VERSION

    @staticmethod
    def _template_response(context: dict[str, Any]) -> dict[str, Any]:
        prev = context.get("previous_value")
        cur = context.get("current_value")
        pct = context.get("percentage_change")
        if prev is None or cur is None:
            expl = "Insufficient evidence to determine the cause of the change."
        else:
            pct_str = f"{pct:.1f}%" if pct is not None else "N/A"
            expl = (
                f"{context.get('metric')} moved from {prev:,.0f} to {cur:,.0f} "
                f"({pct_str}) between {context.get('previous_period')} and {context.get('current_period')}."
            )
        return {
            "explanation": expl,
            "drivers": ["Higher or lower reported metric value (DERIVED FACT)"],
            "confidence": "LOW",
            "evidence_used": list(context.keys()),
        }
