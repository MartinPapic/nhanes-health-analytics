"""Project pipeline registry."""
from typing import Dict
from kedro.pipeline import Pipeline

from nhanes_pipeline.pipelines import data_ingestion, data_processing_member1, data_processing_member2, data_science_member1

def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines."""
    ingestion_pipeline = data_ingestion.create_pipeline()
    processing_member1_pipeline = data_processing_member1.create_pipeline()
    processing_member2_pipeline = data_processing_member2.create_pipeline()
    data_science_member1_pipeline = data_science_member1.create_pipeline()
    
    return {
        "ingestion": ingestion_pipeline,
        "processing_m1": processing_member1_pipeline,
        "processing_m2": processing_member2_pipeline,
        "data_science_m1": data_science_member1_pipeline,
        "__default__": ingestion_pipeline + processing_member1_pipeline + processing_member2_pipeline + data_science_member1_pipeline
    }
