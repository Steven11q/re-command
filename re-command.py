#!/usr/bin/env python3

import os
import navidrome_api
import importlib
import subprocess





def main():
    """Main function to run the Navidrome recommendation script."""

    print("Starting weekly re-command script...")

    # Ensure config exists, run setup if not
    if not os.path.exists("config.py"):
        navidrome_api.first_time_setup()

    # Import config *after* the setup
    import config
    import listenbrainz_api
    #import lastfm_api

    # Reload the config module
    importlib.reload(config)

    folder = config.MUSIC_LIBRARY_PATH

    #this is a bad way to do this but im too tired to do this the proper way by importing beet
    # if you want, you can fix it
    subprocess.run(["powershell", "beet import {}".format(folder)])

    # Check if the ListenBrainz playlist has changed
    #listenbrainz_api.has_playlist_changed()
    if True:
        # Download and tag new songs from ListenBrainz using deemix
        listenbrainz_api.download_new_playlist_songs_deemix()
    else:
        print("ListenBrainz playlist has not changed. Skipping download.")

    # Last.fm authentication and download

    # Parse Navidrome library and provide feedback to ListenBrainz
    salt, token = navidrome_api.get_navidrome_auth_params()
    navidrome_api.process_navidrome_library(salt, token)

    print("Script finished.")

if __name__ == "__main__":
    main()
