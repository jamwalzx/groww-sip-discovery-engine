"""
View 6: Quality Assurance, Golden Set & Human-in-the-Loop Evaluation Harness.
Displays agreement scorecard (Accuracy & Cohen's Kappa), failure taxonomy breakdown,
and interactive human audit log interface with persistent overrides.
"""

import streamlit as st
import pandas as pd

from src.evals.golden_set import get_golden_benchmark, export_golden_set_csv
from src.evals.metrics import EvaluationHarness
from src.evals.failure_taxonomy import FailureTaxonomyClassifier
from src.evals.audit_log import AuditLogManager
from src.pipeline.extractor import StructuredExtractor


def render():
    st.title("🧪 Quality Assurance & Evaluation Harness")
    st.markdown(
        "Quantitative evaluation treating LLM extraction as a rigorous engineering discipline. "
        "Benchmark measured against **25 human-annotated items** labeled blind to model output."
    )

    golden_items = get_golden_benchmark()
    extractor = StructuredExtractor()

    # 1. Run evaluation
    predicted_items = [extractor.extract(it["raw_text"]).model_dump() for it in golden_items]
    harness = EvaluationHarness()
    results = harness.evaluate(golden_items, predicted_items)

    # 2. Scorecard
    st.subheader(f"📊 Evaluation Scorecard (n={results['sample_size']} Blind Annotations)")
    fields = results.get("fields", {})

    score_rows = []
    for fname, fdata in fields.items():
        score_rows.append({
            "Evaluation Field": fname,
            "Accuracy (%)": f"{fdata['accuracy_pct']:.1f}%",
            "Cohen's Kappa (κ)": f"{fdata['cohens_kappa']:.2f}",
            "Agreement Band": fdata["kappa_band"],
            "Validation Status": "✅ PASS" if fdata["status"] == "PASS" else "⚠️ NEEDS REVIEW"
        })

    df_score = pd.DataFrame(score_rows)
    st.dataframe(df_score, use_container_width=True, hide_index=True)

    # Download Golden Set CSV
    csv_path = export_golden_set_csv()
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_data = f.read()

    st.download_button(
        label="Download Golden Benchmark Dataset (CSV)",
        data=csv_data,
        file_name="groww_golden_set_benchmark.csv",
        mime="text/csv"
    )

    st.markdown("---")

    # 3. Failure Taxonomy Breakdown
    st.subheader("🔬 Prediction Discrepancies & Failure Taxonomy")
    classifier = FailureTaxonomyClassifier()
    diag = classifier.analyze_discrepancies(golden_items, predicted_items)

    st.write(f"Total Discrepancies: **{diag['total_discrepancies']} out of {len(golden_items)} items**")

    diag_rows = []
    for mode, mdata in diag.get("failure_taxonomy_distribution", {}).items():
        diag_rows.append({
            "Failure Mode": mode,
            "Mismatches": mdata["count"],
            "Share (%)": f"{mdata['pct']:.1f}%",
            "Linguistic / Behavioral Cause": mdata["description"]
        })

    df_diag = pd.DataFrame(diag_rows)
    st.dataframe(df_diag, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 4. Human-in-the-Loop Audit Log
    st.subheader("🛡️ Persistent Human Audit & Correction Log")
    st.markdown(
        "When an evaluator or Growth PM identifies an inaccurate model prediction, "
        "they record a persistent override in SQLite with a mandatory justification reason."
    )

    audit_mgr = AuditLogManager()
    audit_mgr.seed_default_cases()

    # Form to add a new correction
    with st.expander("➕ Submit New Human Correction / Override"):
        with st.form("new_audit_form"):
            c_fb_id = st.text_input("Feedback ID (e.g., gold_04, play_102)", "gold_04")
            c_field = st.selectbox("Field to Override", ["drop_trigger", "action_taken", "journey_stage", "emotion", "income_stability"])
            c_orig = st.text_input("Model Output (Original Value)", "optimistic")
            c_corr = st.text_input("Human Corrected Value", "frustrated")
            c_mode = st.selectbox("Failure Mode Tag", ["sarcasm_irony", "hinglish_ambiguity", "multi_topic_complexity", "missing_context", "implicit_trigger"])
            c_reason = st.text_area("Mandatory Justification Reason (min 10 characters):", "Sarcastic review inversion: User was enraged by bounce penalty, not optimistic.")
            submitted = st.form_submit_button("Record Human Correction")

            if submitted:
                try:
                    audit_mgr.add_correction(
                        feedback_id=c_fb_id,
                        field_corrected=c_field,
                        original_value=c_orig,
                        corrected_value=c_corr,
                        justification_reason=c_reason,
                        reviewer_id="growth_pm_ui",
                        failure_mode=c_mode
                    )
                    st.success("✅ Correction successfully recorded and persisted to database!")
                except Exception as e:
                    st.error(f"Failed to record correction: {e}")

    # Display all audit records
    corrections = audit_mgr.get_all_corrections()
    if corrections:
        df_corr = pd.DataFrame([
            {
                "Timestamp": c["created_at"][:19] if c.get("created_at") else "",
                "Feedback ID": c["feedback_id"],
                "Field": c["field_corrected"],
                "Model Output": c["original_value"],
                "Human Override": c["corrected_value"],
                "Failure Mode": c["failure_mode"],
                "Justification Reason": c["justification_reason"]
            }
            for c in corrections
        ])
        st.dataframe(df_corr, use_container_width=True, hide_index=True)

