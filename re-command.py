#!/usr/bin/env python3

import config  # Import configuration from config.py
import navidrome_api  # Import Navidrome API module
import listenbrainz_api  # Import ListenBrainz API module
import utils  # Import utility functions

def main():
    """Main function to run the Navidrome recommendation script."""

    print("Starting weekly re-command script...")

    # Check if the playlist has changed
    if not listenbrainz_api.has_playlist_changed():
        print(f"Playlist has not changed since last run. Skipping download.")
        return

    # Parse Navidrome library and provide feedback to ListenBrainz
    salt, token = navidrome_api.get_navidrome_auth_params()
    navidrome_api.process_navidrome_library(salt, token)

    # Download and tag new songs
    listenbrainz_api.download_new_playlist_songs(salt, token)

    print("Script finished.")

if __name__ == "__main__":
    main()
