import serial
import threading
import math
import pgzrun

PORT = "COM7"
BAUD = 115200

WIDTH = 800
HEIGHT = 450
TITLE = "Sensor Data"

FORCE_MAX = 50000

ser = serial.Serial(PORT, BAUD, timeout=5)

print("Waiting for tare...")
for _ in range(20):
    line = ser.readline().decode(errors="replace").strip()
    print(f"GOT: {line}")
    if line.startswith("AVERAGE FORCE"):
        print("Tare found, starting...")
        break

state = {"angle": 0.0, "force": 0}

def read_serial():
    while True:
        try:
            raw = ser.readline().decode(errors="replace").strip()
            parts = raw.split()
            if len(parts) == 2:
                state["angle"] = float(parts[0])
                state["force"] = int(parts[1])
        except Exception as e:
            print(f"error: {e}")

thread = threading.Thread(target=read_serial, daemon=True)
thread.start()

def draw_gauge(cx, cy, radius, frac, color, label, value_str):
    start_deg = 210
    sweep = 240

    for i in range(241):
        a = math.radians(start_deg - i)
        x = cx + radius * math.cos(a)
        y = cy - radius * math.sin(a)
        screen.draw.filled_circle((int(x), int(y)), 6, (60, 60, 60))

    filled_steps = int(frac * 240)
    for i in range(filled_steps):
        a = math.radians(start_deg - i)
        x = cx + radius * math.cos(a)
        y = cy - radius * math.sin(a)
        screen.draw.filled_circle((int(x), int(y)), 6, color)

    needle_deg = start_deg - frac * sweep
    needle_rad = math.radians(needle_deg)
    nx = cx + (radius - 25) * math.cos(needle_rad)
    ny = cy - (radius - 25) * math.sin(needle_rad)
    screen.draw.line((cx, cy), (int(nx), int(ny)), (255, 255, 255))
    screen.draw.filled_circle((cx, cy), 8, (200, 200, 200))

    screen.draw.text(value_str, center=(cx, cy + radius // 2), fontsize=32, color=color)
    screen.draw.text(label, center=(cx, cy + radius // 2 + 35), fontsize=20, color=(180, 180, 180))

def update():
    pass

def draw():
    screen.fill((15, 15, 15))

    a = state["angle"]
    f = state["force"]

    screen.draw.text(f"a={a:.1f} f={f}", (10, 10), fontsize=24, color=(255,255,255))

    screen.draw.line((WIDTH // 2, 30), (WIDTH // 2, HEIGHT - 30), (50, 50, 50))

    frac_a = max(0, min(1, a / 360.0))
    draw_gauge(WIDTH // 4, HEIGHT // 2, 150, frac_a,
               (100, 180, 255), "ANGLE (deg)", f"{a:.1f}")

    frac_f = max(0, min(1, abs(f) / FORCE_MAX))
    force_color = (220, 60, 60)
    draw_gauge(3 * WIDTH // 4, HEIGHT // 2, 150, frac_f,
               force_color, "FORCE", str(f))

pgzrun.go()
