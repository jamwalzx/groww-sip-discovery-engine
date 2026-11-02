import os
import sys
import json
import logging
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path

from src.db.database import get_db
from src.db.models import RawFeedback, CleanedFeedback, ExtractedInsight, Theme, OpportunityScoreRecord
from src.analytics.opportunity_matrix import OpportunityMatrixCalculator
from src.analytics.segmentation import SegmentAnalyzer
from src.analytics.cohort_comparison import CohortComparator
from src.analytics.question_views import QuestionViewAggregator

from src.evals.golden_set import get_golden_benchmark
from src.evals.metrics import EvaluationHarness
from src.evals.failure_taxonomy import FailureTaxonomyClassifier
from src.evals.audit_log import AuditLogManager
from src.evals.bias_panel import SourceBiasAuditor
from src.pipeline.extractor import StructuredExtractor

STATIC_DIR = Path(__file__).resolve().parent / "static"

class StitchUIHandler(SimpleHTTPRequestHandler):
    """
    HTTP handler serving the Stitch UI static prototype with live SQLite metrics and analytics.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with get_db() as db:
                raw_count = db.query(RawFeedback).count()
                clean_count = db.query(CleanedFeedback).filter(CleanedFeedback.is_duplicate == False, CleanedFeedback.is_spam == False).count()
                insights_count = db.query(ExtractedInsight).count()
                themes_count = db.query(Theme).count()
                opp_count = db.query(OpportunityScoreRecord).count()

                payload = {
                    "raw_count": raw_count,
                    "clean_count": clean_count,
                    "insights_count": insights_count,
                    "themes_count": themes_count,
                    "opportunity_scores_count": opp_count,
                }
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif self.path == "/api/opportunity-matrix":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with get_db() as db:
                records = db.query(OpportunityScoreRecord).order_by(OpportunityScoreRecord.rank.asc()).all()
                payload = [r.to_dict() for r in records]
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif self.path == "/api/segments":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            analyzer = SegmentAnalyzer()
            payload = analyzer.compute_all_segments()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif self.path == "/api/cohorts":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            comparator = CohortComparator()
            payload = comparator.compute_all()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif self.path == "/api/questions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            aggregator = QuestionViewAggregator()
            payload = aggregator.get_all_questions()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif self.path == "/api/evals":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            golden_items = get_golden_benchmark()
            extractor = StructuredExtractor()
            predicted_items = [extractor.extract(it["raw_text"]).model_dump() for it in golden_items]
            harness = EvaluationHarness()
            results = harness.evaluate(golden_items, predicted_items)
            diag = FailureTaxonomyClassifier().analyze_discrepancies(golden_items, predicted_items)
            payload = {
                "evaluation_scorecard": results,
                "failure_diagnostics": diag
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif self.path == "/api/audit-log":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            audit_mgr = AuditLogManager()
            audit_mgr.seed_default_cases()
            payload = audit_mgr.get_all_corrections()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif self.path == "/api/bias":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            bias_auditor = SourceBiasAuditor()
            payload = bias_auditor.audit()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        else:
            super().do_GET()

def run_server(port=8080):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, StitchUIHandler)
    print(f"\n=======================================================")
    print(f" Groww AI Engine Stitch UI Server Active")
    print(f" Local URL: http://localhost:{port}/")
    print(f" Serving Directory: {STATIC_DIR}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Stitch UI server.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)

