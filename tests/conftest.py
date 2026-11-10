import os

import pytest

from shopping_agent.agent.memory import PG_URL_ENV


@pytest.fixture
def pg_url():
    """Postgres real, solo si está configurado y responde; si no, se omite la prueba."""
    url = os.environ.get(PG_URL_ENV)
    if not url:
        pytest.skip(f"{PG_URL_ENV} no está definida")
    import psycopg

    try:
        psycopg.connect(url, connect_timeout=3).close()
    except psycopg.OperationalError as error:
        pytest.skip(f"Postgres no responde: {error}")
    return url
