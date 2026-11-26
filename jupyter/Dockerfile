# Servidor Jupyter para cuadernos de exploración (ver docs/jupyter.md).
# El digest fija lo que era `latest` el 2026-11-26 (constitución, regla 11: versiones fijadas).
FROM quay.io/jupyter/scipy-notebook:latest@sha256:21b93d2df02daa665b11442282d01f96d5a639e8ca9045cfd296e2896709b2fc

RUN pip install --no-cache-dir "plotly==7.2.0" "psycopg[binary]==3.3.9" "sqlalchemy==2.1.9"
