"""
Human-in-the-Loop Golden Dataset Benchmark for Mutual Fund SIP Continuation.

Provides 25 curated, human-annotated benchmark examples labeled blind to model
predictions. Used to evaluate extraction accuracy, Cohen's Kappa (κ), and
failure mode taxonomy.
"""

from typing import List, Dict, Any
from pathlib import Path
import csv
import os

GOLDEN_BENCHMARK_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "gold_01",
        "source": "play_store",
        "raw_text": "Bank charged 590 rs mandate bounce fee because debit date was 1st and salary came on 3rd. Groww should let us choose debit date easily. Stopped my SIP immediately.",
        "journey_stage": "month_1_3",
        "drop_trigger": "payment_failure",
        "action_taken": "stopped",
        "emotion": "frustrated",
        "income_stability": "salaried_stable",
        "severity": 5,
        "verbatim_quote": "Bank charged 590 rs mandate bounce fee because debit date was 1st and salary came on 3rd.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_02",
        "source": "reddit",
        "raw_text": "Started SIP of 5000 in Nifty 50 on Groww. In month 2 market fell 4% and my portfolio showed negative XIRR. Panicked and stopped it. Am I doing it wrong?",
        "journey_stage": "month_1_3",
        "drop_trigger": "underwhelming_returns",
        "action_taken": "stopped",
        "emotion": "anxious",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "In month 2 market fell 4% and my portfolio showed negative XIRR. Panicked and stopped it.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_03",
        "source": "youtube",
        "raw_text": "Paisa kat gaya bank se 1 tarikh ko par Groww me 3 din tak pending dikha raha tha. Socha fraud ho gaya. Paused it for now.",
        "journey_stage": "month_1_3",
        "drop_trigger": "confusion",
        "action_taken": "paused",
        "emotion": "confused",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "Paisa kat gaya bank se 1 tarikh ko par Groww me 3 din tak pending dikha raha tha.",
        "failure_challenge": "hinglish_ambiguity"
    },
    {
        "id": "gold_04",
        "source": "play_store",
        "raw_text": "Great app, charged me 350 rs bounce penalty when my account balance was short by just 50 rupees! Best investment platform ever!",
        "journey_stage": "month_1_3",
        "drop_trigger": "payment_failure",
        "action_taken": "stopped",
        "emotion": "frustrated",
        "income_stability": "unknown",
        "severity": 5,
        "verbatim_quote": "charged me 350 rs bounce penalty when my account balance was short by just 50 rupees!",
        "failure_challenge": "sarcasm_irony"
    },
    {
        "id": "gold_05",
        "source": "reddit",
        "raw_text": "I have been investing 10k per month for 3 years without stopping. Key is keeping debit date on the 5th after salary and not looking at daily NAV.",
        "journey_stage": "beyond_12",
        "drop_trigger": "unknown",
        "action_taken": "continued",
        "emotion": "optimistic",
        "income_stability": "salaried_stable",
        "severity": 1,
        "verbatim_quote": "I have been investing 10k per month for 3 years without stopping.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_06",
        "source": "play_store",
        "raw_text": "Freelance client delayed my payment this month so had no balance in bank. Couldn't find pause button easily, so mandate bounced with penalty.",
        "journey_stage": "month_4_12",
        "drop_trigger": "income_irregularity",
        "action_taken": "paused",
        "emotion": "frustrated",
        "income_stability": "gig_freelance",
        "severity": 4,
        "verbatim_quote": "Freelance client delayed my payment this month so had no balance in bank.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_07",
        "source": "app_store",
        "raw_text": "Nav cutoff timings are very confusing. Put order at 1:30 PM on Zerodha Coin and got next day NAV. Customer support takes 48 hours to reply.",
        "journey_stage": "month_1_3",
        "drop_trigger": "confusion",
        "action_taken": "none",
        "emotion": "frustrated",
        "income_stability": "unknown",
        "severity": 3,
        "verbatim_quote": "Nav cutoff timings are very confusing.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_08",
        "source": "youtube",
        "raw_text": "College student here. Started 500 rs SIP from pocket money. Exam fees aayi to stop karna pada. Option hona chahiye temporary stop ka.",
        "journey_stage": "month_1_3",
        "drop_trigger": "cash_crunch",
        "action_taken": "stopped",
        "emotion": "disappointed",
        "income_stability": "student_dependent",
        "severity": 3,
        "verbatim_quote": "Started 500 rs SIP from pocket money. Exam fees aayi to stop karna pada.",
        "failure_challenge": "hinglish_ambiguity"
    },
    {
        "id": "gold_09",
        "source": "reddit",
        "raw_text": "Month 6 into my mutual fund journey. Returns are -2.5% while my friends in crypto made 20%. Reduced my SIP from 10k to 2k.",
        "journey_stage": "month_4_12",
        "drop_trigger": "underwhelming_returns",
        "action_taken": "reduced",
        "emotion": "disappointed",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "Returns are -2.5% while my friends in crypto made 20%. Reduced my SIP from 10k to 2k.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_10",
        "source": "play_store",
        "raw_text": "Order placed on Friday, money deducted instantly from HDFC bank, but units not allocated till Tuesday night. Heart in mouth whole weekend.",
        "journey_stage": "month_1_3",
        "drop_trigger": "confusion",
        "action_taken": "none",
        "emotion": "anxious",
        "income_stability": "unknown",
        "severity": 3,
        "verbatim_quote": "money deducted instantly from HDFC bank, but units not allocated till Tuesday night.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_11",
        "source": "play_store",
        "raw_text": "My salary date changed from 1st to 7th. When I tried to change SIP date in app, it asked me to cancel old mandate and register new one. Too much hassle, so discontinued.",
        "journey_stage": "month_4_12",
        "drop_trigger": "payment_failure",
        "action_taken": "stopped",
        "emotion": "frustrated",
        "income_stability": "salaried_stable",
        "severity": 4,
        "verbatim_quote": "When I tried to change SIP date in app, it asked me to cancel old mandate and register new one.",
        "failure_challenge": "multi_topic_complexity"
    },
    {
        "id": "gold_12",
        "source": "manual_import",
        "raw_text": "Saw YouTube finfluencer video saying market will crash 20% this month. Stopped all my active SIPs in Parag Parikh and Mirae Asset.",
        "journey_stage": "month_4_12",
        "drop_trigger": "outside_advice",
        "action_taken": "stopped",
        "emotion": "anxious",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "Saw YouTube finfluencer video saying market will crash 20% this month. Stopped all my active SIPs",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_13",
        "source": "reddit",
        "raw_text": "Every time market drops 500 points, Groww sends notification 'Market is down today'. This induces panic. Finally disabled notifications and continued my SIP calmly.",
        "journey_stage": "month_4_12",
        "drop_trigger": "market_drop",
        "action_taken": "continued",
        "emotion": "frustrated",
        "income_stability": "unknown",
        "severity": 2,
        "verbatim_quote": "disabled notifications and continued my SIP calmly.",
        "failure_challenge": "multi_topic_complexity"
    },
    {
        "id": "gold_14",
        "source": "app_store",
        "raw_text": "Switching from regular funds to direct funds on INDmoney. Interface is so much cleaner, so stopped my previous SIPs on old app.",
        "journey_stage": "month_4_12",
        "drop_trigger": "switched_platform",
        "action_taken": "stopped",
        "emotion": "optimistic",
        "income_stability": "unknown",
        "severity": 2,
        "verbatim_quote": "stopped my previous SIPs on old app.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_15",
        "source": "youtube",
        "raw_text": "Bhai XIRR kya hota hai? 1 saal se SIP chal rahi hai par 12% ki jagah 6% dikh raha hai. Samajh nahi aa raha.",
        "journey_stage": "month_4_12",
        "drop_trigger": "confusion",
        "action_taken": "none",
        "emotion": "confused",
        "income_stability": "unknown",
        "severity": 3,
        "verbatim_quote": "1 saal se SIP chal rahi hai par 12% ki jagah 6% dikh raha hai.",
        "failure_challenge": "hinglish_ambiguity"
    },
    {
        "id": "gold_16",
        "source": "play_store",
        "raw_text": "Autopay failed silently without any SMS warning! Bank deducted Rs 450 bounce charges. Why couldn't Groww notify me 24 hours prior? Paused my SIP immediately.",
        "journey_stage": "month_1_3",
        "drop_trigger": "payment_failure",
        "action_taken": "paused",
        "emotion": "frustrated",
        "income_stability": "unknown",
        "severity": 5,
        "verbatim_quote": "Autopay failed silently without any SMS warning! Bank deducted Rs 450 bounce charges.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_17",
        "source": "reddit",
        "raw_text": "Started my first SIP at age 23 with first salary. Now 25, portfolio survived 2 corrections and compounding is visible. Increased SIP by 10%.",
        "journey_stage": "beyond_12",
        "drop_trigger": "unknown",
        "action_taken": "increased",
        "emotion": "optimistic",
        "income_stability": "salaried_stable",
        "severity": 1,
        "verbatim_quote": "compounding is visible. Increased SIP by 10%.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_18",
        "source": "youtube",
        "raw_text": "Sir returns nahi ban rahe mutual fund me. 4 months ho gaye FD se bhi kam return hai. Should I stop?",
        "journey_stage": "month_4_12",
        "drop_trigger": "underwhelming_returns",
        "action_taken": "none",
        "emotion": "disappointed",
        "income_stability": "unknown",
        "severity": 3,
        "verbatim_quote": "4 months ho gaye FD se bhi kam return hai. Should I stop?",
        "failure_challenge": "hinglish_ambiguity"
    },
    {
        "id": "gold_19",
        "source": "play_store",
        "raw_text": "Customer support is just automated bot replies! My SIP installment got deducted twice from my SBI account on the same day. Paused my SIP until this is solved.",
        "journey_stage": "month_1_3",
        "drop_trigger": "payment_failure",
        "action_taken": "paused",
        "emotion": "frustrated",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "SIP installment got deducted twice from my SBI account on the same day. Paused my SIP",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_20",
        "source": "manual_import",
        "raw_text": "Medical emergency at home consumed all my savings this month. Had to stop my monthly 3000 investment. Hope I can resume next year.",
        "journey_stage": "month_4_12",
        "drop_trigger": "cash_crunch",
        "action_taken": "stopped",
        "emotion": "disappointed",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "Medical emergency at home consumed all my savings this month. Had to stop my monthly 3000 investment.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_21",
        "source": "play_store",
        "raw_text": "App is clean and simple. Monthly SIP of 1000 debited smoothly on 5th every month. Very happy with the disciplined habit.",
        "journey_stage": "month_4_12",
        "drop_trigger": "unknown",
        "action_taken": "continued",
        "emotion": "optimistic",
        "income_stability": "unknown",
        "severity": 1,
        "verbatim_quote": "Monthly SIP of 1000 debited smoothly on 5th every month.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_22",
        "source": "reddit",
        "raw_text": "Family members told me mutual funds are just like lottery and gambling. Under pressure from parents, I stopped my SIP after month 1.",
        "journey_stage": "month_1_3",
        "drop_trigger": "outside_advice",
        "action_taken": "stopped",
        "emotion": "anxious",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "Under pressure from parents, I stopped my SIP after month 1.",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_23",
        "source": "play_store",
        "raw_text": "Groww interface is very good. But wish there was an option to skip just 1 month SIP when expenses are high instead of cancelling completely.",
        "journey_stage": "month_4_12",
        "drop_trigger": "cash_crunch",
        "action_taken": "none",
        "emotion": "confused",
        "income_stability": "unknown",
        "severity": 3,
        "verbatim_quote": "wish there was an option to skip just 1 month SIP when expenses are high",
        "failure_challenge": "standard"
    },
    {
        "id": "gold_24",
        "source": "youtube",
        "raw_text": "Sir Maine 2 mahine pehle SIP shuru ki thi. Portfolio dekh kar dar lagta hai roz red hota hai to band kar di.",
        "journey_stage": "month_1_3",
        "drop_trigger": "market_drop",
        "action_taken": "stopped",
        "emotion": "anxious",
        "income_stability": "unknown",
        "severity": 4,
        "verbatim_quote": "Portfolio dekh kar dar lagta hai roz red hota hai to band kar di.",
        "failure_challenge": "hinglish_ambiguity"
    },
    {
        "id": "gold_25",
        "source": "reddit",
        "raw_text": "I got bored of waiting for mutual fund returns and moved my capital to intraday trading and F&O. Stopped all 3 SIPs.",
        "journey_stage": "month_4_12",
        "drop_trigger": "lost_interest",
        "action_taken": "stopped",
        "emotion": "detached",
        "income_stability": "unknown",
        "severity": 3,
        "verbatim_quote": "got bored of waiting for mutual fund returns and moved my capital to intraday trading",
        "failure_challenge": "standard"
    }
]


