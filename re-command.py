#!/usr/bin/env python3

import os
import navidrome_api
import importlib

def main():
    """Main function to run the Navidrome recommendation script."""

    print("Starting weekly re-command script...")

    # Ensure config exists, run setup if not
    if not os.path.exists("config.py"):
        navidrome_api.first_time_setup()

    # Import config *after* the setup
    import config
    import listenbrainz_api
    import lastfm_api

    # Reload the config module
    importlib.reload(config)

    # Check if the ListenBrainz playlist has changed
    if listenbrainz_api.has_playlist_changed():
        # Download and tag new songs from ListenBrainz using deemix
        listenbrainz_api.download_new_playlist_songs_deemix()
    else:
        print("ListenBrainz playlist has not changed. Skipping download.")


    # Parse Navidrome library and provide feedback to ListenBrainz
    salt, token = navidrome_api.get_navidrome_auth_params()
    navidrome_api.process_navidrome_library(salt, token)

    print("Script finished.")

if __name__ == "__main__":
    main()
