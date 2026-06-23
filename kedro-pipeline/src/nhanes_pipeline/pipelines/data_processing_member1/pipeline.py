from kedro.pipeline import Pipeline, node, pipeline
from .nodes import merge_and_clean_silver_layer, validate_silver_layer

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=merge_and_clean_silver_layer,
            inputs="ingestion_status",
            outputs="member1_silver_raw",
            name="merge_and_clean_silver_layer_node"
        ),
        node(
            func=validate_silver_layer,
            inputs="member1_silver_raw",
            outputs=["member1_silver", "member1_rejected"],
            name="validate_silver_layer_node"
        )
    ])
