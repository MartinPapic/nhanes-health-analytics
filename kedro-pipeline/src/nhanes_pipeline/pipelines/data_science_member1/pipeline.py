from kedro.pipeline import Pipeline, node, pipeline
from .nodes import calculate_healthy_aging_score, define_longevity_groups

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=calculate_healthy_aging_score,
                inputs="member1_silver",
                outputs="member1_intermediate_gold",
                name="calculate_healthy_aging_score_node",
            ),
            node(
                func=define_longevity_groups,
                inputs="member1_intermediate_gold",
                outputs="member1_gold",
                name="define_longevity_groups_node",
            ),
        ]
    )
