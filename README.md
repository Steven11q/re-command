
# re-command: Automated Music Recommendation System for Navidrome

This has been modified to reflect the changes I made to get it to run properly on my machine.

`re-command` is a Python-based tool designed to enhance your Navidrome music experience by automatically downloading music recommendations with [Deemix](https://deemix.org/) from [ListenBrainz](https://github.com/metabrainz/listenbrainz-server) and [Last.fm](https://www.last.fm/music/+recommended/). It acts as your behind-the-scenes music curator, downloading, tagging, and organizing recommended tracks, while also cleaning up your library based on your ratings.

## Key Features

*   **Automated Track Downloads:** `re-command` automatically downloads via Deemix recommended tracks playlists, fetched on ListenBrainz and Last.fm, directly into your Navidrome library.
*   **Intelligent Metadata Tagging:**  New tracks are automatically tagged with essential information, including artist, title, album, release date, album art and MusicBrainz ID (when available).
*   **Dynamic Playlist Support:** Downloaded tracks are tagged with a special "recommendation" comment (configurable), enabling you to create dynamic playlists in Navidrome or other compatible music players. This allows you to easily listen to a weekly mix of fresh recommendations.
*   **Automated Library Maintenance:** `re-command` removes tracks from previous recommendations based on your Navidrome ratings, keeping your library filled with music you enjoy. Specifically, tracks rated 3 stars or lower (including unrated tracks) are automatically deleted.
*   **ListenBrainz Feedback Integration:**  The script automatically submits feedback to ListenBrainz for disliked tracks (1-star ratings), helping improve future recommendations.
*   **Progress Visualization:**  A progress bar provides real-time feedback on library processing and track downloads.
*   **Directory Cleanup:**  `re-command` automatically removes empty folders within your music library, maintaining a tidy and organized structure.
*   **Simplified Initial Setup:** An interactive setup process guides you through the configuration of the script.

## Prerequisites

*   **Python 3.x**
*   **Required Python Libraries:**
    ```bash
    pip install requests tqdm pylast deemix
    ```
    or simply :
    ```bash
    pip install -r requirements.txt
    ```
*   **External Tools:**
    *   `kid3-cli` (for audio file tagging)

    Installation examples (may vary depending on your OS):
    ```bash
    # Debian/Ubuntu
    sudo apt install kid3-cli

    # Arch Linux
    yay -S kid3-common
    ```
*   **Navidrome Server:** A running Navidrome instance.
*   **ListenBrainz Account  (Optional):**  A ListenBrainz user account.
*   **Last.fm Account (Optional):** A Last.fm user account, for enhanced music discovery.
*   **Deezer Account (Free or Premium) & ARL Token:** Your Deezer ARL token for deemix to function. You can typically find it in your browser dev tools in the "Applications" tab under "Cookies". Free account means only 128 kbps MP3 tracks.

## Setup

1. **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Install requirements:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configuration:**

    *   **First-time setup:** Run the script once (`python3 re-command.py`). It will detect that `config.py` is missing and guide you through an interactive setup process to create it.

    *   **Manual Configuration (Optional):** If you prefer, you can create `config.py` manually. Use the following template:

        ```python
        # Navidrome API Configuration
        ROOT_ND = 'http://your-navidrome-server:4533' # Replace with your Navidrome URL
        USER_ND = 'your_navidrome_username'          # Your Navidrome username
        PASSWORD_ND = 'your_navidrome_password'        # Your Navidrome password
        TARGET_COMMENT = "recommendation"             # Comment tag to identify recommended tracks
        MUSIC_LIBRARY_PATH = "/path/to/your/music/library" # Full path to your music library

        # ListenBrainz API Configuration
        ROOT_LB = 'https://api.listenbrainz.org'       # ListenBrainz API base URL (leave as is)
        TOKEN_LB = 'your_listenbrainz_token'            # Your ListenBrainz API token
        USER_LB = "your_listenbrainz_username"         # Your ListenBrainz username

        # Deezer Configuration
        DEEZER_ARL = "your_deezer_arl_token"           # Your Deezer ARL token. Please also write it down in ~/.config/deemix/.arl or run deemix once to set it up.

        # Playlist History File
        PLAYLIST_HISTORY_FILE = "playlist_history.txt" # File to store the last processed playlist name

        # Last.fm API Configuration (optional, for Last.fm integration)
        LASTFM_API_KEY = "your_lastfm_api_key"         # Your Last.fm API key
        LASTFM_API_SECRET = "your_lastfm_api_secret"   # Your Last.fm API secret
        LASTFM_USERNAME = "your_lastfm_username"       # Your Last.fm username
        LASTFM_PASSWORD_HASH = ""                     # Optional: Your Last.fm password hash (less secure)
        LASTFM_SESSION_KEY = "your_lastfm_session_key" # Your Last.fm session key (more secure)
        LASTFM_TARGET_COMMENT = "lastfm_recommendation" # Comment tag for Last.fm recommended tracks
        ```

## Usage

1. Make the script executable:
    ```bash
    chmod +x re-command.py
    ```

2. Run the script:
    ```bash
    python3 re-command.py
    ```

    The script will perform the following actions:
    *   Check for new recommendations from ListenBrainz and/or Last.fm.
    *   Download new tracks via `deemix`.
    *   Tag downloaded tracks with appropriate metadata.
    *   Parse your Navidrome library, removing previously recommended tracks that you've rated 3 stars or below (or have not rated).
    *   Submit negative feedback to ListenBrainz for tracks you've rated 1 star.
    *   Clean up any empty directories in your music library.

**Automation with `cron` (Recommended):**

To run `re-command` automatically on a weekly schedule (e.g., every Monday at 11 PM), you can add a cron job:

1. Edit your crontab:
    ```bash
    crontab -e
    ```

2. Add the following line (adjust the path and time as needed):
    ```
    0 23 * * 1 /usr/bin/python3 /path/to/re-command.py >> /path/to/re-command.log 2>&1
    ```

**Dynamic Playlist Tip:**

In your music player, create a dynamic playlist that filters for tracks with the comment tag you set in `config.py` (e.g., "lb-recommendation" or "lastfm_recommendation"). This playlist will automatically update with your latest recommendations.

## Known Issues
* Positive feedback to ListenBrainz is not working at all times yet (still in debugging)
* Due to Last.fm API playlist support drop, album folders for Last.fm downloads are "UNKNOWN ALBUM" and the downloads are not exactly the same as the ones on your recommendations/tracks page (but really close).

## Contributing

Contributions to `re-command` are welcome! If you have ideas for improvements, bug fixes, or new features, please feel free to submit issues or pull requests on the project's repository.

## Future Development

*   **More Feedbacks:** Implement submission of positive feedback to ListenBrainz and Last.fm for highly-rated tracks, as well as Last.fm disliked tracks.
