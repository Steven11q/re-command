import os
import subprocess
import re
import config
import requests

def get_last_playlist_name():
    """Retrieves the last playlist name from the history file."""
    try:
        with open(config.PLAYLIST_HISTORY_FILE, "r") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return None

def save_playlist_name(playlist_name):
    """Saves the playlist name to the history file."""
    try:
        with open(config.PLAYLIST_HISTORY_FILE, "w") as f:
            f.write(playlist_name)
    except OSError as e:  # Handle potential errors during file writing
        print(f"Error saving playlist name to file: {e}")

def sanitize_filename(filename):
    """Replaces problematic characters in filenames with underscores."""
    return re.sub(r'[\\/:*?"<>|]', '_', filename)


def download_track_yt_dlp(artist, title, album, release_date, recording_mbid, release_mbid, salt, token, music_library_path, get_album_art_func):
    """Downloads a track using yt-dlp and tags it."""
    try:
        search_query = f"{artist} - {title}"

        artist = sanitize_filename(artist)
        album = sanitize_filename(album)
        title = sanitize_filename(title)

        output_dir = os.path.join(music_library_path, artist, album)
        os.makedirs(output_dir, exist_ok=True)
        temp_filename = f"{output_dir}/temp_%(title)s.%(ext)s"
        yt_dlp_command = [
            "yt-dlp",
            "--embed-metadata",
            "-x",
            "--audio-format", "aac",  # Or your preferred format
            "--output", temp_filename,
            "--add-metadata",
            "--metadata-from-title", "%(artist)s - %(title)s",
            "--cookies", "cookies.txt", # Make sure you have a cookies.txt file
            f"ytsearch1:{search_query}"
        ]

        subprocess.run(yt_dlp_command, check=True, capture_output=True, text=True) # Capture output for debugging


        downloaded_file = glob.glob(f"{output_dir}/temp_*")[0]
        final_file_path = os.path.join(output_dir, f"{title}.m4a") # Or your preferred extension
        os.rename(downloaded_file, final_file_path)

        # Embed album art
        if release_mbid:
            album_art = get_album_art_func(release_mbid, salt, token)
            if album_art:
                with open(f"{final_file_path}.jpg", "wb") as f:
                    f.write(album_art)
                try:
                    subprocess.run(["kid3-cli", "-c", f"set picture \"{final_file_path}.jpg\"", final_file_path], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error setting album art: {e}")
                finally: # Ensure temp image file is deleted
                    os.remove(f"{final_file_path}.jpg")


        tag_track(final_file_path, artist, title, album, release_date, recording_mbid)

    except subprocess.CalledProcessError as e:
        print(f"Error downloading or tagging track {artist} - {title}: {e}")
        print(f"yt-dlp output: {e.stdout}") # Print yt-dlp output for debugging
        print(f"yt-dlp error: {e.stderr}") # Print yt-dlp error output
    except (IndexError, FileNotFoundError): # Handle cases where no file was downloaded
        print(f"No matching file found after download for {artist} - {title}")


def tag_track(file_path, artist, title, album, release_date, recording_mbid):
    """Tags a track with metadata using kid3-cli."""
    try:
        subprocess.run(["kid3-cli",
                        "-c", f"set artist \"{artist}\"",
                        "-c", f"set title \"{title}\"",
                        "-c", f"set album \"{album}\"",
                        "-c", f"set date \"{release_date}\"",
                        "-c", f"set musicBrainzId  \"{recording_mbid}\"",
                        "-c", f"set comment \"{config.TARGET_COMMENT}\"",  # Use config variable
                        file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error tagging {file_path}: {e}")
    except FileNotFoundError:
        print(f"kid3-cli not found.  Is it installed and in your PATH?")

def remove_empty_folders(path):
    """Removes empty folders from a given path."""
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            full_path = os.path.join(root, dir)
            if not os.listdir(full_path):
                try:
                    os.rmdir(full_path)
                except OSError as e:
                    print(f"Error removing folder: {full_path}. Error: {e}")

def get_album_art(album_id, salt, token):
    """Fetches album art from Navidrome."""
    url = f"{config.ROOT_ND}/rest/getCoverArt.view"
    params = {
        'u': config.USER_ND,
        't': token,
        's': salt,
        'v': '1.16.1',
        'c': 'python-script',
        'id': album_id,
        'size': 1200  # Get the largest available size
    }
    try:
        response = requests.get(url, params=params, stream=True)  # Use stream for large images
        response.raise_for_status()
        return response.content  # Return the raw image data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching album art: {e}")
        return None

import glob
