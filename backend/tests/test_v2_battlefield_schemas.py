from datetime import UTC, datetime

from app.schemas import BattlefieldData

NOW = datetime(2026, 5, 29, 10, 0, tzinfo=UTC)


def test_battlefield_data_extension_preserves_existing_contract_fields() -> None:
    data = BattlefieldData.model_validate(
        {
            "battlefield_id": "battlefield_task_001_all",
            "task_id": "task_001",
            "generated_at": NOW,
            "selected_slice": {},
            "available_slices": [],
            "graph_nodes": [],
            "graph_edges": [],
            "score_explanations": [],
            "decision_chain": [],
            "evidence_cards": [],
            "qa_summary": {
                "qa_status": "passed",
                "review_task_count": 0,
                "open_review_task_count": 0,
                "resolved_review_task_count": 0,
                "revision_message_count": 0,
                "risk_edge_ids": [],
                "risk_claim_ids": [],
                "review_task_ids": [],
            },
            "metadata": {},
        }
    )

    assert data.key_relations == []
    assert data.graph_edges == []
    assert data.qa_summary.qa_status == "passed"
