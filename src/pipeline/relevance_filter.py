import os
import re
import logging
from typing import Tuple, Dict, Any, List

logger = logging.getLogger("pipeline.relevance_filter")

# Keywords strongly indicative of SIP behavior, continuation, performance, or first-time investing
SIP_BEHAVIORAL_SIGNALS = [
    r"\bsip\b", r"\bmutual\s+funds?\b", r"\bautopay\b", r"\bmandate\b", r"\be-?mandate\b",
    r"\bnav\b", r"\bxirr\b", r"\breturns?\b", r"\binstalment\b", r"\binstallment\b",
    r"\bbounce\b", r"\bportfolio\b", r"\bunits?\b", r"\bcompounding\b", r"\bfirst\s+time\b",
    r"\bbeginner\b", r"\bindex\s+fund\b", r"\bflexi\s+cap\b", r"\bpause\b", r"\bstop\b",
    r"\bcancel\b", r"\bred\s+days?\b", r"\bcut-?off\b", r"\bdebit\b", r"\bdeduct\w*\b",
    r"\bloss\b", r"\bprofit\b", r"\bmarket\s+drop\b", r"\blumpsum\b", r"\bpenalty\b"
]

# Pure operational complaints that should be filtered OUT unless related to SIP continuation
IRRELEVANT_OPERATIONAL_PATTERNS = [
    (re.compile(r"^\s*(kyc\s+pending|kyc\s+rejected|pan\s+card\s+verification|aadhar\s+link\w*)\s*$", re.I), "pure_kyc_verification_issue"),
    (re.compile(r"^\s*(otp\s+not\s+coming|login\s+issue|cannot\s+login|password\s+reset|fingerprint\s+not\s+working)\s*$", re.I), "pure_login_auth_issue"),
    (re.compile(r"^\s*(app\s+crash\w*|lagging|update\s+error|blank\s+screen)\s*$", re.I), "generic_device_crash"),
    (re.compile(r"^\s*(good|nice|very\s+good|best\s+app|bakwas|worst|super)\s*$", re.I), "one_word_sentiment_no_context"),
]

class RelevanceFilter:
    """
    LLM and heuristic classifier that evaluates whether a feedback record contains
    substantive insights on SIP continuation, investor expectations, app friction, or drop triggers.
    Excludes generic KYC, login, or one-word sentiment complaints.
    """

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.groq_client = None
        self.gemini_client = None

        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info("Initialized Groq client for RelevanceFilter.")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

        if not self.groq_client and self.gemini_api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                logger.info("Initialized Google GenAI client for RelevanceFilter.")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}. Using heuristic classifier.")

    def evaluate_rule_based(self, text: str) -> Tuple[bool, str, float]:
        """
        High-precision rule-based relevance evaluation.
        """
        cleaned = text.strip()
        lower_text = cleaned.lower()

        # 1. Filter out trivial or pure operational complaints
        for pattern, reason in IRRELEVANT_OPERATIONAL_PATTERNS:
            if pattern.search(lower_text):
                return False, reason, 0.95

        # If length is extremely short without explicit SIP mention
        if len(cleaned.split()) < 4 and not re.search(r"\bsip\b", lower_text):
            return False, "insufficient_length_no_substance", 0.90

        # 2. Check for presence of core SIP behavioral signals
        matching_signals = [sig for sig in SIP_BEHAVIORAL_SIGNALS if re.search(sig, lower_text)]

        # Direct SIP or Mutual fund context
        if matching_signals:
            matched_terms = [re.sub(r"[\\b\s\?]+", " ", s).strip() for s in matching_signals[:3]]
            return True, f"contains_sip_context: {', '.join(matched_terms)}", 0.92

        # General investing / portfolio friction
        if any(w in lower_text for w in ["invest", "money", "rupaye", "paisa", "charges", "bank", "account", "tax"]):
            # Check if it has behavior or friction verbs
            if any(w in lower_text for w in ["fail", "error", "delay", "charge", "refund", "cut", "problem", "loss", "stop", "switch"]):
                return True, "financial_transaction_friction", 0.78

        return False, "unrelated_to_sip_continuation", 0.85

    def evaluate(self, text: str) -> Tuple[bool, str, float]:
        """
        Evaluates relevance using LLM when available, falling back to rule-based engine.
        """
        if not text or not text.strip():
            return False, "empty_text", 1.0

        # 1. Attempt Groq evaluation
        if self.groq_client:
            try:
                model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                prompt = f"""You are a product analyst filtering user feedback for Groww's mutual fund SIP continuation engine.
Goal: Keep feedback discussing SIP behavior, continuation, pausing, stopping, expectations, returns, NAV/XIRR confusion, debit failures, or first-time investing.
Drop pure KYC verification tickets, login OTP lockouts, or one-word praise ("good app") with no behavioral context.

Feedback:
"{text}"

Reply in exactly two lines:
RELEVANT: [YES/NO]
REASON: [Brief 1-sentence reason]"""

                completion = self.groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                txt = completion.choices[0].message.content.strip()
                is_rel = "RELEVANT: YES" in txt.upper()
                reason = "groq_classified"
                for line in txt.split("\n"):
                    if line.upper().startswith("REASON:"):
                        reason = line[7:].strip()
                return is_rel, reason, 0.95
            except Exception as e:
                logger.warning(f"Groq relevance filter call failed: {e}. Trying next provider...")

        # 2. Attempt Gemini evaluation
        if self.gemini_client:
            try:
                prompt = f"""You are a product analyst filtering user feedback for Groww's mutual fund SIP continuation engine.
Goal: Keep feedback discussing SIP behavior, continuation, pausing, stopping, expectations, returns, NAV/XIRR confusion, debit failures, or first-time investing.
Drop pure KYC verification tickets, login OTP lockouts, or one-word praise ("good app") with no behavioral context.

Feedback:
"{text}"

Reply in exactly two lines:
RELEVANT: [YES/NO]
REASON: [Brief 1-sentence reason]"""

                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                txt = response.text.strip()
                is_rel = "RELEVANT: YES" in txt.upper()
                reason = "gemini_classified"
                for line in txt.split("\n"):
                    if line.upper().startswith("REASON:"):
                        reason = line[7:].strip()
                return is_rel, reason, 0.95
            except Exception as e:
                logger.warning(f"Gemini relevance filter call failed: {e}. Falling back to rule-based evaluation.")

        return self.evaluate_rule_based(text)

    def filter_batch(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Filters a list of cleaned feedback items, computing drop percentage and categorizing items.
        """
        relevant_items = []
        dropped_items = []

        for item in items:
            is_rel, reason, conf = self.evaluate(item["raw_text"])
            item_copy = dict(item)
            item_copy["relevance_reason"] = reason
            item_copy["relevance_confidence"] = conf

            if is_rel:
                relevant_items.append(item_copy)
            else:
                dropped_items.append(item_copy)

        total = len(items)
        drop_pct = (len(dropped_items) / max(total, 1)) * 100

        return {
            "relevant_items": relevant_items,
            "dropped_items": dropped_items,
            "total_evaluated": total,
            "relevant_count": len(relevant_items),
            "dropped_count": len(dropped_items),
            "drop_percentage": drop_pct
        }

