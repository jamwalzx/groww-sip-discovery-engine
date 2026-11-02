import os
import json
import logging
from collections import Counter
from typing import Dict, Any, List

logger = logging.getLogger("ml.theme_namer")

# High-fidelity domain patterns for naming Indian mutual fund SIP behavioral clusters
CURATED_TAXONOMY_MAP = [
    {
        "keywords": ["bounce", "mandate", "autopay", "bank penalty", "debit date", "590", "salary date"],
        "title": "Salary Date Mismatch Leading to Autopay Debit Rejection & Bank Charges",
        "description": "Investors experience mandate bounce fees when SIP debit date precedes salary credit, triggering rage cancellations.",
        "type": "inductive",
        "drop_trigger": "payment_failure"
    },
    {
        "keywords": ["negative", "loss", "xirr", "returns are negative", "returnz", "month 2", "month 3", "underwhelming"],
        "title": "Month 3-6 Negative Return Disappointment & Volatility Panic",
        "description": "First-time investors panic over short-term portfolio red days and negative XIRR before rupee cost averaging compounds.",
        "type": "inductive",
        "drop_trigger": "underwhelming_returns"
    },
    {
        "keywords": ["nav", "cut-off", "ledger", "update", "2 days", "units allocated", "allotment"],
        "title": "Confusion Regarding NAV Cut-off Timings and Settlement Delays",
        "description": "Users are puzzled why unit allotment and portfolio updates take 1-2 business days post-debit.",
        "type": "inductive",
        "drop_trigger": "confusion"
    },
    {
        "keywords": ["discipline", "14 month", "18 month", "2 year", "1000 rs", "continuous", "after salary"],
        "title": "Disciplined Multi-Year Continuers with Fixed Post-Salary Debits",
        "description": "Persistent investors who mitigate anxiety by automating debits right after salary and ignoring daily portfolio checks.",
        "type": "inductive",
        "drop_trigger": "none"
    },
    {
        "keywords": ["cash crunch", "emergency", "wedding", "pause", "skip", "temporary", "need money"],
        "title": "Temporary Cash Flow Crunches & Friction with Emergency Pause UI",
        "description": "Investors face temporary life events and struggle to find a low-friction 1-3 month pause option without mandate cancellation.",
        "type": "inductive",
        "drop_trigger": "cash_crunch"
    },
    {
        "keywords": ["recession", "market crash", "market gir", "nifty fall", "market drop"],
        "title": "Macro Market Downturn Anxiety & Uninformed Discontinuation",
        "description": "Investors pause SIPs during market corrections following external doom news or social media rumors.",
        "type": "deductive",
        "drop_trigger": "market_drop"
    },
    {
        "keywords": ["support", "customer care", "ticket", "no response", "automated template", "bot"],
        "title": "Customer Support Resolution Lag for Transaction & Debit Inquiries",
        "description": "Support tickets related to failed debits or refunds receive automated responses, eroding user trust.",
        "type": "deductive",
        "drop_trigger": "switched_platform"
    },
    {
        "keywords": ["bug", "stuck", "crash", "freeze", "blank screen", "not opening"],
        "title": "Technical App Glitches During Portfolio Review and SIP Modification",
        "description": "App crashes or screen freezes when users attempt to modify SIP amounts or view historical performance.",
        "type": "deductive",
        "drop_trigger": "confusion"
    }
]

class ThemeNamer:
    """
    Labels discovered semantic clusters with concise, PM-actionable titles,
    identifying whether each theme is emergent/inductive or part of a standard deductive taxonomy.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Google GenAI for ThemeNamer.")
            except Exception as e:
                logger.warning(f"ThemeNamer could not initialize GenAI: {e}")

    def name_cluster(self, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Names a single cluster by analyzing its items, exemplars, and extracted tags.
        """
        items = cluster_data.get("items", [])
        exemplars = cluster_data.get("exemplars", [])

        # Compute aggregate metrics
        severities = [it.get("severity", 2) for it in items]
        avg_sev = sum(severities) / max(len(severities), 1)

        drop_triggers = [it.get("drop_trigger") for it in items if it.get("drop_trigger") not in ["unknown", None]]
        dominant_trigger = Counter(drop_triggers).most_common(1)[0][0] if drop_triggers else "unknown"

        journey_stages = [it.get("journey_stage") for it in items if it.get("journey_stage") not in ["unknown", None]]
        dominant_stage = Counter(journey_stages).most_common(1)[0][0] if journey_stages else "unknown"

        all_text = " ".join([it.get("raw_text", "") for it in items]).lower()

        # 1. Attempt LLM Naming if GenAI client is available
        if self.client and len(items) >= 2:
            try:
                quotes_text = "\n".join([f"- {it.get('raw_text', '')[:120]}" for it in exemplars])
                prompt = f"""You are a Growth Product Manager at Groww analyzing user feedback clusters.
Given these sample quotes from a cluster of mutual fund SIP feedback:
{quotes_text}

Provide a JSON object with:
1. "title": Concise actionable theme title (max 8 words, specific to the root friction or habit)
2. "description": 1-sentence product summary
3. "taxonomy_type": "inductive" if an emergent, specific behavioral problem, else "deductive"
4. "primary_drop_trigger": Dominant cause of drop (e.g. payment_failure, underwhelming_returns, confusion, cash_crunch)"""

                res = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.0}
                )
                parsed = json.loads(res.text.strip())
                return {
                    "title": parsed.get("title", f"Theme: {dominant_trigger.replace('_', ' ').title()}"),
                    "description": parsed.get("description", "Discovered mutual fund feedback cluster."),
                    "taxonomy_type": parsed.get("taxonomy_type", "inductive"),
                    "primary_drop_trigger": parsed.get("primary_drop_trigger", dominant_trigger),
                    "primary_journey_stage": dominant_stage,
                    "avg_severity": float(avg_sev)
                }
            except Exception as e:
                logger.warning(f"LLM theme naming failed: {e}. Using domain taxonomy matcher.")

        # 2. Domain Taxonomy Matcher
        best_match = None
        max_matches = 0

        for tax in CURATED_TAXONOMY_MAP:
            match_count = sum(1 for kw in tax["keywords"] if kw in all_text)
            if match_count > max_matches:
                max_matches = match_count
                best_match = tax

        if best_match and max_matches >= 2:
            return {
                "title": best_match["title"],
                "description": best_match["description"],
                "taxonomy_type": best_match["type"],
                "primary_drop_trigger": best_match["drop_trigger"] if best_match["drop_trigger"] != "none" else dominant_trigger,
                "primary_journey_stage": dominant_stage,
                "avg_severity": float(avg_sev)
            }

        # Fallback based on dominant trigger
        clean_name = dominant_trigger.replace("_", " ").title() if dominant_trigger != "unknown" else "General In-App Experience"
        return {
            "title": f"Friction Area: {clean_name}",
            "description": f"User cohort expressing issues and expectations related to {clean_name.lower()}.",
            "taxonomy_type": "deductive" if dominant_trigger in ["unknown", "confusion"] else "inductive",
            "primary_drop_trigger": dominant_trigger,
            "primary_journey_stage": dominant_stage,
            "avg_severity": float(avg_sev)
        }

