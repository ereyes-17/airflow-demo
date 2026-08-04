from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection

TABLE = "yt_api"

def _get_db_conn_id() -> str:
    return "POSTGRES_DB_YT_ELT"


def _get_elt_db_name() -> str:
    return Variable.get("ELT_DATABASE_NAME")

def get_conn_cursor() -> tuple[RealDictCursor, connection]:
    hook = PostgresHook(postgres_conn_id=_get_db_conn_id(), database=_get_elt_db_name())

    conn: connection = hook.get_conn()

    curs: RealDictCursor = conn.cursor(cursor_factory=RealDictCursor)

    return curs, conn

def close_conn_cursor(conn: connection, curs: RealDictCursor):
    curs.close()
    conn.close()

def create_schema(schema: str):
    curs, conn = get_conn_cursor()

    schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema}"

    curs.execute(schema_sql)

    conn.commit()

    close_conn_cursor(conn, curs)

def create_table(schema: str):
    curs, conn = get_conn_cursor()

    if schema == "staging":
        table_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.{TABLE} (
                "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                "Video_Title" TEXT NOT NULL,
                "Video_Views" INT,
                "Upload_Date" TIMESTAMP NOT NULL,
                "Duration" VARCHAR(20) NOT NULL,
                "Likes_Count" INT,
                "Comments_Count" INT
            );
        """
    else:
        table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {schema}.{TABLE} (
                        "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                        "Video_Title" TEXT NOT NULL,
                        "Video_Views" INT,
                        "Upload_Date" TIMESTAMP NOT NULL,
                        "Duration" VARCHAR(20) NOT NULL,
                        "Likes_Count" INT,
                        "Comments_Count" INT
                    );
                """

    curs.execute(table_sql)

    conn.commit()

    close_conn_cursor(conn, curs)

def get_video_ids(curs: RealDictCursor, conn: connection, schema: str) -> list[str]:
    curs.execute(f"""SELECT "Video_ID" FROM {schema}.{TABLE};""")
    ids = curs.fetchall()

    video_ids = [row["Video_ID"] for row in ids]

    return video_ids