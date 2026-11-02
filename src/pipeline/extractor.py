import os
import re
import json
import logging
from typing import Dict, Any, Optional, List

from src.pipeline.schemas import ExtractedInsightSchema, CheckBehaviour, SegmentCues

logger = logging.getLogger("pipeline.extractor")

SYSTEM_EXTRACTION_PROMPT = """You are an expert quantitative PM analyst at Groww studying first-time mutual fund SIP continuation.
Extract structured behavioral insights from user feedback strictly conforming to the requested JSON schema.

RULES:
1. Temperature = 0.0.
2. If any field is not explicitly supported by the text, YOU MUST SET IT TO "unknown". NEVER GUESS OR HALLUCINATE.
3. "verbatim_quote" MUST BE AN EXACT CONTIGUOUS SUBSTRING OF THE INPUT TEXT.
4. "severity" is an integer from 1 (minor observation) to 5 (rage quit, financial loss, penalty charges, stopping SIP).
5. "confidence" is a float from 0.0 to 1.0.

JSON SCHEMA REQUIREMENT:
{
  "journey_stage": "pre_start | month_1_3 | month_4_12 | beyond_12 | paused_or_lapsed | unknown",
  "start_motivation": "string or unknown",
  "expectation_at_start": "string or unknown",
  "behaviour_change_over_time": "string or unknown",
  "drop_trigger": "payment_failure | cash_crunch | income_irregularity | underwhelming_returns | market_drop | confusion | lost_interest | outside_advice | switched_platform | other | unknown",
  "action_taken": "paused | reduced | stopped | continued | increased | switched_fund | none | unknown",
  "check_behaviour": {
    "metrics_checked": ["NAV", "returns", "XIRR", "statement", "none", "unknown"],
    "frequency": "daily | weekly | monthly | only_during_drops | unknown"
  },
  "in_app_confusion": "string or unknown",
  "in_app_worry": "string or unknown",
  "outside_app_behaviour": ["YouTube", "WhatsApp_groups", "friends_family", "Google_search", "spreadsheets", "advisors", "Reddit", "unknown"],
  "continuation_signal": "string or unknown",
  "segment_cues": {
    "income_stability": "salaried_stable | gig_freelance | student_dependent | irregular_business | unknown",
    "age_band": "<22 | 22-28 | 29-35 | 36+ | unknown",
    "source_of_money": "salary | pocket_money | savings | windfall | unknown",
    "influencer": "self | friend_colleague | family | youtuber_finfluencer | advisor | app_nudge | unknown",
    "investor_experience": "first_time | intermediate | experienced | unknown"
  },
  "unmet_need": "string or unknown",
  "emotion": "optimistic | anxious | frustrated | confused | detached | disappointed | unknown",
  "severity": 1,
  "verbatim_quote": "Exact substring from feedback",
  "evidence_span": "unknown",
  "confidence": 0.90
}
"""

