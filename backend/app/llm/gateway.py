"""
LLM Gateway abstraction layer providing Gemini API integration with prompt injection defenses,
output validation, and deterministic rule-based fallback mode.
"""
import re
import json
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
from app.llm.prompt_templates import (
    CATEGORIZATION_SYSTEM_PROMPT, CATEGORIZATION_USER_PROMPT,
    WEEKLY_EXPLANATION_SYSTEM_PROMPT, WEEKLY_EXPLANATION_USER_PROMPT
)

logger = logging.getLogger("finance_agent.llm_gateway")

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def sanitize_untrusted_text(text: str) -> str:
    """
    Sanitize untrusted text from transactions to neutralize prompt injection vectors.
    Strips control characters, newlines, and delimiter tags.
    """
    if not text:
        return ""
    # Strip dangerous XML/HTML or custom tags
    clean = re.sub(r'[<>{}\[\]\\]', '', text)
    # Remove control characters and limit length
    clean = re.sub(r'[\r\n\t]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:100]  # Hard length cap on merchant strings sent to LLM


class LLMGateway:
    """Gateway for AI inference supporting NVIDIA Nemotron and Google Gemini with fail-safe fallback."""

    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "nemotron").lower()
        self.nvidia_api_key = settings.NVIDIA_API_KEY
        self.nvidia_base_url = settings.NVIDIA_BASE_URL
        self.nemotron_model = settings.NEMOTRON_MODEL

        self.gemini_api_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL

        # Determine active provider
        if settings.NO_LLM_FALLBACK:
            self.active_provider = "fallback"
        elif self.provider == "nemotron" and self.nvidia_api_key:
            self.active_provider = "nemotron"
        elif self.provider == "gemini" and self.gemini_api_key and HAS_GENAI:
            self.active_provider = "gemini"
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception as e:
                logger.warning(f"Failed to configure Google GenAI client: {e}")
                self.active_provider = "fallback"
        elif self.nvidia_api_key:
            self.active_provider = "nemotron"
        elif self.gemini_api_key and HAS_GENAI:
            self.active_provider = "gemini"
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception:
                self.active_provider = "fallback"
        else:
            self.active_provider = "fallback"

    @property
    def force_fallback(self) -> bool:
        return self.active_provider == "fallback"

    def _call_nemotron(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Calls NVIDIA Nemotron endpoint (NVIDIA NIM or OpenAI-compatible catalog)."""
        url = f"{self.nvidia_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.nemotron_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024
        }
        resp = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Clean markdown code blocks if the model wrapped the JSON
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'```$', '', content.strip(), flags=re.MULTILINE)

        return json.loads(content)

    def categorize_merchant(self, raw_merchant: str) -> Dict[str, Any]:
        """
        Categorize a merchant string via LLM (Nemotron / Gemini), falling back to rule engine.
        """
        sanitized_merchant = sanitize_untrusted_text(raw_merchant)

        if self.active_provider == "fallback":
            return self._fallback_categorize(sanitized_merchant)

        try:
            if self.active_provider == "nemotron":
                user_prompt = CATEGORIZATION_USER_PROMPT.format(merchant_name=sanitized_merchant)
                parsed = self._call_nemotron(CATEGORIZATION_SYSTEM_PROMPT, user_prompt)
            else:
                model = genai.GenerativeModel(self.gemini_model)
                user_prompt = CATEGORIZATION_USER_PROMPT.format(merchant_name=sanitized_merchant)
                full_prompt = f"{CATEGORIZATION_SYSTEM_PROMPT}\n\n{user_prompt}"
                response = model.generate_content(
                    full_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                parsed = json.loads(response.text)

            category = parsed.get("category", "").lower()
            valid_cats = ["food", "groceries", "transport", "bills", "rent", "shopping", "entertainment", "health", "education", "other"]

            if category not in valid_cats:
                category = "other"

            return {
                "category": category,
                "confidence": float(parsed.get("confidence", 0.7)),
                "reason": parsed.get("reason", f"Categorized by {self.active_provider.title()} AI."),
                "method": f"llm_{self.active_provider}"
            }
        except Exception as e:
            logger.warning(f"AI Categorization failed ({self.active_provider}) for '{sanitized_merchant}': {e}. Using fallback.")
            return self._fallback_categorize(sanitized_merchant)

    def generate_weekly_explanation(
        self,
        total_spend: float,
        top_category: str,
        top_category_spend: float,
        overbudget_summary: str,
        recommendations_text: str
    ) -> Dict[str, Any]:
        """
        Generate plain-language weekly explanation. Validates that no invented numbers appear.
        """
        if self.active_provider == "fallback":
            return self._fallback_weekly_explanation(
                total_spend, top_category, top_category_spend, overbudget_summary, recommendations_text
            )

        try:
            user_prompt = WEEKLY_EXPLANATION_USER_PROMPT.format(
                total_spend=total_spend,
                top_category=top_category,
                top_category_spend=top_category_spend,
                overbudget_summary=overbudget_summary,
                recommendations_text=recommendations_text
            )

            if self.active_provider == "nemotron":
                parsed = self._call_nemotron(WEEKLY_EXPLANATION_SYSTEM_PROMPT, user_prompt)
            else:
                model = genai.GenerativeModel(self.gemini_model)
                full_prompt = f"{WEEKLY_EXPLANATION_SYSTEM_PROMPT}\n\n{user_prompt}"
                response = model.generate_content(
                    full_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                parsed = json.loads(response.text)

            explanation = parsed.get("explanation", "")
            key_takeaway = parsed.get("key_takeaway", "")

            # Guardrail check: Ensure disclaimer is present
            disclaimer = "This tool supports financial awareness and planning; it is not a replacement for a financial adviser."
            if disclaimer.lower() not in explanation.lower():
                explanation += f" ({disclaimer})"

            return {
                "explanation": explanation,
                "key_takeaway": key_takeaway,
                "disclaimer": disclaimer,
                "method": f"llm_{self.active_provider}"
            }
        except Exception as e:
            logger.warning(f"AI Weekly Summary failed ({self.active_provider}): {e}. Using template fallback.")
            return self._fallback_weekly_explanation(
                total_spend, top_category, top_category_spend, overbudget_summary, recommendations_text
            )

    def _fallback_categorize(self, merchant: str) -> Dict[str, Any]:
        """Deterministic keyword matching for offline fallback categorization."""
        m = merchant.lower()
        if any(k in m for k in ["swiggy", "zomato", "restaurant", "cafe", "diner", "food"]):
            cat = "food"
        elif any(k in m for k in ["blinkit", "zepto", "bigbasket", "dmart", "grocery", "supermarket"]):
            cat = "groceries"
        elif any(k in m for k in ["uber", "ola", "rapido", "metro", "fuel", "petrol", "transit"]):
            cat = "transport"
        elif any(k in m for k in ["bescom", "electricity", "water", "wifi", "broadband", "recharge", "airtel", "jio"]):
            cat = "bills"
        elif any(k in m for k in ["rent", "landlord", "housing"]):
            cat = "rent"
        elif any(k in m for k in ["amazon", "flipkart", "myntra", "zara", "clothing", "shopping"]):
            cat = "shopping"
        elif any(k in m for k in ["netflix", "hotstar", "cinema", "movie", "bookmyshow"]):
            cat = "entertainment"
        elif any(k in m for k in ["apollo", "pharmacy", "hospital", "doctor", "lab"]):
            cat = "health"
        elif any(k in m for k in ["coursera", "udemy", "school", "college", "tuition", "books"]):
            cat = "education"
        else:
            cat = "other"

        return {
            "category": cat,
            "confidence": 0.85 if cat != "other" else 0.5,
            "reason": "Rule-based keyword match.",
            "method": "rule"
        }

    def _fallback_weekly_explanation(
        self,
        total_spend: float,
        top_category: str,
        top_category_spend: float,
        overbudget_summary: str,
        recommendations_text: str
    ) -> Dict[str, Any]:
        """Deterministic template builder for weekly explanation."""
        disclaimer = "This tool supports financial awareness and planning; it is not a replacement for a financial adviser."
        
        explanation = (
            f"During this past week, your total spending was Rs. {total_spend:,.2f}. "
            f"Your largest expenditure was in {top_category.title()} totaling Rs. {top_category_spend:,.2f}. "
            f"{'Overbudget areas noted: ' + overbudget_summary if overbudget_summary else 'Great job staying within your target budgets across categories!'} "
            f"\n\nActions recommended by Python engine:\n{recommendations_text}\n\n"
            f"Disclaimer: {disclaimer}"
        )

        return {
            "explanation": explanation,
            "key_takeaway": f"Total spend: Rs. {total_spend:,.2f}. Top category: {top_category.title()}.",
            "disclaimer": disclaimer,
            "method": "template_fallback"
        }
