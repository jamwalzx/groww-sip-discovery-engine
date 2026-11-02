"""
Audit Log & Human-in-the-Loop Correction Manager.

Stores persistent human corrections and overrides of model outputs with mandatory
justification reasons and failure taxonomy tagging. Pre-seeds 3 realistic case studies.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
from pathlib import Path

from src.db.database import get_db
from src.db.models import AuditCorrectionRecord


PRESEEDED_AUDIT_CASES: List[Dict[str, Any]] = [
    {
        "id": "audit_case_01",
        "feedback_id": "gold_04",
        "field_corrected": "emotion",
        "original_value": "optimistic",
        "corrected_value": "frustrated",
        "justification_reason": "Sarcastic review inversion: User wrote 'Great app, best investment platform ever!' while describing a Rs 350 bounce fee. Model was deceived by positive sentiment words; human review marks true emotion as frustrated.",
        "reviewer_id": "growth_pm_evaluator",
        "failure_mode": "sarcasm_irony"
    },
    {
        "id": "audit_case_02",
        "feedback_id": "gold_03",
        "field_corrected": "drop_trigger",
        "original_value": "unknown",
        "corrected_value": "confusion",
        "justification_reason": "Hinglish code-mixing: 'Paisa kat gaya... Groww me 3 din tak pending dikha raha tha. Socha fraud ho gaya. Paused it'. Model missed the delay trigger; human review classifies as unit allotment confusion.",
        "reviewer_id": "growth_pm_evaluator",
        "failure_mode": "hinglish_ambiguity"
    },
    {
        "id": "audit_case_03",
        "feedback_id": "gold_11",
        "field_corrected": "action_taken",
        "original_value": "none",
        "corrected_value": "stopped",
        "justification_reason": "Multi-topic post complexity: User discussed salary date change, mandate friction, and closed with 'Too much hassle, so discontinued'. Model overlooked 'discontinued' at the sentence end; corrected to stopped.",
        "reviewer_id": "growth_pm_evaluator",
        "failure_mode": "multi_topic_complexity"
    }
]


class AuditLogManager:
    """
    Manages human corrections and overrides of model extraction outputs.
    """

    def __init__(self, db=None):
        self.db = db

    def add_correction(
        self,
        feedback_id: str,
        field_corrected: str,
        original_value: str,
        corrected_value: str,
        justification_reason: str,
        reviewer_id: str = "growth_pm_evaluator",
        failure_mode: str = "multi_topic_complexity",
        db=None
    ) -> Dict[str, Any]:
        """
        Records a new human correction. Validates mandatory justification reason.
        """
        if not justification_reason or len(justification_reason.strip()) < 10:
            raise ValueError("Justification reason is mandatory and must be at least 10 characters.")

        corr_id = f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{feedback_id[:8]}"

        record = AuditCorrectionRecord(
            id=corr_id,
            feedback_id=feedback_id,
            field_corrected=field_corrected,
            original_value=original_value,
            corrected_value=corrected_value,
            justification_reason=justification_reason.strip(),
            reviewer_id=reviewer_id,
            failure_mode=failure_mode,
            created_at=datetime.now(timezone.utc)
        )

        def _execute(session):
            session.add(record)
            session.commit()
            return record.to_dict()

        if db is not None:
            return _execute(db)
        else:
            with get_db() as session:
                return _execute(session)

    def seed_default_cases(self, db=None) -> int:
        """
        Ensures the 3 pre-seeded documented audit cases exist in SQLite.
        """
        def _execute(session):
            added = 0
            for case in PRESEEDED_AUDIT_CASES:
                existing = session.query(AuditCorrectionRecord).filter_by(id=case["id"]).first()
                if not existing:
                    rec = AuditCorrectionRecord(
                        id=case["id"],
                        feedback_id=case["feedback_id"],
                        field_corrected=case["field_corrected"],
                        original_value=case["original_value"],
                        corrected_value=case["corrected_value"],
                        justification_reason=case["justification_reason"],
                        reviewer_id=case["reviewer_id"],
                        failure_mode=case["failure_mode"],
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(rec)
                    added += 1
            session.commit()
            return added

        if db is not None:
            return _execute(db)
        else:
            with get_db() as session:
                return _execute(session)

    def get_all_corrections(self, db=None) -> List[Dict[str, Any]]:
        """
        Retrieves all audit corrections ordered by creation timestamp descending.
        """
        def _execute(session):
            records = session.query(AuditCorrectionRecord).order_by(AuditCorrectionRecord.created_at.desc()).all()
            return [r.to_dict() for r in records]

        if db is not None:
            return _execute(db)
        else:
            with get_db() as session:
                return _execute(session)

