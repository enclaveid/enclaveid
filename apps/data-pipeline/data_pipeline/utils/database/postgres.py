from cuid2 import Cuid
from sqlalchemy import make_url

CUID_GENERATOR = Cuid(length=25)


def conn_string_to_conn_args(conn_string: str):
    url = make_url(conn_string)
    return {
        "host": url.host,
        "port": url.port,
        "user": url.username,
        "password": url.password,
        "dbname": url.database,
    }


def generate_cuid():
    return CUID_GENERATOR.generate()
