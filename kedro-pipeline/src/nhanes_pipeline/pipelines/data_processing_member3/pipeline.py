"""Pipeline DAG — Member 3: Laboratory & Limited Access.

Author: Matías Retamal

Execution graph:
    ingestion_status
      ├─► ingest_laboratory_bronze_node      → member3_lab_bronze
      ├─► ingest_limited_access_bronze_node  → member3_ltd_bronze
      └─► extract_data_dictionary_node       → member3_data_dictionary

    member3_lab_bronze → process_laboratory_silver_node
      ├─► member3_lab_silver
      └─► member3_lab_rejected

    member3_ltd_bronze → process_limited_access_silver_node
      ├─► member3_ltd_silver
      └─► member3_ltd_rejected

    (member3_lab_silver, member3_ltd_silver) → build_laboratory_gold_node
      └─► member3_gold

    (member3_lab_silver, member3_lab_rejected,
     member3_ltd_silver, member3_ltd_rejected) → generate_quality_report_node
      └─► member3_quality_report

    (member3_gold, params:postgres_credentials) → export_gold_to_postgres_node
      └─► member3_postgres_status
"""
from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    build_laboratory_gold,
    export_gold_to_postgres,
    extract_data_dictionary,
    generate_quality_report,
    ingest_laboratory_bronze,
    ingest_limited_access_bronze,
    process_laboratory_silver,
    process_limited_access_silver,
)


def create_pipeline(**kwargs) -> Pipeline:
    """Return the complete Member-3 Kedro pipeline.

    Tags:
        ``bronze``        — raw ingestion nodes.
        ``silver``        — validation and cleaning nodes.
        ``gold``          — feature engineering node.
        ``quality``       — data quality reporting node.
        ``export``        — PostgreSQL export node.
        ``member3``       — all nodes in this pipeline.
        ``laboratory``    — lab-data-specific nodes.
        ``limited_access``— mortality-data-specific nodes.
    """
    return pipeline([
        # ── BRONZE ──────────────────────────────────────────────────────────
        node(
            func=ingest_laboratory_bronze,
            inputs="ingestion_status",
            outputs="member3_lab_bronze",
            name="ingest_laboratory_bronze_node",
            tags=["bronze", "member3", "laboratory"],
        ),
        node(
            func=ingest_limited_access_bronze,
            inputs="ingestion_status",
            outputs="member3_ltd_bronze",
            name="ingest_limited_access_bronze_node",
            tags=["bronze", "member3", "limited_access"],
        ),
        node(
            func=extract_data_dictionary,
            inputs="ingestion_status",
            outputs="member3_data_dictionary",
            name="extract_data_dictionary_node",
            tags=["bronze", "member3", "documentation"],
        ),
        # ── SILVER ──────────────────────────────────────────────────────────
        node(
            func=process_laboratory_silver,
            inputs="member3_lab_bronze",
            outputs=["member3_lab_silver", "member3_lab_rejected"],
            name="process_laboratory_silver_node",
            tags=["silver", "member3", "laboratory"],
        ),
        node(
            func=process_limited_access_silver,
            inputs="member3_ltd_bronze",
            outputs=["member3_ltd_silver", "member3_ltd_rejected"],
            name="process_limited_access_silver_node",
            tags=["silver", "member3", "limited_access"],
        ),
        # ── GOLD ────────────────────────────────────────────────────────────
        node(
            func=build_laboratory_gold,
            inputs=["member3_lab_silver", "member3_ltd_silver"],
            outputs="member3_gold",
            name="build_laboratory_gold_node",
            tags=["gold", "member3"],
        ),
        # ── QUALITY REPORT ──────────────────────────────────────────────────
        node(
            func=generate_quality_report,
            inputs=[
                "member3_lab_silver",
                "member3_lab_rejected",
                "member3_ltd_silver",
                "member3_ltd_rejected",
            ],
            outputs="member3_quality_report",
            name="generate_quality_report_node",
            tags=["quality", "member3"],
        ),
        # ── EXPORT ──────────────────────────────────────────────────────────
        node(
            func=export_gold_to_postgres,
            inputs=["member3_gold", "params:postgres_credentials"],
            outputs="member3_postgres_status",
            name="export_gold_to_postgres_node",
            tags=["export", "postgres", "member3"],
        ),
    ])
