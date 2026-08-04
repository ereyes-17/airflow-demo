import logging
from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)

SODA_PATH = "/opt/airflow/include/soda"
DATASOURCE = "pg_datasource"

def yt_elt_data_quality(schema):
    try:
        task = BashOperator(
            task_id=f"soda_test{schema}",
            bash_command=f"soda scan -d {DATASOURCE} -c {SODA_PATH}/configuration.yml -v SCHEMA={schema} {SODA_PATH}/checks.yml"
        )
        return task
    except Exception as e:
        logger.error(f"Error running dq for schema: {schema}")
        raise e

def test_connection():
    try:
        task = BashOperator(
            task_id="test-soda-postgres-connection",
            bash_command=f"soda test-connection -d {DATASOURCE} -c {SODA_PATH}/configuration.yml -V"
        )
        return task
    except Exception as e:
        logger.error(f"Soda-Postgres Test Connection failed")
        raise e