"""
Failure Taxonomy Classifier for LLM Disagreements and Prediction Errors.

Categorizes prediction discrepancies into structured error taxonomies:
    - hinglish_ambiguity: Code-mixed Hindi-English idioms or vernacular syntax
    - sarcasm_irony: Sarcastic praise masking frustration or financial loss
    - multi_topic_complexity: Competing issues in a single post (e.g. mandate + KYC)
    - missing_context: Ambiguous or brief feedback lacking clear behavioral cues
    - implicit_trigger: Subtle churn triggers lacking explicit keywords
"""

from typing import List, Dict, Any
from collections import Counter


FAILURE_TAXONOMY_CATEGORIES = {
    "hinglish_ambiguity": {
        "title": "Hinglish Idiom & Code-Mixing Ambiguity",
        "description": "Colloquial Hindi-English idioms (e.g. 'paisa kat gaya', 'band kar di', 'dar lagta hai') where standard LLM tokenizers misjudge intent or action."
    },
    "sarcasm_irony": {
        "title": "Sarcastic / Ironic Tone Inversion",
        "description": "Reviews expressing extreme dissatisfaction through superficial praise (e.g. 'Best investment platform ever!' followed by complaints about bounce penalties)."
    },
    "multi_topic_complexity": {
        "title": "Multi-Topic Cognitive Complexity",
        "description": "Posts containing multiple intertwining events (e.g. salary date change + mandate failure + customer care lag), leading model to latch onto secondary topics."
    },
    "missing_context": {
        "title": "Missing Conversational Context",
        "description": "Short, fragmented statements lacking explicit timeline or action details."
    },
    "implicit_trigger": {
        "title": "Implicit / Unstated Churn Trigger",
        "description": "User describes emotional detachment or stopping without stating the primary catalyst."
    }
}


class FailureTaxonomyClassifier:
    """
    Diagnoses model prediction errors against golden set ground truth.
    """

    @staticmethod
    def classify_error(
        item: Dict[str, Any],
        pred: Dict[str, Any]
    ) -> str:
        """
        Classifies why a specific prediction differed from ground truth.
        """
        # If ground truth was pre-tagged with a challenge, respect it
        tagged = item.get("failure_challenge", "standard")
        if tagged in FAILURE_TAXONOMY_CATEGORIES:
            return tagged

        raw_text = item.get("raw_text", "").lower()

        # Check for sarcasm indicators
        if any(w in raw_text for w in ["great app", "best app", "best platform", "superb"]) and any(w in raw_text for w in ["penalty", "charged", "worst", "fraud", "scam"]):
            return "sarcasm_irony"

        # Check for Hinglish
        hinglish_markers = ["paisa", "kat gaya", "karna pada", "dikha", "dar lagta", "bhai", "samajh", "aayi", "ho gaya", "band"]
        if any(m in raw_text for m in hinglish_markers):
            return "hinglish_ambiguity"

        # Check for multi-topic complexity
        if len(raw_text.split()) > 35 or ("," in raw_text and ("and" in raw_text or "so" in raw_text)):
            return "multi_topic_complexity"

        return "missing_context"

    def analyze_discrepancies(
        self,
        golden_items: List[Dict[str, Any]],
        predicted_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Isolates all mismatches across key fields and tallies failure taxonomy modes.
        """
        discrepancies = []
        failure_counts = Counter()

        for g, p in zip(golden_items, predicted_items):
            mismatches = []
            for field in ["drop_trigger", "action_taken", "journey_stage", "emotion"]:
                g_val = str(g.get(field, "")).strip().lower()
                p_val = str(p.get(field, "")).strip().lower()
                if g_val != p_val:
                    mismatches.append({"field": field, "ground_truth": g_val, "predicted": p_val})

            if mismatches:
                failure_mode = self.classify_error(g, p)
                failure_counts[failure_mode] += 1
                discrepancies.append({
                    "id": g.get("id"),
                    "raw_text": g.get("raw_text")[:90] + "...",
                    "failure_mode": failure_mode,
                    "failure_title": FAILURE_TAXONOMY_CATEGORIES.get(failure_mode, {}).get("title", failure_mode),
                    "mismatches": mismatches
                })

        total_errors = len(discrepancies)
        distribution = {
            mode: {
                "count": count,
                "pct": round(count / total_errors * 100.0, 1) if total_errors > 0 else 0.0,
                "description": FAILURE_TAXONOMY_CATEGORIES.get(mode, {}).get("description", "")
            }
            for mode, count in failure_counts.most_common()
        }

        top_mode = failure_counts.most_common(1)[0][0] if failure_counts else "None"

        return {
            "total_discrepancies": total_errors,
            "top_failure_mode": top_mode,
            "failure_taxonomy_distribution": distribution,
            "discrepancy_cases": discrepancies
        }

