import requests
import hashlib
import os
import subprocess
import config
import utils
from tqdm import tqdm
import sys
import listenbrainz_api
import pylast


def get_navidrome_auth_params():
    """Generates authentication parameters for Navidrome."""
    salt = os.urandom(6).hex()
    token = hashlib.md5((config.PASSWORD_ND + salt).encode('utf-8')).hexdigest()
    return salt, token


def get_all_songs(salt, token):
    """Fetches all songs from Navidrome."""
    url = f"{config.ROOT_ND}/rest/search3.view"
    params = {
        'u': config.USER_ND,
        't': token,
        's': salt,
        'v': '1.16.1',  # Keep the API version updated if Navidrome updates
        'c': 'python-script',
        'f': 'json',
        'query': '',
        'songCount': 10000  # Adjust if your library is larger
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if data['subsonic-response']['status'] == 'ok' and 'searchResult3' in data['subsonic-response']:
        return data['subsonic-response']['searchResult3']['song']
    else:
        print(f"Error fetching songs from Navidrome: {data['subsonic-response']['status']}")
        return []  # Return an empty list on error


def get_song_details(song_id, salt, token):
    """Fetches details of a specific song from Navidrome."""
    url = f"{config.ROOT_ND}/rest/getSong.view"
    params = {
        'u': config.USER_ND,
        't': token,
        's': salt,
        'v': '1.16.1',
        'c': 'python-script',
        'f': 'json',
        'id': song_id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if data['subsonic-response']['status'] == 'ok' and 'song' in data['subsonic-response']:
        return data['subsonic-response']['song']
    else:
        print(f"Error fetching song details from Navidrome: {data.get('subsonic-response', {}).get('status', 'Unknown')}")  # Improved error handling
        return None


def update_song_comment(file_path, new_comment):
    """Updates the comment of a song using kid3-cli."""
    try:
        subprocess.run(["kid3-cli", "-c", f"set comment \"{new_comment}\"", file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error updating comment for {file_path}: {e}")
    except FileNotFoundError:
        print(f"kid3-cli not found.  Is it installed and in your PATH?")


def delete_song(song_path):
    """Deletes a song file."""
    if os.path.exists(song_path):
        try:
            os.remove(song_path)
        except OSError as e:
            print(f"Error deleting song: {song_path}. Error: {e}")


def process_navidrome_library(salt, token):
    """Processes the Navidrome library with a progress bar."""
    import config  # Import config here
    all_songs = get_all_songs(salt, token)
    print(f"Parsing {len(all_songs)} songs from Navidrome to cleanup badly rated songs.")

    deleted_songs = []

    # Add progress bar using tqdm
    for song in tqdm(all_songs, desc="Processing Navidrome Library", unit="song", file=sys.stdout):
        song_details = get_song_details(song['id'], salt, token)
        if song_details and 'comment' in song_details:
            song_path = os.path.join(config.MUSIC_LIBRARY_PATH, song_details['path'])
            user_rating = song_details.get('userRating', 0)

            if song_details['comment'] == config.TARGET_COMMENT:  # Listenbrainz
                if user_rating >= 4:  # Loved
                    update_song_comment(song_path, "")

                elif user_rating <= 3:  # Disliked or no rating
                    delete_song(song_path)
                    deleted_songs.append(f"{song_details['artist']} - {song_details['title']}")
                    if 'musicBrainzId' in song_details and song_details['musicBrainzId'] and user_rating == 1:
                        listenbrainz_api.submit_feedback(song_details['musicBrainzId'], 1)  # Submit negative feedback if rating is 1

    if deleted_songs:
        print("Deleting the following songs from last week recommendation playlist:")
        for song in deleted_songs:
            print(f"- {song}")
    else:
        print("No songs with recommendation comment were found.")

    utils.remove_empty_folders(config.MUSIC_LIBRARY_PATH)


def first_time_setup():
    """Guides the user through the initial configuration."""
    config_data = {}

    print("\nWelcome to the Navidrome Recommendation Script! Let's set things up.\n")

    # --- Navidrome Configuration ---
    config_data["ROOT_ND"] = input("Enter your Navidrome root URL (e.g., http://your-navidrome-server:4533): ")
    config_data["USER_ND"] = input("Enter your Navidrome username: ")
    config_data["PASSWORD_ND"] = input("Enter your Navidrome password: ")
    config_data["MUSIC_LIBRARY_PATH"] = input("Enter the full path to your music library directory: ")

    # --- ListenBrainz Configuration ---
    use_listenbrainz = input("Do you want to use ListenBrainz? (yes/no): ").lower()
    config_data["LISTENBRAINZ_ENABLED"] = use_listenbrainz == "yes"

    if config_data["LISTENBRAINZ_ENABLED"]:
        config_data["ROOT_LB"] = "https://api.listenbrainz.org"  # This is constant
        print("\nTo get your ListenBrainz token:")
        print("1. Go to https://listenbrainz.org/profile/")
        print("2. Click on 'Edit Profile'.")
        print("3. Scroll down to 'API Keys'.")
        print("4. Generate a new token or copy an existing one.\n")
        config_data["TOKEN_LB"] = input("Enter your ListenBrainz token: ")
        config_data["USER_LB"] = input("Enter your ListenBrainz username: ")
    else:
        config_data["ROOT_LB"] = ""
        config_data["TOKEN_LB"] = ""
        config_data["USER_LB"] = ""

    # --- Last.fm Configuration ---
    use_lastfm = input("Do you want to use Last.fm? (yes/no): ").lower()
    config_data["LASTFM_ENABLED"] = use_lastfm == "yes"

    if config_data["LASTFM_ENABLED"]:
        config_data["LASTFM_USERNAME"] = input("Enter your Last.fm username: ")
        print("\nTo get your Last.fm API key and secret:")
        print("1. Go to https://www.last.fm/api/account/create")
        print("2. Create a new API account (if you don't have one).")
        print("3. Fill in the application details (you can use placeholder values for most fields).")
        print("4. Copy the API key and shared secret.\n")
        config_data["LASTFM_API_KEY"] = input("Enter your Last.fm API key: ")
        config_data["LASTFM_API_SECRET"] = input("Enter your Last.fm API secret: ")
        print("\nTo get your Last.fm token (needed for a session key):")
        print("1. Open a new browser tab and go to:")
        print(f"   http://ws.audioscrobbler.com/2.0/?method=auth.getToken&api_key={config_data['LASTFM_API_KEY']}&format=json")
        print("2. This will return a JSON response with a token. Copy the token value.\n")
        lastfm_token = input("Enter your Last.fm token: ")

        # Generate and save Last.fm session key
        try:
            network = pylast.LastFMNetwork(api_key=config_data["LASTFM_API_KEY"], api_secret=config_data["LASTFM_API_SECRET"])
            session_key_generator = pylast.SessionKeyGenerator(network)
            session_key = session_key_generator.get_web_auth_session_key(f"http://www.last.fm/api/auth/?api_key={config_data['LASTFM_API_KEY']}&token={lastfm_token}")
            config_data["LASTFM_SESSION_KEY"] = session_key
        except Exception as e:
            print(f"Error during Last.fm session key generation: {e}")
            config_data["LASTFM_SESSION_KEY"] = ""  # Set empty string to avoid issues later
    else:
        config_data["LASTFM_USERNAME"] = ""
        config_data["LASTFM_API_KEY"] = ""
        config_data["LASTFM_API_SECRET"] = ""
        config_data["LASTFM_SESSION_KEY"] = ""


    # --- Deemix Configuration ---
    print("\nTo get your Deezer ARL:")
    print("1. Log in to Deezer in your web browser.")
    print("2. Open the Developer Tools (usually by pressing F12).")
    print("3. Go to the 'Application' or 'Storage' tab.")
    print("4. Find the 'Cookies' section and expand it.")
    print("5. Locate the cookie named 'arl'.")
    print("6. Copy the value of the 'arl' cookie.\n")
    arl = input("Enter your Deezer ARL: ")

    # Get the user's home directory
    home_dir = os.path.expanduser("~")

    # Define the path to the .arl file
    deemix_config_dir = os.path.join(home_dir, ".config", "deemix")
    arl_file_path = os.path.join(deemix_config_dir, ".arl")

    # Create the deemix config directory if it doesn't exist
    os.makedirs(deemix_config_dir, exist_ok=True)

    # Write the ARL to the .arl file
    try:
        with open(arl_file_path, "w") as arl_file:
            arl_file.write(arl)
        print(f"Deezer ARL saved to {arl_file_path}")
        config_data["DEEZER_ARL_FILE"] = arl_file_path  # Store the file path
    except OSError as e:
        print(f"Error saving Deezer ARL to file: {e}")
        config_data["DEEZER_ARL_FILE"] = ""  # Set to empty string on error

    config_data["DEEMIX_ENABLED"] = True

    # --- Other Configuration ---
    config_data["LASTFM_PASSWORD_HASH"] = ""
    config_data["TARGET_COMMENT"] = "lb_recommendation"
    config_data["PLAYLIST_HISTORY_FILE"] = "playlist_history.txt"
    config_data["LASTFM_TARGET_COMMENT"] = "lastfm_recommendation"

    # Save configuration to config.py
    try:
        with open("config.py", "w") as f:
            f.write("# Re-command Recommendation Script Configuration\n")
            for key, value in config_data.items():
                if isinstance(value, str):
                    f.write(f"{key} = \"{value}\"\n")
                else:
                    f.write(f"{key} = {value}\n")

        print("\nConfiguration saved to config.py. You can edit this file later if needed.")

    except OSError as e:
        print(f"Error saving configuration file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if config.py exists
    if not os.path.exists("config.py"):
        first_time_setup()
        import config  # Import config after it's created
    else:
        import config
