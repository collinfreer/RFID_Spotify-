import json
import os
import sys
import time
import threading
import urllib.request
import io

try:
    import pygame
except ImportError:
    print("Please install pygame: pip install pygame")
    sys.exit(1)

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from spotipy.cache_handler import CacheFileHandler
except ImportError:
    print("Please install spotipy: pip install spotipy")
    sys.exit(1)

CONFIG_FILE = "config.json"

SCREEN_W = 800
SCREEN_H = 480
FPS = 30
POLL_INTERVAL = 3

BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GRAY       = (50, 50, 50)
LIGHT_GRAY = (180, 180, 180)
SPOTIFY_GREEN = (30, 215, 96)
BTN_PLAY   = (30, 150, 60)
BTN_STOP   = (160, 30, 30)
BTN_DEFAULT = (60, 60, 60)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def create_spotify_client(config):
    sc = config["spotify"]
    auth_manager = SpotifyOAuth(
        client_id=sc["client_id"],
        client_secret=sc["client_secret"],
        redirect_uri=sc["redirect_uri"],
        scope=sc["scope"],
        cache_handler=CacheFileHandler(
            cache_path=sc.get("cache_path", ".spotify_rfid_cache")
        ),
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def download_image(url, size=(300, 300)):
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read()
        surface = pygame.image.load(io.BytesIO(data))
        return pygame.transform.scale(surface, size)
    except Exception as e:
        print(f"Album art download failed: {e}")
        return None

class SpotifyState:
    def __init__(self, sp):
        self.sp = sp
        self.lock = threading.Lock()
        self.track_name = ""
        self.artist_name = ""
        self.album_art = None
        self.is_playing = False
        self._current_track_id = None
        self._last_poll = 0

    def poll(self):
        if time.time() - self._last_poll < POLL_INTERVAL:
            return
        self._last_poll = time.time()
        try:
            playback = self.sp.current_playback()
            if not playback or not playback.get("item"):
                with self.lock:
                    self.track_name = "Nothing playing"
                    self.artist_name = ""
                    self.is_playing = False
                return
            item = playback["item"]
            track_id   = item["id"]
            is_playing = playback["is_playing"]
            track_name = item["name"]
            artist_name = ", ".join(a["name"] for a in item["artists"])
            images = item["album"]["images"]
            art_url = images[1]["url"] if len(images) > 1 else images[0]["url"]
            with self.lock:
                self.is_playing  = is_playing
                self.track_name  = track_name
                self.artist_name = artist_name
                if track_id != self._current_track_id:
                    self._current_track_id = track_id
                    art = download_image(art_url, size=(300, 300))
                    if art:
                        self.album_art = art
        except Exception as e:
            print(f"Spotify poll error: {e}")

    def force_refresh(self):
        self._last_poll = 0

    def toggle_play_pause(self):
        try:
            if self.is_playing:
                self.sp.pause_playback()
            else:
                self.sp.start_playback()
            self.force_refresh()
        except Exception as e:
            print(f"Play/pause error: {e}")

    def stop(self):
        try:
            self.sp.pause_playback()
            self.force_refresh()
        except Exception as e:
            print(f"Stop error: {e}")

    def next_track(self):
        try:
            self.sp.next_track()
            time.sleep(0.5)
            self.force_refresh()
        except Exception as e:
            print(f"Next track error: {e}")

    def prev_track(self):
        try:
            self.sp.previous_track()
            time.sleep(0.5)
            self.force_refresh()
        except Exception as e:
            print(f"Previous track error: {e}")

def draw_button(screen, font, label, rect, color=BTN_DEFAULT):
    pygame.draw.rect(screen, color, rect, border_radius=14)
    text = font.render(label, True, WHITE)
    text_rect = text.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2))
    screen.blit(text, text_rect)

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def main():
    config = load_config()
    sp     = create_spotify_client(config)
    state  = SpotifyState(sp)

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    pygame.display.set_caption("Spotify Display")
    pygame.mouse.set_visible(False)

    font_track  = pygame.font.SysFont("sans", 26, bold=True)
    font_artist = pygame.font.SysFont("sans", 22)
    font_status = pygame.font.SysFont("sans", 20)
    font_btn    = pygame.font.SysFont("sans", 22, bold=True)

    clock = pygame.time.Clock()

    ART_SIZE   = 300
    ART_X, ART_Y = 30, 80

    BTN_W, BTN_H = 155, 60
    BTN_GAP      = 14
    BTN_Y        = SCREEN_H - BTN_H - 20
    total_btn_w  = 4 * BTN_W + 3 * BTN_GAP
    BTN_START_X  = (SCREEN_W - total_btn_w) // 2

    def btn_rect(index):
        x = BTN_START_X + index * (BTN_W + BTN_GAP)
        return pygame.Rect(x, BTN_Y, BTN_W, BTN_H)

    rect_prev  = btn_rect(0)
    rect_play  = btn_rect(1)
    rect_stop  = btn_rect(2)
    rect_next  = btn_rect(3)

    INFO_X     = ART_X + ART_SIZE + 30
    INFO_WIDTH = SCREEN_W - INFO_X - 20

    running = True
    while running:
        state.poll()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if rect_prev.collidepoint(pos):
                    state.prev_track()
                elif rect_play.collidepoint(pos):
                    state.toggle_play_pause()
                elif rect_stop.collidepoint(pos):
                    state.stop()
                elif rect_next.collidepoint(pos):
                    state.next_track()

        screen.fill(BLACK)

        with state.lock:
            album_art   = state.album_art
            track_name  = state.track_name
            artist_name = state.artist_name
            is_playing  = state.is_playing

        if album_art:
            screen.blit(album_art, (ART_X, ART_Y))
        else:
            pygame.draw.rect(screen, GRAY, (ART_X, ART_Y, ART_SIZE, ART_SIZE), border_radius=10)
            no_art = font_artist.render("No album art", True, LIGHT_GRAY)
            screen.blit(no_art, no_art.get_rect(center=(ART_X + ART_SIZE // 2, ART_Y + ART_SIZE // 2)))

        y_text = ART_Y + 10
        for line in wrap_text(track_name, font_track, INFO_WIDTH):
            surf = font_track.render(line, True, WHITE)
            screen.blit(surf, (INFO_X, y_text))
            y_text += font_track.get_linesize() + 2

        y_text += 6
        for line in wrap_text(artist_name, font_artist, INFO_WIDTH):
            surf = font_artist.render(line, True, LIGHT_GRAY)
            screen.blit(surf, (INFO_X, y_text))
            y_text += font_artist.get_linesize() + 2

        y_text += 14
        status_label = "Playing" if is_playing else "Paused"
        status_surf  = font_status.render(status_label, True, SPOTIFY_GREEN)
        screen.blit(status_surf, (INFO_X, y_text))

        draw_button(screen, font_btn, "Prev",  rect_prev)
        play_label = "Pause" if is_playing else "Play"
        draw_button(screen, font_btn, play_label, rect_play, color=BTN_PLAY)
        draw_button(screen, font_btn, "Stop",  rect_stop, color=BTN_STOP)
        draw_button(screen, font_btn, "Next",  rect_next)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