def get_golden_benchmark() -> List[Dict[str, Any]]:
    """Returns the curated 25 golden set items."""
    return GOLDEN_BENCHMARK_ITEMS


def export_golden_set_csv(output_path: str = "data/processed/golden_set.csv") -> str:
    """Exports the golden dataset to CSV format for external human review/audits."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "id", "source", "raw_text", "journey_stage", "drop_trigger",
        "action_taken", "emotion", "income_stability", "severity",
        "verbatim_quote", "failure_challenge"
    ]

    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in GOLDEN_BENCHMARK_ITEMS:
            writer.writerow({k: item.get(k, "") for k in fields})

    return str(path.resolve())


def load_golden_set_csv(input_path: str = "data/processed/golden_set.csv") -> List[Dict[str, Any]]:
    """Loads golden set items from a CSV file."""
    path = Path(input_path)
    if not path.exists():
        return get_golden_benchmark()

    items = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append({
                "id": row["id"],
                "source": row["source"],
                "raw_text": row["raw_text"],
                "journey_stage": row["journey_stage"],
                "drop_trigger": row["drop_trigger"],
                "action_taken": row["action_taken"],
                "emotion": row["emotion"],
                "income_stability": row["income_stability"],
                "severity": int(row.get("severity", 3)),
                "verbatim_quote": row["verbatim_quote"],
                "failure_challenge": row.get("failure_challenge", "standard")
            })
    return items
