from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from api.video_stats import get_playlist_id, get_video_ids, extracted_video_data, save_to_json
from dataquality.soda import yt_elt_data_quality, test_connection
import pendulum

local_tz = pendulum.timezone("America/New_York")

default_args = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "data@engineers.com",
    # "retries": 1,
    # "retry_delay": timedelta(hours=1),
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(hours=1),
    "start_date": datetime(2025, 1, 1, tzinfo=local_tz),
    # "end_date": datetime(2030, 1, 1, tzinfo=local_tz)
}

with DAG(
    dag_id="produce_json",
    default_args=default_args,
    description="produces a json with youtube video statistics and metadata",
    schedule="0 14 * * *",
    catchup=False,
) as produce_json_dag:
    # define tasks
    playlist_id = get_playlist_id()
    video_ids = get_video_ids(playlist_id)
    extracted_data = extracted_video_data(video_ids)
    save_to_json_task = save_to_json(extracted_data)

    # define as a trigger
    trigger_update_db = TriggerDagRunOperator(
        task_id="trigger_update_db",
        trigger_dag_id="update_db"
    )

    # define deps
    playlist_id >> video_ids >> extracted_data >> save_to_json_task >> trigger_update_db

from datawarehouse.dwh import staging_table, core_table

with DAG(
    dag_id="update_db",
    default_args=default_args,
    description="DAG to process youtube json data into datawarehouse",
    schedule=None,
    catchup=False
) as update_db_dag:
    update_staging = staging_table()
    update_core = core_table()

    trigger_data_quality = TriggerDagRunOperator(
        task_id="trigger_data_quality",
        trigger_dag_id="data_quality"
    )

    update_staging >> update_core >> trigger_data_quality

with DAG(
    dag_id="data_quality",
    default_args=default_args,
    description="DAG to check dq on both db layer",
    schedule=None,
    catchup=False
) as data_quality_dag:
    soda_test_connection = test_connection()
    soda_validate_staging = yt_elt_data_quality("staging")
    soda_validate_core = yt_elt_data_quality("core")

    soda_test_connection >> soda_validate_staging >> soda_validate_core