# re-command: Unleash Your Inner Music Maestro (with a Little Help from ListenBrainz)

🎶 Ready to ditch your friends recommendations and let the algorithms curate your next sonic adventure?  re-command is your personal musical sherpa, guiding you through the treacherous terrain of ListenBrainz recommendations and seamlessly integrating them into your Navidrome music kingdom.  Think of it as a weekly musical surprise party, delivered right to your hard drive.

## Features: Because Your Ears Deserves the Best

* **Automated Downloads:**  Like a musical ninja, re-command stealthily downloads recommended tracks from ListenBrainz, depositing them directly into your Navidrome library. No clicking, no fuss, just pure musical magic.
* **Smart Tagging:**  Forget manual tagging! re-command is a metadata wizard, automatically tagging your new tunes with all the essential info: artist, title, album, release date, and even the mystical MusicBrainz ID.
* **Smart Playlist Harmony:**  Each downloaded track gets a special "recommendation" tag, making it easy to create dynamic weekly playlists in Navidrome or your favorite player.  It's like having a personal mixtape delivered fresh every week.
* **Album Art Glam:**  Because music isn't just about sound, re-command fetches and embeds album art, giving your library the visual flair it deserves. (Album art not guaranteed, but we'll try our best!)
* **Library Cleanup Crew:**  Got some musical regrets?  re-command acts as your personal music librarian, discreetly removing disliked or unrated tracks from previous recommendations.  Only the 4-5 star gems remain, ensuring your library is a sanctuary of sonic bliss.
* **ListenBrainz Whisperer:**  re-command provides feedback to ListenBrainz for disliked tracks, helping the algorithms learn your taste and refine future recommendations. You are done listening that terrible track again and again.
* **Progress Tracking:**  No more guessing games!  A snazzy progress bar keeps you updated on downloads and library processing.  You'll know exactly when your next musical feast is ready.
* **Folder Organization Guru:**  re-command tidies up empty folders in your music library, keeping things neat and organized.  It follows the old classic artist/albums/tracks directory structure.
* **First-Time Setup Fairy:**  Setting up re-command is a breeze, thanks to a friendly guide that walks you through the process.

## Prerequisites: Gather Your Musical Arsenal

* **Python 3:** The lifeblood of the operation.
* **Required Libraries:** `pip install requests tqdm`
* **External Tools:** `yt-dlp` (the download master) and `kid3-cli` (the tagging titan). Installation instructions below!
* **Navidrome Server:** Your musical kingdom.
* **ListenBrainz Account:** Your source of musical wisdom.
* **Cookies.txt:** A secret file containing your YouTube Music cookies.  (Don't worry, we won't tell anyone.)  This helps yt-dlp bypass download restrictions. Browser extensions like "Get cookies.txt" can help you obtain this precious artifact.  (OAuth is not supported anymore by yt-dlp, sorry!)

## Setup: Building Your Musical Empire

1. **Clone the Repository:** Bring the code to your server.  (Ideally in the same place as your music.)
2. **Configuration:** Run the script once, and it'll guide you through the setup, creating a `config.py` file. Or, if you're feeling adventurous, create `config.py` yourself and fill in the details :
     ```python
    ROOT_ND = "http://your-navidrome-server:4533" # Your Navidrome URL
    USER_ND = "your_navidrome_username"
    PASSWORD_ND = "your_navidrome_password"
    MUSIC_LIBRARY_PATH = "/path/to/your/music/library"

    ROOT_LB = "https://api.listenbrainz.org" # ListenBrainz API root URL (constant)
    TOKEN_LB = "your_listenbrainz_token"
    USER_LB = "your_listenbrainz_username"

    TARGET_COMMENT = "recommendation" # Comment used to mark recommended songs
    PLAYLIST_HISTORY_FILE = "playlist_history.txt" # File to store playlist history
    ```

## Usage: Conducting Your Musical Orchestra

Just run `python3 re-command.py`.  The script will work its magic, checking for new recommendations, cleaning up your library from old songs and folders, downloading fresh tunes, and tagging everything beautifully.

**Pro Tip:** Set up a cron job to run this weekly (like a musical alarm clock).

```bash
chmod +X re-command.py
crontab -e
```
And then add this line at the bottom of the file :
```
0 23 * * 1 /usr/bin/python3 /home/your/script/location/re-command.py >> home/your/script/location/re-command.log 2>&1
```

**Bonus Tip:** Create a dynamic playlist in your player with a "tag = recommendation" filter. Instant access to your weekly dose of musical goodness!

## Contributing: Join the Musical Revolution

Got ideas?  Found a bug?  Contributions are always welcome!

## Future Developments: The Musical Journey Continues

* **Last.fm Integration:**  Because two sources of musical wisdom are better than one.
* **Liked Songs Feedback:**  Spread the love to ListenBrainz for your favorite tracks.
* **More Testing:**  Because we want everything to be pitch-perfect.
