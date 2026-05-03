import argparse
import hashlib
import time
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASELINE_FILE = "baseline.json"
LOG_FILE = "logs.txt"
TARGET_DIR = "test_dir"

# ---------------- HASH ----------------
def get_hash(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

# ---------------- BASELINE ----------------
def create_baseline():
    baseline = {}
    for file in Path(TARGET_DIR).rglob("*"):
        if file.is_file():
            baseline[str(file)] = get_hash(file)

    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=4)

    print("[+] Baseline created")

# ---------------- LOG ----------------
def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.ctime()} - {msg}\n")

# ---------------- EVENT HANDLER ----------------
class MonitorHandler(FileSystemEventHandler):

    def __init__(self, baseline):
        self.baseline = baseline

    def on_modified(self, event):
        if not event.is_directory:
            path = event.src_path
            new_hash = get_hash(path)
            old_hash = self.baseline.get(path)

            if old_hash and new_hash != old_hash:
                msg = f"[ALERT] Modified: {path}"
                print(msg)
                log(msg)

    def on_created(self, event):
        if not event.is_directory:
            msg = f"[ALERT] New file: {event.src_path}"
            print(msg)
            log(msg)

    def on_deleted(self, event):
        if not event.is_directory:
            msg = f"[ALERT] Deleted: {event.src_path}"
            print(msg)
            log(msg)

# ---------------- MONITOR ----------------
def monitor():
    with open(BASELINE_FILE) as f:
        baseline = json.load(f)

    event_handler = MonitorHandler(baseline)
    observer = Observer()
    observer.schedule(event_handler, TARGET_DIR, recursive=True)

    observer.start()
    print("[*] Real-time monitoring started...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

# ---------------- MAIN ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Integrity Monitor")

    parser.add_argument("--init", action="store_true", help="Create baseline")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring")

    args = parser.parse_args()

    if args.init:
        create_baseline()
    elif args.monitor:
        monitor()
    else:
        print("Use --init or --monitor")