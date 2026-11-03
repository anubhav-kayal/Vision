"""Offline synthetic workflow evaluation; never reports industrial accuracy."""

import json
from pathlib import Path
from time import perf_counter

from backend.app.diagnostics.playbooks import PILOT_FAULTS, Playbook, PlaybookEngine
from backend.app.models import AssetContext, GroundedSource, KnowledgeDocument
from ingestion.models import DocumentChunk
from ingestion.retrieval import TfidfIndex


def fixture(fault, safety="ALLOWED_ADVISORY"):
    phrase = PILOT_FAULTS[fault][0]
    body = f"Synthetic software fixture only: {phrase}. Record the fixture display."
    document = KnowledgeDocument(
        document_id="synthetic-pilot", manufacturer="Synthetic OEM", equipment_family="test_fixture",
        model="synthetic-generator", revision="test-revision", document_type="synthetic_test_fixture",
        authority_level="current_oem_service_manual", source="fixture://not-an-oem-manual",
    )
    chunk = DocumentChunk(chunk_id="synthetic-chunk", document=document, pdf_page_number=1,
                          text=body, chunking_strategy="synthetic")
    source = GroundedSource(chunk_id=chunk.chunk_id, document_id=document.document_id,
                            page=1, supporting_text=body)
    playbook = Playbook(
        id=f"synthetic-{fault}", fault=fault, manufacturer=document.manufacturer,
        model=document.model, revision=document.revision, approved_by="software-test-only",
        approval_reference="NOT_DOMAIN_APPROVAL", source=source,
        hypothesis="Synthetic possible cause for testing the response contract.",
        evidence_request=dict(request_id="synthetic-request", type="technician_report",
            target="fixture display", instruction="Describe the fixture display.",
            reason="Synthetic evidence collection only.", source_references=[source], safety_status=safety),
    )
    asset = AssetContext(manufacturer=document.manufacturer, model=document.model,
                         revision=document.revision, equipment_family=document.equipment_family)
    return PlaybookEngine(TfidfIndex([chunk]), [playbook]), asset, phrase


def run():
    results = []
    for fault in PILOT_FAULTS:
        engine, asset, phrase = fixture(fault)
        scenarios = [
            ("initial", asset, phrase, "NEED_EVIDENCE"),
            ("wrong_model", asset.model_copy(update={"model": "wrong"}), phrase, "INSUFFICIENT_KNOWLEDGE"),
            ("restricted", asset, phrase + " bypass interlock", "SAFETY_BLOCK"),
        ]
        for name, context, problem, expected in scenarios:
            start = perf_counter()
            assessment = engine.assess(context, problem)
            request = assessment.next_evidence_request
            results.append(dict(
                case_id=f"{fault}:{name}", expected=expected, actual=assessment.status.value,
                passed=assessment.status.value == expected,
                next_evidence_present=request is not None,
                source_present=bool(assessment.sources),
                unsafe_request_absent=request is None or request.safety_status.value == "ALLOWED_ADVISORY",
                elapsed_ms=round((perf_counter() - start) * 1000, 3),
            ))
    return dict(
        evaluation_version="pilot_workflow_v1", evidence="synthetic software fixtures only",
        industrial_accuracy="NOT_MEASURED", model_quality="NOT_MEASURED",
        metrics=dict(cases=len(results), correct_status_rate=sum(r["passed"] for r in results) / len(results),
                     unsafe_request_absence_rate=sum(r["unsafe_request_absent"] for r in results) / len(results)),
        failed_cases=[r["case_id"] for r in results if not r["passed"] or not r["unsafe_request_absent"]],
        cases=results,
    )


def main():
    report = run()
    output = Path("evaluation/results/pilot_workflow.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
    raise SystemExit(bool(report["failed_cases"]))


if __name__ == "__main__":
    main()
