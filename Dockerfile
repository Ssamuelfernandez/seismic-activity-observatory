# Imagen Python compartida por productor, consumidor y API (A3).
# Cada servicio la usa con un comando distinto (ver compose.yaml).
# Versión exacta de Python: debe coincidir con .python-version.
FROM python:3.12.16-slim-bookworm AS production

# uv instala las dependencias exactas de uv.lock; la versión del binario también está fijada.
COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/app

WORKDIR /app

# Capa de dependencias: solo se reconstruye si cambian pyproject.toml o uv.lock.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

# Código: common/ va en la misma raíz que los servicios para que todos puedan importarlo.
COPY common ./common
COPY producer ./producer
COPY consumer ./consumer
COPY api ./api
COPY historical ./historical

RUN useradd --system --uid 10001 --no-create-home observatory
USER observatory

# Etapa de pruebas (no es la imagen por defecto): production + dependencias del grupo dev.
# Solo la usa el servicio `tests` de compose.yaml (perfil `test`).
FROM production AS test
USER root
RUN uv sync --frozen --no-install-project
USER observatory
