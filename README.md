# RFID_Spotify
Trigger a Spotify playlist using an RFID card

Pre-requisites:
Must have a Spotify premium account
Must get Spotify API client ID and secret
Must have a Raspberry Pi (I used 3b)
Must have a WIIM device as a connected device in your Spotify premium account (trust me - this is WAYYY easier than trying to make Raspberry Pi work with Bluetooth)
Must have RFID card reader
Must have programmable RFID cards

Install Python dependencies:
- `pip install -r requirements.txt`

Copy config.example.json to config.json and fill in your local values.

Set `rfid.device_path` to your reader event device, for example `/dev/input/by-id/usb-YOUR_RFID_READER-event-kbd`.

Your config.json file should contain:
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
    }
}

## Raspberry Pi service setup

To run the player automatically on boot without an attached keyboard session:

1. Install dependencies:
    `pip install -r requirements.txt`
2. Put the project in a stable location such as `/home/pi/RFID_Spotify`.
3. Set `config.json`, especially `rfid.device_path`, to your RFID reader event device.
4. Create `/etc/systemd/system/rfid-spotify.service` with contents like:

```
[Unit]
Description=RFID Spotify Player
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RFID_Spotify
ExecStart=/usr/bin/python3 /home/pi/RFID_Spotify/RFID_SPOTIFY_WIIM.py
Restart=always

[Install]
WantedBy=multi-user.target
```

5. Enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl enable rfid-spotify
sudo systemctl start rfid-spotify
```

6. Check service health and logs:

```
sudo systemctl status rfid-spotify
journalctl -u rfid-spotify -f
```

