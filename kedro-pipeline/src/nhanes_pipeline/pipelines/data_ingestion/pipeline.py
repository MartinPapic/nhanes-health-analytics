from kedro.pipeline import Pipeline, node, pipeline
from .nodes import download_cdc_data

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=download_cdc_data,
            inputs=None,
            outputs="ingestion_status",
            name="download_cdc_data_node"
        )
    ])
