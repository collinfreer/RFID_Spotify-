# RFID_Spotify
Play a Spotify playlist on a WiiM device when an RFID card is scanned, with album art and playback controls on a touchscreen display.

The script reads a USB RFID reader exposed as a Linux input device, looks up the scanned card ID in a JSON mapping file, then starts the mapped playlist through Spotify Connect on your WiiM. A second script displays the current track, album art, and touch controls on a Waveshare 5\" DSI touchscreen.

## Requirements
- Spotify Premium
- A Spotify app registration with a client ID and client secret
- A WiiM device visible in Spotify Connect
- A USB RFID reader that appears under `/dev/input/...`
- Linux or Raspberry Pi OS with Python installed
- Programmable RFID cards
- A Waveshare 5\" DSI capacitive touchscreen (optional, for display UI)

## Parts List
Here are the exact products I used. You do not need to use the same hardware, but this is a complete shopping list if you are starting from scratch.

Disclosure: The links below are Amazon affiliate links. As an Amazon Associate I earn from qualifying purchases.

- [Element14 Raspberry Pi 3 B+ Motherboard](https://amzn.to/4ecO3TP) (affiliate link)
- [CanaKit 5V 2.5A Raspberry Pi 3 B+ Power Supply/Adapter](https://amzn.to/43Dsc1P) (affiliate link)
- [Beamo Preloaded 64GB Raspberry Pi OS MicroSD Card](https://amzn.to/4x6SDe3) (affiliate link)
- [WiiM Mini AirPlay 2 Wireless Audio Streamer](https://amzn.to/4x09oHE) (affiliate link)
- [13.56Mhz USB RFID Reader](https://amzn.to/3RDH3GY) (affiliate link)
- [100 PCS 125KHz RFID Proximity ID Cards](https://amzn.to/4vhWsLx) (affiliate link)
- Waveshare 5\" DSI LCD Capacitive Touchscreen (optional, for display UI)

## Prerequisites

### Spotify API Credentials

1. Go to [developer.spotify.com](https://developer.spotify.com) and log in with your Spotify account
2. Click **Create App**
3. Give it any name and description
4. Set the Redirect URI to `http://127.0.0.1:8888/callback` — this must match exactly
5. Click **Save**
6. On the app dashboard, click **Settings** to find your **Client ID** and **Client Secret**
7. Copy both into `config.json` under `spotify.client_id` and `spotify.client_secret`

On first run, a browser window will open asking you to log in and approve access. After approving, the token is cached locally and you won't be prompted again.

### Connecting the Touchscreen

Connect your DSI touchscreen to the Raspberry Pi following your display manufacturer's instructions. The DSI port is the narrow ribbon connector on the Pi board labeled **DISPLAY**.

Some models (including the Waveshare 5\" DSI) connect via ribbon cable only with no additional power connection required. Others may require a USB power cable from the Pi to the display for the backlight. Check your manufacturer's documentation to confirm which applies to your model.

**Always power off the Pi before connecting or disconnecting the display.**

To test that the display is working, power on the Pi with the screen connected. You should see the desktop appear on the touchscreen. To verify touch input, tap the screen and confirm the cursor responds. If the display or touch does not work, consult your manufacturer's driver installation instructions — some models require additional setup.

### Mapping RFID Cards to Playlists

This project does not require writing data to RFID cards. Each card already has a unique fixed ID. You simply discover that ID and map it to a Spotify playlist.

**Step 1 — Discover a card's ID**

Run the RFID script and scan the card:

    source venv/bin/activate
    python RFID_SPOTIFY_WIIM.py

When you scan a card, the terminal will print its ID, for example:

    Card ID: 13954811

Press Ctrl+C to stop.

**Step 2 — Add it to the mapping file**

Open `rfid_spotify_map.json` and add an entry:

    {
        "13954811": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
    }

**Step 3 — Get a playlist URI**

In Spotify, right-click any playlist → **Share** → **Copy link to playlist**. The URL looks like:

    https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

The playlist ID is everything after `/playlist/`. You can paste the full URL or just the ID — both work.

Repeat for each card you want to map.

## Install

    pip install -r requirements.txt

Dependencies:
- `spotipy`
- `evdev`
- `pygame` (required for the touchscreen display UI)

## Configuration
The script uses `config.json` in the project root.
- If `config.json` does not exist, the script creates it with default values and exits.
- You can also start from `config.example.json`.
- Set `rfid.device_path` to your reader event device, for example `/dev/input/by-id/usb-YOUR_RFID_READER-event-kbd`.

Example config:

    {
        "spotify": {
            "client_id": "YOUR_SPOTIFY_CLIENT_ID",
            "client_secret": "YOUR_SPOTIFY_CLIENT_SECRET",
            "redirect_uri": "http://127.0.0.1:8888/callback",
            "scope": "user-read-playback-state user-modify-playback-state",
            "cache_path": ".spotify_rfid_cache"
        },
        "wiim": {
            "device_name": "WiiM",
            "match_mode": "contains",
            "initial_volume": 50
        },
        "rfid": {
            "mapping_file": "rfid_spotify_map.json",
            "device_path": "/dev/input/by-id/usb-YOUR_RFID_READER-event-kbd"
        },
        "display": {
            "screensaver_image": "screensaver.png",
            "screensaver_delay_seconds": 300
        }
    }

Notes:
- `wiim.match_mode` supports `contains` or `exact`.
- `wiim.initial_volume` is optional. If set, it is clamped to 0-100 before playback starts.
- `display.screensaver_image` is the filename or full path of the image to use as a screensaver. Place the file in the project folder. If not found, the screensaver falls back to bouncing text.
- `display.screensaver_delay_seconds` controls how long the display shows nothing playing before the screensaver activates. Default is 300 (5 minutes).
- On startup, the script merges missing defaults into an older `config.json` and writes the updated file back to disk.

## RFID Mapping File
`rfid.mapping_file` should point to a JSON file that maps card IDs to Spotify playlists.

Example:

    {
        "1234567890": "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
        "9876543210": "https://open.spotify.com/playlist/37i9dQZF1DX4dyzvuaRJ0n",
        "1122334455": "37i9dQZF1DWXRqgorJj26U"
    }

Playlist values can be any of these forms:
- A Spotify playlist URI
- A Spotify playlist URL
- A bare Spotify playlist ID

## Touchscreen Display UI
`display_ui.py` runs alongside the RFID script and shows the current track, album art, artist name, and touch controls (Previous, Play/Pause, Stop, Next) on a Waveshare 5\" DSI touchscreen.

It polls Spotify every 3 seconds and updates the display automatically when a new card is scanned.

### Screensaver
After the delay configured in `display.screensaver_delay_seconds`, a screensaver activates. If the image file specified in `display.screensaver_image` exists in the project folder, it bounces around the screen. Otherwise it falls back to bouncing text.

To set a custom screensaver image, copy any PNG to the project folder:

    scp your-image.png <username>@<pi-ip-address>:~/RFID_Spotify/screensaver.png

Then set `display.screensaver_image` to `screensaver.png` in `config.json`.

## First Run
The script authenticates with Spotify using OAuth and stores the token cache at `spotify.cache_path`. On the first authenticated run, expect to complete the Spotify login flow in a browser.

## Usage

Start the RFID player:

    python RFID_SPOTIFY_WIIM.py

Start the touchscreen display:

    python display_ui.py

List visible Spotify Connect devices:

    python RFID_SPOTIFY_WIIM.py --list-devices

Test a playlist without scanning a card:

    python RFID_SPOTIFY_WIIM.py --test-playlist spotify:playlist:37i9dQZF1DXcBWIGoYBM5M

Behavior at runtime:
- The script retries several times to find the configured WiiM device in Spotify Connect.
- If the RFID mapping file is missing or empty, it prints guidance and exits.
- If a card is scanned with no matching entry, it reports that and waits for the next scan.

## Raspberry Pi Service Setup
Both scripts run automatically on boot as systemd services. The Pi should be configured for desktop autologin so the display UI has a screen to render to.

### Enable desktop autologin

    sudo raspi-config

Navigate to System Options → Boot / Auto Login → Desktop Autologin.

### Create the display service
Create `/etc/systemd/system/spotify-display.service`:

    [Unit]
    Description=Spotify Touchscreen Display
    After=network-online.target graphical.target
    Wants=network-online.target

    [Service]
    User=<your-pi-username>
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=/home/<your-pi-username>/.Xauthority
    WorkingDirectory=/home/<your-pi-username>/RFID_Spotify
    ExecStart=/home/<your-pi-username>/RFID_Spotify/venv/bin/python3 /home/<your-pi-username>/RFID_Spotify/display_ui.py
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=graphical.target

### Create the RFID service
Create `/etc/systemd/system/spotify-rfid.service`:

    [Unit]
    Description=Spotify RFID Playlist Trigger
    After=network-online.target
    Wants=network-online.target

    [Service]
    User=<your-pi-username>
    WorkingDirectory=/home/<your-pi-username>/RFID_Spotify
    ExecStart=/home/<your-pi-username>/RFID_Spotify/venv/bin/python3 /home/<your-pi-username>/RFID_Spotify/RFID_SPOTIFY_WIIM.py
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

### Enable and start both services

    sudo systemctl daemon-reload
    sudo systemctl enable spotify-display.service
    sudo systemctl enable spotify-rfid.service
    sudo systemctl start spotify-display.service
    sudo systemctl start spotify-rfid.service

### Check status and logs

    sudo systemctl status spotify-display.service
    sudo systemctl status spotify-rfid.service
    journalctl -u spotify-display -f
    journalctl -u spotify-rfid -f

### Deploy updates
To pull the latest code from GitHub and restart both services:

    cd ~/RFID_Spotify
    git pull origin main
    sudo systemctl restart spotify-display.service
    sudo systemctl restart spotify-rfid.service
