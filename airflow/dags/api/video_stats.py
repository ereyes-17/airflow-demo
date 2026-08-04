import requests
import json
import os
from datetime import date
from airflow.models import Variable
from airflow.decorators import task

MAX_RESULTS = 50


def _get_api_key() -> str:
    return Variable.get("API_KEY")


def _get_channel_handle() -> str:
    return Variable.get("CHANNEL_HANDLE")


@task
def get_playlist_id() -> str:
    api_key = _get_api_key()
    channel_handle = _get_channel_handle()
    url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={channel_handle}&maxResults={MAX_RESULTS}&key={api_key}"

    try:
        response = requests.get(url)

        data = response.json()

        channel_items = data["items"][0]

        channel_playlist_id = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]

        return channel_playlist_id
    except requests.exceptions.RequestException as re:
        raise re

@task
def get_video_ids(playlist_id: str) -> list[str]:
    api_key = _get_api_key()
    video_ids = []

    page_token = None

    base_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={MAX_RESULTS}&playlistId={playlist_id}&key={api_key}"

    try:
        while True:
            url = base_url

            if page_token:
                url += f"&pageToken={page_token}"

            response = requests.get(url)

            response.raise_for_status()

            data = response.json()

            for item in data.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_ids.append(video_id)

            page_token = data.get("nextPageToken") # default is None

            if not page_token:
                break
            
    except requests.exceptions.RequestException as e:
        raise e

    return video_ids

@task
def extracted_video_data(video_ids):
    api_key = _get_api_key()
    extracted_data = []

    def batch_list(video_ids: list[str], batch_size):
        for video_id in range(0, len(video_ids), batch_size):
            yield video_ids[video_id: video_id + batch_size]

    try:
        for batch in batch_list(video_ids, MAX_RESULTS):
            video_ids_str = ",".join(batch)

            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=snippet&part=statistics&id={video_ids_str}&key={api_key}"

            response = requests.get(url)

            response.raise_for_status()

            data = response.json()

            for item in data.get("items", []):
                video_id = item["id"]
                snippet = item["snippet"]
                content_details = item["contentDetails"]
                statistics = item["statistics"]

                video_data = {
                    "videoId": video_id,
                    "title": snippet["title"],
                    "publishedAt": snippet["publishedAt"],
                    "duration": content_details["duration"],
                    "viewCount": statistics.get("viewCount", None),
                    "likeCount": statistics.get("likeCount", None),
                    "commentCount": statistics.get("commentCount", None)
                }

                extracted_data.append(video_data)

        return extracted_data

    except requests.exceptions.RequestException as e:
        raise e

@task
def save_to_json(extracted_data):
    data_dir = os.path.join(os.environ.get("AIRFLOW_HOME", "/opt/airflow"), "data")
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, f"YT_data_{date.today()}.json")
    with open(file_path, 'w', encoding='utf-8') as json_outfile:
        json.dump(extracted_data, json_outfile, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # These decorators turn the functions into Airflow task constructors.
    # When running outside Airflow, call the underlying Python callable directly.
    playlist_id = get_playlist_id.python_callable()

    video_ids = get_video_ids.python_callable(playlist_id)
    print(f"Found {len(video_ids)} videos for playlist id {playlist_id}.")

    extracted_videos = extracted_video_data.python_callable(video_ids)

    save_to_json.python_callable(extracted_videos)