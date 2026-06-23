from kedro.pipeline import Pipeline, node, pipeline
from .nodes import merge_and_clean_silver_layer, transform_silver_to_gold


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=merge_and_clean_silver_layer,
            inputs="ingestion_status",
            outputs="member2_silver",
            name="merge_and_clean_silver_layer_member2"
        ),
        node(
            func=transform_silver_to_gold,
            inputs="member2_silver",
            outputs="member2_gold",
            name="transform_silver_to_gold_member2"
        )
    ])