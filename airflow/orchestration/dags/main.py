from airflow import DAG
from datetime import datetime, timedelta
from api.video_stats import get_playlist_id, get_video_ids, extracted_video_data, save_to_json
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
) as dag:
    # define tasks
    playlist_id = get_playlist_id()
    video_ids = get_video_ids(playlist_id)
    extracted_data = extracted_video_data(video_ids)
    save_to_json_task = save_to_json(extracted_data)

    # define deps
    playlist_id >> video_ids >> extracted_data >> save_to_json_task