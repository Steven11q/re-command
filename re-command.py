#!/usr/bin/env python3

import os
import navidrome_api
import importlib
import subprocess
from mutagen.id3 import ID3, COMM




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

    

    # Check if the ListenBrainz playlist has changed
    #listenbrainz_api.has_playlist_changed()
    if listenbrainz_api.has_playlist_changed():
        # Download and tag new songs from ListenBrainz using deemix
        listenbrainz_api.download_new_playlist_songs_deemix()
    else:
        print("ListenBrainz playlist has not changed. Skipping download.")

    #parse new entries and add comment
    for entry in os.scandir(folder):  
        if entry.is_file():  # check if it's a file
            mp3_file = entry.path
            if mp3_file.endswith(".mp3"):
                
                try:
                    id3v2_3 = ID3(mp3_file, translate=False, load_v1=False)
                except:
                    # No ID3 header found; creating a new tag
                    id3v2_3 = ID3()

                comment_field = config.TARGET_COMMENT
                # Empty 'desc' is important to display in players
                id3v2_3.add(COMM(encoding=3, lang='eng', desc='', text=comment_field))
                id3v2_3.save(mp3_file, v2_version=3, v1=2)

    # Last.fm authentication and download

    # Parse Navidrome library and provide feedback to ListenBrainz
    salt, token = navidrome_api.get_navidrome_auth_params()
    navidrome_api.process_navidrome_library(salt, token)

    #import files into Navidrome library
    #this is a bad way to do this but im too tired to do this the proper way by importing beet
    # if you want, you can fix it
    
    subprocess.run(["powershell", "beet import -qgW {}".format(folder)])
    #subprocess.run(["powershell", "beet modify path:{} comments={}".format(folder, config.TARGET_COMMENT)])
    print("Script finished.")

if __name__ == "__main__":
    main()
