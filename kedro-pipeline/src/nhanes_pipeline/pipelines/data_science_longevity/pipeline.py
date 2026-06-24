from kedro.pipeline import Pipeline, node, pipeline
from .nodes import merge_and_feature_engineer, train_tpot_automl

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=merge_and_feature_engineer,
            inputs=["member1_gold", "member2_gold", "member3_gold"],
            outputs="master_longevity_dataset",
            name="merge_and_feature_engineer_node"
        ),
        node(
            func=train_tpot_automl,
            inputs="master_longevity_dataset",
            outputs="longevity_model",
            name="train_tpot_automl_node"
        )
    ])
