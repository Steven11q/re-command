import requests
import time
import utils
import asyncio
from tqdm import tqdm
import subprocess
import os
from streamrip.client import DeezerClient
from streamrip.config import Config
from streamrip.media import  PendingSingle
from streamrip.db import Dummy, Database

#from streamrip.rip import Rip

#config = Config.defaults()
#config.session.qobuz.email_or_userid = "YOUR_EMAIL"
#config.session.qobuz.password_or_token = "YOUR_PASSWORD"
#c = QobuzClient(config)
#my_deezer_client = streamrip.clients.DeezerClient()

global c
global config2







def has_playlist_changed():
    """Checks if the playlist has changed since the last run."""
    import config # Import config here
    current_playlist_name = get_latest_playlist_name()
    last_playlist_name = utils.get_last_playlist_name()

    if current_playlist_name == last_playlist_name:
        return False

    utils.save_playlist_name(current_playlist_name)
    return True

def get_latest_playlist_name():
    """Retrieves the name of the latest *recommendation* playlist from ListenBrainz."""
    import config # Import config here
    playlist_json = get_recommendation_playlist(config.USER_LB)

    # Find the "Weekly Exploration" playlist specifically
    for playlist in playlist_json["playlists"]:
        # Check if the title starts with "Weekly Exploration for" followed by your username
        if playlist["playlist"]["title"].startswith(f"Weekly Exploration for {config.USER_LB}"):
            latest_playlist_mbid = playlist["playlist"]["identifier"].split("/")[-1]
            latest_playlist = get_playlist_by_mbid(latest_playlist_mbid)
            return latest_playlist['playlist']['title']

    # If "Weekly Exploration" is not found, raise an error or return a default value
    print("Error: 'Weekly Exploration' playlist not found.")
    return None  # Or return a default playlist name

    # If "Weekly Exploration" is not found, raise an error or return a default value
    print("Error: 'Weekly Exploration' playlist not found.")
    return None



#PITA two
async def meow(query: str,song_info ):
    config2 = Config.defaults()
    import config # Import config here
    config2.session.deezer.arl = config.DEEZER_ARL
    config2.session.downloads.folder = config.MUSIC_LIBRARY_PATH
    config2.session.deezer.quality = 0
    c = DeezerClient(config2)
    await c.login()
    try:
        
        c_track = await c.search("track", query)
        a_id = c_track[0].get('data')[0].get('id')
        db = Database(downloads=Dummy(), failed=Dummy())
        a = PendingSingle(id = a_id,  client = c, config = config2,  db = db)
        resolved_album = await a.resolve()
        await resolved_album.rip()      
    except:
        print(f"Error downloading {song_info['artist']} - {song_info['title']}")
        #time.sleep(1)

    await c.session.close()
        


    #await c.close()
    #idk why it wont let me close the session?
    #if someone figures this out plz fix it :3

def get_recommendation_playlist(username, **params):
    """Fetches the recommendation playlist from ListenBrainz."""
    import config # Import config here
    AUTH_HEADER_LB = {
        "Authorization": f"Token {config.TOKEN_LB}"
    }
    response = requests.get(
        url=f"{config.ROOT_LB}/1/user/{username}/playlists/recommendations",
        params=params,
        headers=AUTH_HEADER_LB,
    )
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()

def get_playlist_by_mbid(playlist_mbid, **params):
    """Fetches a playlist by its MBID from ListenBrainz."""
    import config # Import config here
    AUTH_HEADER_LB = {
        "Authorization": f"Token {config.TOKEN_LB}"
    }
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

