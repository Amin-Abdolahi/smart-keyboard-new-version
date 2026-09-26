# test_hook.py
# تست عملکرد keyboard hook

import keyboard as kb
import time

print("تست keyboard hook...")
print("هر کلیدی که بزنی، scan_code و name اون چاپ میشه.")
print("برای خروج: Ctrl+C\n")

def on_event(event):
    if event.event_type == 'down':
        print(f"name={event.name!r}, scan={event.scan_code}, type={event.event_type}")

hook = kb.hook(on_event)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    kb.unhook(hook)
    print("\nپایان.")