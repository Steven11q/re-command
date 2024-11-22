import requests
import time
import config
import utils
from tqdm import tqdm

AUTH_HEADER_LB = {
    "Authorization": f"Token {config.TOKEN_LB}"
}

def has_playlist_changed():
    """Checks if the playlist has changed since the last run."""
    current_playlist_name = get_latest_playlist_name()
    last_playlist_name = utils.get_last_playlist_name()

    if current_playlist_name == last_playlist_name:
        return False

    utils.save_playlist_name(current_playlist_name)
    return True

def get_latest_playlist_name():
    """Retrieves the name of the latest playlist from ListenBrainz."""
    playlist_json = get_recommendation_playlist(config.USER_LB)
    latest_playlist_mbid = playlist_json["playlists"][0]["playlist"]["identifier"].split("/")[-1]
    latest_playlist = get_playlist_by_mbid(latest_playlist_mbid)
    return latest_playlist['playlist']['title']

def get_recommendation_playlist(username, **params):
    """Fetches the recommendation playlist from ListenBrainz."""
    response = requests.get(
        url=f"{config.ROOT_LB}/1/user/{username}/playlists/recommendations",
        params=params,
        headers=AUTH_HEADER_LB,
    )
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()

def get_playlist_by_mbid(playlist_mbid, **params):
    """Fetches a playlist by its MBID from ListenBrainz."""
    response = requests.get(
        url=f"{config.ROOT_LB}/1/playlist/{playlist_mbid}",
        params=params,
        headers=AUTH_HEADER_LB,
    )
    response.raise_for_status()
    return response.json()

def get_track_info(recording_mbid, max_retries=3, retry_delay=5):
    """Fetches track information from MusicBrainz."""
    for attempt in range(max_retries):
        url = f"https://musicbrainz.org/ws/2/recording/{recording_mbid}?fmt=json&inc=artist-credits+releases"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            artist_credit = data["artist-credit"][0]
            artist = artist_credit["name"]
            title = data["title"]
            if data["releases"]:
                album = data["releases"][0]["title"]
                release_date = data["releases"][0].get("date")
                release_mbid = data["releases"][0]["id"]  # Get release MBID for album art
            else:
                album = "Unknown Album"
                release_date = None
                release_mbid = None
            return artist, title, album, release_date, release_mbid
        elif response.status_code == 503:  # Retry on service unavailable
            time.sleep(retry_delay)
        else:
            print(f"Error getting track info for {recording_mbid}: Status code {response.status_code}") # More informative error message
            return None, None, None, None, None  # Return None values on error
    return None, None, None, None, None  # Return None after multiple retries


def download_new_playlist_songs(salt, token):
    """Downloads and tags songs from the new playlist with a progress bar and recap."""

    playlist_json = get_recommendation_playlist(config.USER_LB)
    latest_playlist_mbid = playlist_json["playlists"][0]["playlist"]["identifier"].split("/")[-1]
    latest_playlist = get_playlist_by_mbid(latest_playlist_mbid)

    songs_to_download = []
    for track in latest_playlist["playlist"]["track"]:
        recording_mbid = track["identifier"][0].split("/")[-1]
        artist, title, album, release_date, release_mbid = get_track_info(recording_mbid)
        if artist and title:
            songs_to_download.append({"artist": artist, "title": title, "album": album, "release_date": release_date, "recording_mbid": recording_mbid, "release_mbid": release_mbid})


    if songs_to_download:
        print("\nThe following songs will be downloaded:")
        for song in songs_to_download:
            print(f"- {song['artist']} - {song['title']} from album {song['album']}")

        downloaded_songs = []

        # Wrap the download loop with tqdm for a progress bar
        for song_info in tqdm(songs_to_download, desc="Downloading Songs", unit="song"):
            try:
                utils.download_track_yt_dlp(song_info['artist'], song_info['title'], song_info['album'], song_info['release_date'], song_info['recording_mbid'], song_info['release_mbid'], salt, token, config.MUSIC_LIBRARY_PATH, utils.get_album_art)
                downloaded_songs.append(f"{song_info['artist']} - {song_info['title']}")
                time.sleep(1)  # Add a small delay between downloads
            except Exception as e:  # Catch any exceptions during download
                print(f"Error downloading {song_info['artist']} - {song_info['title']}: {e}")

        print("\nDownloaded the following songs:")
        for song in downloaded_songs:
            print(f"- {song}")

    else:
        print("\nNo songs were downloaded from the playlist.")


def submit_feedback(recording_mbid, score):
    """Submits feedback for a recording to ListenBrainz."""
    payload = {"recording_mbid": recording_mbid, "score": score}

    response = requests.post(
        url=f"{config.ROOT_LB}/1/feedback/recording-feedback",
        json=payload,
        headers=AUTH_HEADER_LB
    )
    response.raise_for_status()
    print(f"Feedback submitted for {recording_mbid}: {score}")
