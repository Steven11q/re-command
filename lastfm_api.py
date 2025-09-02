import pylast
import config
import time
import os
import utils
from tqdm import tqdm
import deemix as deezer_api
import subprocess
import requests

def authenticate_lastfm():
    """Authenticates with Last.fm using pylast."""
    if config.LASTFM_PASSWORD_HASH:
        # Using password hash (less secure)
        network = pylast.LastFMNetwork(
            api_key=config.LASTFM_API_KEY,
            api_secret=config.LASTFM_API_SECRET,
            username=config.LASTFM_USERNAME,
            password_hash=config.LASTFM_PASSWORD_HASH
        )
    elif config.LASTFM_SESSION_KEY:
        # Using session key (more secure)
        network = pylast.LastFMNetwork(
            api_key=config.LASTFM_API_KEY,
            api_secret=config.LASTFM_API_SECRET,
            session_key=config.LASTFM_SESSION_KEY
        )
    else:
        # Get session key if not configured
        network = pylast.LastFMNetwork(api_key=config.LASTFM_API_KEY, api_secret=config.LASTFM_API_SECRET)
        skg = pylast.SessionKeyGenerator(network)
        url = skg.get_web_auth_url()

        print(f"Please authorize this script to access your account: {url}\n")
        import webbrowser
        webbrowser.open(url)

        # Wait for a few seconds before prompting the user
        time.sleep(5)  # Wait for 5 seconds

        while True:
            input("Press Enter after you have authorized the application...")
            try:
                session_key = skg.get_web_auth_session_key(url)
                config.LASTFM_SESSION_KEY = session_key
                # Update config.py with the new session key
                with open("config.py", "r") as f:
                    lines = f.readlines()
                with open("config.py", "w") as f:
                    for line in lines:
                        if line.startswith("LASTFM_SESSION_KEY"):
                            f.write(f"LASTFM_SESSION_KEY = \"{session_key}\"\n")
                        else:
                            f.write(line)
                network.session_key = session_key
                break
            except pylast.WSError as e:
                if e.details == "The token supplied to this request is invalid. It has either expired or not yet been authorised.":
                    print("Token still invalid or not authorized yet. Please ensure you've authorized and try again.")
                else:
                    print(f"Error during authentication: {e.details}")
                    return None
    return network

def get_recommended_tracks(network, limit=100):
    """
    Fetches recommended tracks from Last.fm using the undocumented /recommended endpoint.
    """
    user = network.get_user(config.LASTFM_USERNAME)
    recommendations = []

    url = f"https://www.last.fm/player/station/user/{config.LASTFM_USERNAME}/recommended"
    headers = {
        'Referer': 'https://www.last.fm/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for bad status codes

    data = response.json()

    for track_data in data["playlist"]:
        artist = track_data["artists"][0]["name"]
        title = track_data["name"]
        recommendations.append({
            "artist": artist,
            "title": title,
            "album": "Unknown Album",  # Album not available in this data
            "release_date": None
        })

        if len(recommendations) >= limit:
            break

    return recommendations

def download_track_deemix_lastfm(deezer_link, artist, title, album, release_date, music_library_path):
    """Downloads a track using deemix, tags it, and organizes it into Artist/Album folders."""
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
            utils.tag_track_lastfm(downloaded_file, artist, title, album, release_date)
        else:
            print(f"No matching file found after download for {artist} - {title} from {deezer_link}")

    except Exception as e:
        print(f"Error downloading or tagging track {artist} - {title} ({deezer_link}): {e}")

def download_new_playlist_songs_deemix_lastfm(network):
    """Downloads and tags songs from the new playlist using deemix."""
    recommended_tracks = get_recommended_tracks(network)

    if not recommended_tracks:
        print("No recommendations found from Last.fm.")
        return

    songs_to_download = []
    for track in recommended_tracks:
        songs_to_download.append({
            "artist": track["artist"],
            "title": track["title"],
            "album": track["album"],
            "release_date": track["release_date"]
        })

    if songs_to_download:
        print("\nThe following songs will be downloaded from Last.fm recommendations:")
        for song in songs_to_download:
            print(f"- {song['artist']} - {song['title']} from album {song['album']}")

        downloaded_songs = []
        for song_info in tqdm(songs_to_download, desc="Downloading Songs from Last.fm", unit="song"):
            try:
                deezer_link = deezer_api.get_deezer_track_link(song_info['artist'], song_info['title'])
                if deezer_link:
                    download_track_deemix_lastfm(deezer_link, song_info['artist'], song_info['title'], song_info['album'], song_info['release_date'], config.MUSIC_LIBRARY_PATH)
                    downloaded_songs.append(f"{song_info['artist']} - {song_info['title']}")
                    time.sleep(1)  # Consider removing or adjusting
                else:
                    print(f"Skipping download for {song_info['artist']} - {song_info['title']} (no Deezer link found).")
            except Exception as e:
                print(f"Error downloading {song_info['artist']} - {song_info['title']}: {e}")

        print("\nDownloaded the following songs from Last.fm:")
        for song in downloaded_songs:
            print(f"- {song}")
    else:
        print("\nNo songs were downloaded from the Last.fm playlist.")
