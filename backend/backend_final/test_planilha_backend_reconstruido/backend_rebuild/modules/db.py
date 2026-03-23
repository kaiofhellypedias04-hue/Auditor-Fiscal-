import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from dotenv import load_dotenv

# Carrega SEMPRE o .env da raiz do projeto (mesma pasta do main.py)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_PATH)


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            f"DATABASE_URL não está definido. Verifique o arquivo .env em: {ENV_PATH}"
        )
    return url


@contextmanager
def get_conn():
    conn = psycopg.connect(get_database_url(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
