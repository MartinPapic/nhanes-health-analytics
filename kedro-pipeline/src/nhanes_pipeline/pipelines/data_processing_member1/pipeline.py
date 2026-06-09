from kedro.pipeline import Pipeline, node, pipeline
from .nodes import merge_and_clean_silver_layer

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=merge_and_clean_silver_layer,
            inputs="ingestion_status",
            outputs="member1_silver",
            name="merge_and_clean_silver_layer_node"
        )
    ])
