"""Pipeline DAG — Miembro 3: Laboratory & Limited Access.

Autor: Matías Retamal
Trello: [ETL-03] Pipelines Kedro modulares.

Grafo de ejecución:
    ingestion_status
        ├─► ingest_laboratory_bronze_node    → member3_lab_bronze
        ├─► ingest_limited_access_bronze_node → member3_ltd_bronze
        └─► extract_data_dictionary_node      → member3_data_dictionary

    member3_lab_bronze
        └─► process_laboratory_silver_node
              ├─► member3_lab_silver
              └─► member3_lab_rejected

    member3_ltd_bronze
        └─► process_limited_access_silver_node
              ├─► member3_ltd_silver
              └─► member3_ltd_rejected

    (member3_lab_silver, member3_ltd_silver)
        └─► build_laboratory_gold_node → member3_gold

    member3_gold
        └─► export_gold_to_postgres_node → member3_postgres_status
"""
from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    build_laboratory_gold,
    export_gold_to_postgres,
    extract_data_dictionary,
    ingest_laboratory_bronze,
    ingest_limited_access_bronze,
    process_laboratory_silver,
    process_limited_access_silver,
)


def create_pipeline(**kwargs) -> Pipeline:
    """Crea y retorna el pipeline completo del Miembro 3.

    Returns:
        Pipeline: DAG Kedro con nodos Bronze → Silver → Gold → PostgreSQL.
    """
    return pipeline(
        [
            # ------------------------------------------------------------------
            # BRONZE — Ingesta desde 01_raw
            # ------------------------------------------------------------------
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
            # ------------------------------------------------------------------
            # SILVER — Validación y limpieza
            # ------------------------------------------------------------------
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
            # ------------------------------------------------------------------
            # GOLD — Feature Engineering
            # ------------------------------------------------------------------
            node(
                func=build_laboratory_gold,
                inputs=["member3_lab_silver", "member3_ltd_silver"],
                outputs="member3_gold",
                name="build_laboratory_gold_node",
                tags=["gold", "member3"],
            ),
            # ------------------------------------------------------------------
            # EXPORT — PostgreSQL
            # ------------------------------------------------------------------
            node(
                func=export_gold_to_postgres,
                inputs=["member3_gold", "params:postgres_credentials"],
                outputs="member3_postgres_status",
                name="export_gold_to_postgres_node",
                tags=["export", "postgres", "member3"],
            ),
        ]
    )
