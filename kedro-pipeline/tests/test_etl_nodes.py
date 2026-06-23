import pandas as pd
import pytest

from nhanes_pipeline.pipelines.data_processing_member1.nodes import validate_silver_layer

def test_validate_silver_layer_empty():
    df = pd.DataFrame()
    valid, rejected = validate_silver_layer(df)
    assert valid.empty
    assert rejected.empty

def test_validate_silver_layer_valid_data():
    data = {
        'SEQN': [1, 2, 3],
        'RIDAGEYR': [25, 40, 80],
        'RIAGENDR': [1.0, 2.0, 1.0]
    }
    df = pd.DataFrame(data)
    valid, rejected = validate_silver_layer(df)
    
    assert len(valid) == 3
    assert len(rejected) == 0

def test_validate_silver_layer_invalid_data():
    data = {
        'SEQN': [1, 2, None, 4, 5],
        'RIDAGEYR': [25, 15, 80, 130, 40], # 15 is < 20, 130 is > 120
        'RIAGENDR': [1.0, 2.0, 1.0, 1.0, 3.0] # 3.0 is invalid gender
    }
    df = pd.DataFrame(data)
    valid, rejected = validate_silver_layer(df)
    
    # Solo el registro 1 (SEQN 1) es completamente válido
    assert len(valid) == 1
    assert valid.iloc[0]['SEQN'] == 1
    
    # 4 registros deben ser rechazados
    assert len(rejected) == 4
    assert 'rejection_reason' in rejected.columns
    assert all(rejected['rejection_reason'] == "Fallo de validación en SEQN, Edad o Género")
