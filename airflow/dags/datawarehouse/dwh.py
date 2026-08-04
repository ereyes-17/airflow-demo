from datawarehouse.datautils import get_conn_cursor, close_conn_cursor, create_schema, get_video_ids, create_table
from datawarehouse.dataloading import load_data
from datawarehouse.datamodification import insert_row, update_rows, delete_rows
from datawarehouse.data_transformation import transform_data

import logging
from airflow.decorators import task

logger = logging.getLogger(__name__)
TABLE = "yt_api"

@task
def staging_table():
    schema = "staging"

    curs, conn = None, None

    try:
        curs, conn = get_conn_cursor()

        YT_data = load_data()

        create_schema(schema)
        create_table(schema)

        table_ids = get_video_ids(curs, conn, schema)

        logger.info(YT_data)

        for row in YT_data:
            if len(table_ids) == 0:
                insert_row(curs, conn, schema, row)
            else:
                if row["videoId"] in table_ids:
                    update_rows(curs, conn, schema, row)
                else:
                    insert_row(curs, conn, schema, row)

        ids_in_json = {row["videoId"] for row in YT_data}

        ids_to_delete = set(table_ids) - ids_in_json

        if ids_to_delete:
            delete_rows(curs, conn, ids_to_delete)

        logger.info(f"{schema}.{TABLE} table update completed")
    except Exception as e:
        logger.error(f"A failure occurred while populating {schema}.{TABLE}", e)
        raise e

    finally:
        if conn and curs:
            close_conn_cursor(conn, curs)

@task
def core_table():
    schema = "core"

    curs, conn = None, None

    try:
        curs, conn = get_conn_cursor()

        YT_data = load_data()

        create_schema(schema)
        create_table(schema)

        table_ids = get_video_ids(curs, conn, schema)

        current_video_ids = set()

        curs.execute(f"SELECT * FROM staging.{TABLE}")
        rows = curs.fetchall()

        for row in rows:
            current_video_ids.add(row["Video_ID"])

            if len(table_ids) == 0:
                transformed_row = transform_data(row)
                insert_row(curs, conn, schema, transformed_row)

            else:
                transformed_row = transform_data(row)

                if transformed_row["Video_ID"] in table_ids:
                    update_rows(curs, conn, schema, transformed_row)
                else:
                    insert_row(curs, conn, schema, transformed_row)

        ids_to_delete = set(table_ids) - current_video_ids

        if ids_to_delete:
            delete_rows(curs, conn, schema, ids_to_delete)

        logger.info(f"{schema}.{TABLE} table update completed")
    except Exception as e:
        logger.error(f"A failure occurred while populating {schema}.{TABLE}", e)
        raise e

    finally:
        if conn and curs:
            close_conn_cursor(conn, curs)
