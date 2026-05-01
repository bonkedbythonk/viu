import os
import shutil
import subprocess
import sys
import tempfile
import termios
import threading
import time
import tty
from sys import exit

import requests
from PIL import Image

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

class PrefetchManager:
    def __init__(self, links):
        self.links = links
        self.temp_dir = tempfile.mkdtemp(prefix="viu_manga_")
        self.cache = {}
        self.lock = threading.Lock()
        self.target_idx = 0
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def set_target(self, idx):
        self.target_idx = idx

    def get_image(self, idx):
        with self.lock:
            if idx in self.cache:
                return self.cache[idx]
        return None

    def _worker(self):
        while not self.stop_event.is_set():
            # fetch up to 5 images ahead
            start = self.target_idx
            end = min(self.target_idx + 5, len(self.links))
            for i in range(start, end):
                if self.stop_event.is_set():
                    break
                with self.lock:
                    if i in self.cache:
                        continue
                try:
                    resp = requests.get(self.links[i], timeout=10)
                    resp.raise_for_status()
                    path = os.path.join(self.temp_dir, f"page_{i}.jpg")
                    with open(path, "wb") as f:
                        f.write(resp.content)
                    with self.lock:
                        self.cache[i] = path
                except Exception:
                    pass
            self.stop_event.wait(0.2)

    def cleanup(self):
        self.stop_event.set()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

def get_key():
    """Read a single keypress (including arrows)."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch1 = sys.stdin.read(1)
        if ch1 == "\x1b":
            ch2 = sys.stdin.read(2)
            return ch1 + ch2
        return ch1
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def draw_banner_at(msg: str, row: int):
    """Move cursor to `row`, then render a centered, cyan-bordered panel."""
    sys.stdout.write(f"\x1b[{row};1H")
    text = Text(msg, justify="center")
    panel = Panel(Align(text, align="center"), border_style="cyan", padding=(1, 2))
    console.print(panel)

def _prepare_image(path1, path2, term_height):
    # Smart resize using Pillow
    # Roughly 20 pixels per row height
    target_height = max(800, term_height * 20)
    
    img1 = Image.open(path1).convert("RGB")
    ratio1 = target_height / img1.height
    new_w1 = int(img1.width * ratio1)
    img1 = img1.resize((new_w1, target_height), Image.Resampling.LANCZOS)
    
    if path2:
        img2 = Image.open(path2).convert("RGB")
        ratio2 = target_height / img2.height
        new_w2 = int(img2.width * ratio2)
        img2 = img2.resize((new_w2, target_height), Image.Resampling.LANCZOS)
        
        # Stitch horizontally
        total_width = new_w1 + new_w2
        spread = Image.new("RGB", (total_width, target_height))
        spread.paste(img1, (0, 0))
        spread.paste(img2, (new_w1, 0))
        
        out_path = os.path.join(os.path.dirname(path1), f"spread_{os.path.basename(path1)}_{os.path.basename(path2)}.jpg")
        spread.save(out_path, format="JPEG", quality=85)
        return out_path
    else:
        out_path = os.path.join(os.path.dirname(path1), f"resized_{os.path.basename(path1)}.jpg")
        img1.save(out_path, format="JPEG", quality=85)
        return out_path

def icat_manga_viewer(image_links: list[str], window_title: str):
    ICAT = shutil.which("kitty")
    if not ICAT:
        console.print("[bold red]kitty (for icat) not found[/]")
        exit(1)

    idx, total = 0, len(image_links)
    title = f"{window_title}  ({total} images)"
    show_banner = True
    show_spread = False
    
    prefetcher = PrefetchManager(image_links)

    try:
        while True:
            console.clear()
            term_width, term_height = shutil.get_terminal_size((80, 24))
            panel_height = 0

            # Calculate space for image based on banner visibility
            if show_banner:
                msg_lines = 3  # Title + blank + controls
                panel_height = msg_lines + 4  # Padding and borders
                image_height = term_height - panel_height - 1
            else:
                image_height = term_height

            prefetcher.set_target(idx)
            
            # Wait for main image
            path1 = None
            while not path1:
                path1 = prefetcher.get_image(idx)
                if not path1:
                    console.clear()
                    draw_banner_at(f"Loading page {idx + 1}...", term_height // 2)
                    time.sleep(0.1)
                    
            path2 = None
            if show_spread and idx + 1 < total:
                while not path2:
                    path2 = prefetcher.get_image(idx + 1)
                    if not path2:
                        console.clear()
                        draw_banner_at(f"Loading spread {idx + 2}...", term_height // 2)
                        time.sleep(0.1)
            
            # Use Pillow to dynamically resize and/or spread the images for fast ICAT draw
            final_img_path = _prepare_image(path1, path2, image_height)
            
            console.clear()

            subprocess.run(
                [
                    ICAT,
                    "+kitten",
                    "icat",
                    "--clear",
                    "--scale-up",
                    "--place",
                    f"{term_width}x{image_height}@0x0",
                    "--z-index",
                    "-1",
                    final_img_path,
                ],
                check=False,
            )

            if show_banner:
                spread_status = "ON" if show_spread else "OFF"
                idx_display = f"{idx + 1}-{idx + 2}" if show_spread and idx + 1 < total else f"{idx + 1}"
                controls = (
                    f"[{idx_display}/{total}]  Prev: [h/←]   Next: [l/→]   "
                    f"Toggle Banner: [b]   Spread: [s] ({spread_status})   Quit: [q/Ctrl-C]"
                )
                msg = f"{title}\n\n{controls}"
                start_row = term_height - panel_height
                draw_banner_at(msg, start_row)

            # key handling
            key = get_key()
            step = 2 if show_spread else 1
            if key in ("l", "\x1b[C"):
                if idx + step < total:
                    idx += step
                else:
                    idx = total - 1
            elif key in ("h", "\x1b[D"):
                if idx - step >= 0:
                    idx -= step
                else:
                    idx = 0
            elif key == "b":
                show_banner = not show_banner
            elif key == "s":
                show_spread = not show_spread
                # adjust index so it doesn't overflow if toggling at end
                if show_spread and idx == total - 1 and total > 1:
                    idx -= 1
            elif key in ("q", "\x03"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        prefetcher.cleanup()
        console.clear()
        console.print("Exited viewer.", style="bold")