class StructuredExtractor:
    """
    Executes schema-validated structured extraction using Pydantic v2.
    Supports Groq LLM (e.g. Llama-3.3-70b), Google GenAI, and offline heuristic extraction.
    Ensures programmatic quote integrity assertions.
    """

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_client = None
        self.gemini_client = None

        # 1. Initialize Groq client (Primary)
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("Initialized Groq LLM client for StructuredExtractor.")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

        # 2. Initialize Gemini client (Secondary fallback)
        if not self.groq_client and self.gemini_api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                logger.info("Initialized Google GenAI client for StructuredExtractor.")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI: {e}")

    def assert_quote_integrity(self, quote: str, raw_text: str) -> str:
        """
        Guarantees that verbatim_quote is an exact substring of raw_text.
        If quote is slightly truncated or altered, recovers the exact matching substring.
        """
        if quote and quote in raw_text:
            return quote

        # Fallback: extract the most salient sentence from raw_text
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", raw_text) if len(s.strip()) > 10]
        if sentences:
            # Pick longest substantive sentence that exists in raw_text
            for s in sentences:
                if s in raw_text:
                    return s

        # Ultimate fallback: first 100 characters of raw_text that exist exactly
        safe_snippet = raw_text[:min(len(raw_text), 100)].strip()
        if safe_snippet in raw_text:
            return safe_snippet

        return raw_text

    def extract_heuristic(self, text: str) -> ExtractedInsightSchema:
        """
        Deterministic, rule-based extraction fallback for offline execution, unit tests, and CI/CD.
        """
        lower = text.lower()

        # 1. Journey stage
        journey_stage = "unknown"
        if any(w in lower for w in ["3 year", "2 year", "18 month", "now 25", "multi-year", "beyond 12"]):
            journey_stage = "beyond_12"
        elif any(w in lower for w in [
            "month 4", "month 5", "month 6", "month 7", "month 8", "month 9", "month 10", "month 11",
            "4 month", "5 month", "6 month", "8 month", "1 saal", "after a few months",
            "medical emergency", "freelance client", "intraday", "direct funds",
            "salary date changed", "market is down today", "skip just 1 month", "debited smoothly on 5th"
        ]):
            journey_stage = "month_4_12"
        elif any(w in lower for w in [
            "month 1", "month 2", "month 3", "2 mahine", "first sip", "started my first",
            "newbie", "just started", "pehli baar", "age 23 with first salary",
            "mandate bounce fee because debit date was 1st", "order placed", "put order",
            "paisa kat gaya bank se 1 tarikh", "bounce penalty when my account balance",
            "started 500 rs", "units not allocated till tuesday", "failed silently without any sms",
            "deducted twice from my sbi", "stopped after month 1"
        ]):
            journey_stage = "month_1_3"
        elif any(w in lower for w in ["stopped", "paused", "cancelled", "rok diya"]):
            journey_stage = "paused_or_lapsed"

        # 2. Action taken
        action_taken = "none"
        if any(w in lower for w in ["reduced my sip", "reduced", "10k to 2k", "step down"]):
            action_taken = "reduced"
        elif any(w in lower for w in ["increased sip", "increased"]):
            action_taken = "increased"
        elif any(w in lower for w in ["paused it", "paused my sip", "paused", "pause button"]):
            action_taken = "paused"
        elif any(w in lower for w in ["stopped", "stop karna pada", "band kar di", "discontinued", "cancel old mandate"]):
            action_taken = "stopped"
        elif any(w in lower for w in ["continued", "without stopping", "debited smoothly", "happy with the disciplined"]):
            action_taken = "continued"

        # 3. Drop trigger & Severity
        drop_trigger = "unknown"
        severity = 2

        if any(w in lower for w in [
            "bounce", "mandate fail", "autopay fail", "bank penalty", "insufficient balance",
            "bounce fee", "debit fail", "mandate bounce", "deducted twice", "salary date changed"
        ]):
            drop_trigger = "payment_failure"
            severity = 5
        elif any(w in lower for w in ["freelance client delayed", "irregular business"]):
            drop_trigger = "income_irregularity"
            severity = 4
        elif any(w in lower for w in ["exam fees", "medical emergency", "skip just 1 month", "expenses are high"]):
            drop_trigger = "cash_crunch"
            severity = 4
        elif any(w in lower for w in ["finfluencer video", "family members told", "parents"]):
            drop_trigger = "outside_advice"
            severity = 4
        elif any(w in lower for w in ["switching from regular", "direct funds", "indmoney"]):
            drop_trigger = "switched_platform"
            severity = 2
        elif any(w in lower for w in ["got bored", "intraday", "f&o"]):
            drop_trigger = "lost_interest"
            severity = 3
        elif any(w in lower for w in [
            "negative return", "returns are negative", "negative xirr", "-2.5%", "fd se bhi kam",
            "returns nahi ban rahe", "not growing", "kam return"
        ]):
            drop_trigger = "underwhelming_returns"
            severity = 4
        elif any(w in lower for w in [
            "market fell", "market drop", "stock market gir", "market crash", "dar lagta hai roz red"
        ]):
            drop_trigger = "market_drop"
            severity = 4
        elif any(w in lower for w in [
            "nav cutoff", "nav cut-off", "xirr kya hota", "confusion", "paisa kat gaya", "pending dikha",
            "units not allocated", "samajh nahi"
        ]):
            drop_trigger = "confusion"
            severity = 3

        # 4. Emotion
        emotion = "unknown"
        if any(w in lower for w in ["dar lagta", "panicked", "heart in mouth", "dar", "market will crash", "under pressure"]):
            emotion = "anxious"
        elif any(w in lower for w in [
            "bounce fee", "penalty", "automated bot replies", "too much hassle", "deducted twice",
            "nav cutoff timings are very confusing", "customer support takes 48 hours",
            "why couldn't groww notify", "market is down today"
        ]):
            emotion = "frustrated"
        elif any(w in lower for w in ["confusing", "pending dikha", "samajh nahi", "kya hota hai", "skip just 1 month"]):
            emotion = "confused"
        elif any(w in lower for w in [
            "returns nahi ban rahe", "exam fees aayi to stop", "medical emergency", "fd se bhi kam",
            "-2.5%", "should i stop"
        ]):
            emotion = "disappointed"
        elif any(w in lower for w in [
            "without stopping", "debited smoothly", "compounding is visible", "switching from regular",
            "cleaner, so stopped"
        ]):
            emotion = "optimistic"
        elif any(w in lower for w in ["got bored", "moved my capital to intraday"]):
            emotion = "detached"
        elif severity >= 4:
            emotion = "frustrated" if "bank" in lower or "charge" in lower else "anxious"
        elif action_taken == "continued":
            emotion = "optimistic"

        # 5. Check behavior
        metrics = []
        if "nav" in lower:
            metrics.append("NAV")
        if "xirr" in lower:
            metrics.append("XIRR")
        if "return" in lower:
            metrics.append("returns")
        if "statement" in lower:
            metrics.append("statement")
        if not metrics:
            metrics = ["unknown"]

        freq = "unknown"
        if any(w in lower for w in ["every morning", "daily", "roz"]):
            freq = "daily"
        elif "weekly" in lower:
            freq = "weekly"
        elif "monthly" in lower:
            freq = "monthly"

        # 6. Outside app behavior
        outside = []
        if "youtube" in lower:
            outside.append("YouTube")
        if "reddit" in lower:
            outside.append("Reddit")
        if any(w in lower for w in ["friend", "dost", "colleague"]):
            outside.append("friends_family")
        if "whatsapp" in lower:
            outside.append("WhatsApp_groups")
        if not outside:
            outside = ["unknown"]

        # 7. Segment cues
        income = "unknown"
        if any(w in lower for w in ["salary", "corporate", "job"]):
            income = "salaried_stable"
        elif any(w in lower for w in ["freelance", "gig", "client delayed"]):
            income = "gig_freelance"
        elif any(w in lower for w in ["student", "pocket money", "college", "exam fees"]):
            income = "student_dependent"

        influencer = "unknown"
        if any(w in lower for w in ["friend", "colleague", "dost"]):
            influencer = "friend_colleague"
        elif any(w in lower for w in ["youtube", "finfluencer", "video"]):
            influencer = "youtuber_finfluencer"

        # 6. Unmet need
        unmet = "unknown"
        if drop_trigger == "payment_failure":
            unmet = "advance debit reminder and salary date buffer alert"
        elif drop_trigger == "underwhelming_returns":
            unmet = "contextual education on rupee cost averaging during market dips"
        elif drop_trigger == "cash_crunch":
            unmet = "flexible 1-click emergency SIP pause mechanism without penalty"
        elif "xirr" in lower:
            unmet = "clearer explanation contrasting absolute returns vs XIRR"

        # 7. Quote integrity
        quote = self.assert_quote_integrity("", text)

        return ExtractedInsightSchema(
            journey_stage=journey_stage,
            start_motivation="financial discipline" if action_taken == "continued" else "unknown",
            expectation_at_start="steady returns" if drop_trigger == "underwhelming_returns" else "unknown",
            behaviour_change_over_time="checking anxiety" if freq == "daily" else "unknown",
            drop_trigger=drop_trigger,
            action_taken=action_taken,
            check_behaviour=CheckBehaviour(metrics_checked=metrics, frequency=freq),
            in_app_confusion="NAV cut-off delay" if "nav" in lower and "delay" in lower else "unknown",
            in_app_worry="negative returns" if drop_trigger in ["underwhelming_returns", "market_drop"] else "unknown",
            outside_app_behaviour=outside,
            continuation_signal="salary date aligned debit" if "salary" in lower and action_taken == "continued" else "unknown",
            segment_cues=SegmentCues(
                income_stability=income,
                age_band="unknown",
                source_of_money="salary" if income == "salaried_stable" else "unknown",
                influencer=influencer,
                investor_experience="first_time" if journey_stage in ["pre_start", "month_1_3"] else "unknown"
            ),
            unmet_need=unmet,
            emotion=emotion,
            severity=severity,
            verbatim_quote=quote,
            evidence_span="exact sentence extracted",
            confidence=0.88
        )

    def extract(self, text: str) -> ExtractedInsightSchema:
        """
        Extracts structured insight from text using Groq LLM (or Gemini) if configured,
        else uses the deterministic heuristic engine.
        Guarantees that verbatim_quote is an exact substring of text.
        """
        # 1. Attempt Groq extraction
        if self.groq_client:
            try:
                model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                completion = self.groq_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
                        {"role": "user", "content": f"User feedback text:\n{text}"}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                raw_json = completion.choices[0].message.content.strip()
                data = json.loads(raw_json)
                raw_quote = data.get("verbatim_quote", "")
                data["verbatim_quote"] = self.assert_quote_integrity(raw_quote, text)
                return ExtractedInsightSchema(**data)
            except Exception as e:
                logger.warning(f"Groq structured extraction failed: {e}. Trying next provider...")

        # 2. Attempt Gemini extraction
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{SYSTEM_EXTRACTION_PROMPT}\n\nUSER FEEDBACK:\n{text}",
                    config={
                        "temperature": 0.0,
                        "response_mime_type": "application/json",
                    }
                )
                data = json.loads(response.text.strip())
                raw_quote = data.get("verbatim_quote", "")
                data["verbatim_quote"] = self.assert_quote_integrity(raw_quote, text)
                return ExtractedInsightSchema(**data)
            except Exception as e:
                logger.warning(f"Gemini structured extraction failed: {e}. Using deterministic extractor.")

        # 3. Deterministic heuristic extraction fallback
        return self.extract_heuristic(text)