def download_track_deemix(deezer_link, artist, title, album, release_date, recording_mbid, release_mbid, music_library_path):
    """Downloads a track using deemix, tags it, and organizes it into Artist/Album folders."""
    import config # Import config here
    try:
        artist = utils.sanitize_filename(artist)
        album = utils.sanitize_filename(album)
        title = utils.sanitize_filename(title)

        # Create the Artist/Album directory structure
        output_dir = os.path.join(music_library_path, artist, album)
        os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

        # Construct the deemix command
        deemix_command = [
            "deemix",
            "-p", output_dir,  # Use the Artist/Album path
            deezer_link
        ]

        # Execute the deemix command and capture output
        result = subprocess.run(deemix_command, capture_output=True, text=True)

        # Save the output to a file (for debugging)
        with open("deemix_output.txt", "w") as outfile:
            outfile.write(f"STDOUT:\n{result.stdout}\n")
            outfile.write(f"STDERR:\n{result.stderr}\n")
            outfile.write(f"Return Code: {result.returncode}\n")

        print(f"deemix return code: {result.returncode}")
        print(f"deemix stdout: {result.stdout}")
        print(f"deemix stderr: {result.stderr}")

        # Find the downloaded file
        downloaded_file = None
        for filename in os.listdir(output_dir):
            if filename.endswith(".mp3") or filename.endswith(".flac"):  # Or other formats
                downloaded_file = os.path.join(output_dir, filename)
                break

        if downloaded_file:
            # Tag the track
            utils.tag_track(downloaded_file, artist, title, album, release_date, recording_mbid)
        else:
            print(f"No matching file found after download for {artist} - {title} from {deezer_link}")

    except Exception as e:
        print(f"Error downloading or tagging track {artist} - {title} ({deezer_link}): {e}")

    """Downloads a track using deemix and tags it."""
    try:
        artist = utils.sanitize_filename(artist)
        album = utils.sanitize_filename(album)
        title = utils.sanitize_filename(title)

        output_dir = os.path.join(music_library_path, artist, album)
        os.makedirs(output_dir, exist_ok=True)

        # Construct the deemix command
        deemix_command = [
            "deemix",
            "-p", output_dir,
            deezer_link
        ]

        # Execute the deemix command
        result = subprocess.run(deemix_command, capture_output=True, text=True)


        if result.returncode != 0:
            print(f"Error downloading {deezer_link} with deemix.")
            print(f"deemix stdout: {result.stdout}")
            print(f"deemix stderr: {result.stderr}")
            return

        # Find the downloaded file (assuming .mp3, but deemix might download other formats)
        downloaded_file = None
        for filename in os.listdir(output_dir):
            if filename.endswith(".mp3") or filename.endswith(".flac"):  # Add other possible extensions
                downloaded_file = os.path.join(output_dir, filename)
                break

        if downloaded_file:
            # Tag the track
            utils.tag_track(downloaded_file, artist, title, album, release_date, recording_mbid)
        else:
            print(f"No matching file found after download for {artist} - {title} from {deezer_link}")

    except Exception as e:
        print(f"Error downloading or tagging track {artist} - {title} ({deezer_link}): {e}")

def download_new_playlist_songs_deemix():
    """Downloads and tags songs from the new playlist using deemix."""
    # Get the latest playlist name (and ensure it's the correct one)
    import config # Import config here
    latest_playlist_name = get_latest_playlist_name()

    if latest_playlist_name is None:
        print("Error: Could not retrieve the latest playlist name.")
        return

    # Find the "Weekly Exploration" playlist by its name
    playlist_json = get_recommendation_playlist(config.USER_LB)
    latest_playlist_mbid = None
    for playlist in playlist_json["playlists"]:
        if playlist["playlist"]["title"] == latest_playlist_name:
            latest_playlist_mbid = playlist["playlist"]["identifier"].split("/")[-1]
            break

    if latest_playlist_mbid is None:
        print(f"Error: Could not find playlist with name '{latest_playlist_name}'.")
        return

    latest_playlist = get_playlist_by_mbid(latest_playlist_mbid)
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
        #asyncio.run(woof())
        for song_info in tqdm(songs_to_download, desc="Downloading Songs", unit="song"):
            #try:
                
                # Get Deezer track link using the new function
                query = "{} {}".format(song_info['artist'],song_info['title'])
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                asyncio.run(meow(query, song_info))
                #downloaded_songs.append(f"{song_info['artist']} - {song_info['title']}")
                
                #deezer_link = deezer_api.get_deezer_track_link(song_info['artist'], song_info['title']
                #this is the part that was being a PITA
                #if deezer_link:
                #    download_track_deemix(deezer_link, song_info['artist'], song_info['title'], song_info['album'], song_info['release_date'], song_info['recording_mbid'], song_info['release_mbid'], config.MUSIC_LIBRARY_PATH)
                #    time.sleep(1)  # Consider removing or adjusting the sleep
                #else:
                #    print(f"Skipping download for {song_info['artist']} - {song_info['title']} (no Deezer link found).")
            #except Exception as e:
                #print(f"Error downloading {song_info['artist']} - {song_info['title']}: {e}")

        print("\nDownloaded the following songs:")
        for song in downloaded_songs:
            print(f"- {song}")
        #downloaded_songs.append(f"{song_info['artist']} - {song_info['title']}")

    else:
        print("\nNo songs were downloaded from the playlist.")

def submit_feedback(recording_mbid, score):
    """Submits feedback for a recording to ListenBrainz."""
    import config # Import config here
    AUTH_HEADER_LB = {
        "Authorization": f"Token {config.TOKEN_LB}"
    }
    payload = {"recording_mbid": recording_mbid, "score": score}

    response = requests.post(
        url=f"{config.ROOT_LB}/1/feedback/recording-feedback",
        json=payload,
        headers=AUTH_HEADER_LB
    )
    response.raise_for_status()
    print(f"Feedback submitted for {recording_mbid}: {score}")
