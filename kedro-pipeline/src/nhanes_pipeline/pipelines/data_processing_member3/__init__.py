"""Pipeline de Procesamiento — Miembro 3 (Matías Retamal).

Módulos:
    nodes:    Nodos Bronze → Silver → Gold para Laboratory & Limited Access.
    pipeline: Definición del grafo DAG de Kedro.
"""
from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
