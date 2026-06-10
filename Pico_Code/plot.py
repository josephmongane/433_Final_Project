import serial
import threading
import math
import pgzrun

PORT = "COM7"
BAUD = 115200

WIDTH = 900
HEIGHT = 500
TITLE = "Ball & Wall"

# --- Serial -----------------------------------------------------------

ser = serial.Serial(PORT, BAUD, timeout=5)

print("Waiting for tare (skipped if not found)...")
for _ in range(20):
    line = ser.readline().decode(errors="replace").strip()
    print(f"GOT: {line}")
    if line.startswith("AVERAGE FORCE"):
        print("Tare found, starting...")
        break
else:
    print("No tare message found, starting anyway...")

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

threading.Thread(target=read_serial, daemon=True).start()

# --- Scene constants --------------------------------------------------

BALL_RADIUS   = 22
WALL_X        = WIDTH - 120        # x position of the wall face
BALL_Y        = HEIGHT // 2        # ball stays on horizontal axis
TRACK_Y       = HEIGHT // 2
TRACK_X_MIN   = 80
TRACK_X_MAX   = WALL_X - BALL_RADIUS

# The encoder reads ~308 deg at rest. ANGLE_ZERO is that rest position.
# Relative angle = (raw - ANGLE_ZERO) mod 360, so rotation toward the wall gives positive values.
# Flip the sign in relative_angle() if your motor turns the other way.
ANGLE_ZERO = 308.0   # tune to your resting encoder reading

def relative_angle(raw):
    delta = (raw - ANGLE_ZERO + 360) % 360
    if delta > 180:
        delta -= 360   # range [-180, 180]
    return delta

# Relative zones: 0-5 ramp in, 5-100 wall contact, otherwise retreated

FORCE_MAX     = 50_000             # raw units that map to "full squish"
MAX_SQUISH    = 14                 # pixels the ball flattens at max force
SPARK_LIFETIME = 18                # frames sparks live

# --- Spark state ------------------------------------------------------

sparks = []  # list of {"x","y","vx","vy","life"}

def spawn_sparks(x, y, count=8):
    import random
    for _ in range(count):
        angle = random.uniform(-math.pi / 2 - 0.6, -math.pi / 2 + 0.6)
        speed = random.uniform(2, 6)
        sparks.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": SPARK_LIFETIME,
        })

# --- Map angle → ball X -----------------------------------------------

_prev_zone = "free"
_spark_cooldown = 0

def angle_to_ball_x(angle):
    """Return ball centre X based on angle reading."""
    if angle <= 5:
        # ramp in: 0 deg → left edge, 5 deg → just touching wall
        t = max(0.0, angle / 5.0)
        return int(TRACK_X_MIN + t * (TRACK_X_MAX - TRACK_X_MIN))
    elif angle < 100:
        return TRACK_X_MAX   # pressed against wall
    else:
        # retreat proportionally back to left
        t = min(1.0, (angle - 100) / 80.0)
        return int(TRACK_X_MAX - t * (TRACK_X_MAX - TRACK_X_MIN))

# --- Draw helpers ------------------------------------------------------

