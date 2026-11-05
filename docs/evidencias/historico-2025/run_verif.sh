docker compose exec -T postgres sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB' < docs/evidencias/historico-2025/verificacion.sql
