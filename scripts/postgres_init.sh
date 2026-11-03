#!/usr/bin/env bash
# Inicialización de PostgreSQL en la PRIMERA creación del volumen (A5, FR-020, FR-027).
# La imagen oficial ejecuta los archivos de /docker-entrypoint-initdb.d solo si el directorio
# de datos está vacío; los arranques posteriores no lo repiten.
#
# 1) Aplica sql/001_schema.sql tal cual (esquema del contrato; no crea roles).
# 2) Aplica sql/002_roles.sql con las contraseñas leídas de variables de entorno.
set -euo pipefail

: "${POSTGRES_USER:?Falta POSTGRES_USER}"
: "${POSTGRES_DB:?Falta POSTGRES_DB}"
: "${DB_API_PASSWORD:?Falta DB_API_PASSWORD}"
: "${DB_PRODUCER_PASSWORD:?Falta DB_PRODUCER_PASSWORD}"
: "${DB_CONSUMER_PASSWORD:?Falta DB_CONSUMER_PASSWORD}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -f /sql/001_schema.sql

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -v api_password="$DB_API_PASSWORD" \
    -v producer_password="$DB_PRODUCER_PASSWORD" \
    -v consumer_password="$DB_CONSUMER_PASSWORD" \
    -f /sql/002_roles.sql
