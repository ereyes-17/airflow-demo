import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = "MrBeast"

url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}"

def get_playlist_id() -> str:
    try:
        response = requests.get(url)

        data = response.json()

        channel_items = data["items"][0]

        channel_playlist_id = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]

        return channel_playlist_id
    except requests.exceptions.RequestException as e:
        raise e

if __name__ == "__main__":
    print(get_playlist_id)