def draw_wall():
    # Brick-style wall
    brick_w, brick_h = 60, 30
    cols = 2
    rows = HEIGHT // brick_h + 1
    for row in range(rows):
        for col in range(cols):
            offset = (brick_w // 2) if (row % 2 == 1) else 0
            bx = WALL_X + col * brick_w - offset
            by = row * brick_h - brick_h // 2
            screen.draw.filled_rect(
                Rect(bx + 1, by + 1, brick_w - 2, brick_h - 2),
                (160, 100, 60)
            )
            screen.draw.rect(
                Rect(bx, by, brick_w, brick_h),
                (120, 70, 40)
            )
    # solid face line
    screen.draw.line((WALL_X, 0), (WALL_X, HEIGHT), (90, 55, 25))

def draw_track():
    # Dashed horizontal guide line
    dash_len = 12
    x = TRACK_X_MIN
    while x < WALL_X:
        screen.draw.line(
            (x, TRACK_Y),
            (min(x + dash_len, WALL_X), TRACK_Y),
            (60, 60, 80)
        )
        x += dash_len * 2

def draw_ball(bx, by, squish):
    rx = max(BALL_RADIUS - squish, 6)
    ry = BALL_RADIUS + int(squish * 0.6)  # conservation of volume feel

    # Shadow
    screen.draw.filled_circle((bx + 4, by + 6), rx - 2, (30, 30, 30))

    # Body – draw as ellipse via filled circles at varying y offsets
    # pgzero has no filled_ellipse; approximate with scaled circles
    steps = max(ry * 2, 1)
    for dy in range(-ry, ry + 1):
        # ellipse equation: (dx/rx)^2 + (dy/ry)^2 = 1  →  dx = rx * sqrt(1 - (dy/ry)^2)
        ratio = 1 - (dy / ry) ** 2
        if ratio < 0:
            continue
        dx = int(rx * math.sqrt(ratio))
        # colour gradient: lighter at top
        intensity = int(80 + 120 * (1 - (dy + ry) / (2 * ry)))
        screen.draw.line(
            (bx - dx, by + dy),
            (bx + dx, by + dy),
            (intensity, intensity, 255)
        )

    # Highlight
    screen.draw.filled_circle((bx - rx // 3, by - ry // 3), max(rx // 4, 3), (220, 220, 255))

def draw_force_bar(force):
    """Vertical bar on the right showing contact force."""
    bar_x = WALL_X + 20
    bar_top = 60
    bar_bot = HEIGHT - 60
    bar_h = bar_bot - bar_top
    bar_w = 18

    screen.draw.filled_rect(Rect(bar_x, bar_top, bar_w, bar_h), (40, 40, 50))

    frac = max(0.0, min(1.0, abs(force) / FORCE_MAX))
    fill_h = int(frac * bar_h)
    if fill_h > 0:
        r = int(80 + 175 * frac)
        g = int(200 - 180 * frac)
        b = 60
        screen.draw.filled_rect(
            Rect(bar_x, bar_bot - fill_h, bar_w, fill_h),
            (r, g, b)
        )

    screen.draw.rect(Rect(bar_x, bar_top, bar_w, bar_h), (100, 100, 120))
    screen.draw.text("F", centerx=bar_x + bar_w // 2, centery=bar_top - 16,
                     fontsize=18, color=(180, 180, 200))

def draw_sparks():
    for s in sparks:
        alpha = s["life"] / SPARK_LIFETIME
        c = (int(255 * alpha), int(180 * alpha), 0)
        screen.draw.filled_circle((int(s["x"]), int(s["y"])), max(1, int(3 * alpha)), c)

def draw_hud(angle, force, squish):
    screen.draw.text(f"angle: {angle:.1f}°", (10, 10), fontsize=22, color=(200, 200, 220))
    screen.draw.text(f"force: {force}",       (10, 36), fontsize=22, color=(200, 200, 220))
    contact_label = "CONTACT" if squish > 0 else "free"
    col = (80, 255, 120) if squish == 0 else (255, 100, 80)
    screen.draw.text(contact_label, (10, 62), fontsize=20, color=col)

# --- pgzero lifecycle -------------------------------------------------

def update():
    global _prev_zone, _spark_cooldown

    for s in sparks:
        s["x"] += s["vx"]
        s["y"] += s["vy"]
        s["vy"] += 0.3
        s["life"] -= 1
    sparks[:] = [s for s in sparks if s["life"] > 0]

    angle = relative_angle(state["angle"])
    in_contact = (5 <= angle < 100)
    if in_contact and _prev_zone != "contact" and _spark_cooldown == 0:
        spawn_sparks(WALL_X - BALL_RADIUS, BALL_Y)
        _spark_cooldown = 20
    _prev_zone = "contact" if in_contact else "free"
    if _spark_cooldown > 0:
        _spark_cooldown -= 1

def draw():
    screen.fill((18, 18, 28))

    angle = relative_angle(state["angle"])
    force = state["force"]

    bx = angle_to_ball_x(angle)
    in_contact = (5 <= angle < 100)
    squish = int(MAX_SQUISH * min(1.0, abs(force) / FORCE_MAX)) if in_contact else 0

    draw_track()
    draw_wall()
    draw_ball(bx, BALL_Y, squish)
    draw_sparks()
    draw_force_bar(force)
    draw_hud(angle, force, squish)

pgzrun.go()