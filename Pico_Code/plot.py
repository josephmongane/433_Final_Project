import serial
import matplotlib.pyplot as plt
import numpy as np


PORT = "COM7"
BAUD = 115200
NUM_SAMPLES = 1000

ser = serial.Serial(PORT, BAUD, timeout=5)

# Request a batch
ser.reset_input_buffer()
ser.write(f"{NUM_SAMPLES}\n".encode())

angles = []
forces = []

for _ in range(NUM_SAMPLES):
    try:
        raw = ser.readline().decode(errors="replace").strip()
        parts = raw.split()
        if len(parts) == 2:
            t, v = parts[0], parts[1]
            angles.append(float(t))
            forces.append(int(v))
    except ValueError:
        continue

ser.close()

sample_idx = range(len(angles))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

ax1.plot(sample_idx, angles, color='steelblue', linewidth=0.8)
ax1.set_ylabel("Angle")
ax1.set_title("Angle over samples")
ax1.grid(True, alpha=0.3)

ax2.plot(sample_idx, forces, color='tomato', linewidth=0.8)
ax2.set_ylabel("Force")
ax2.set_xlabel("Sample index")
ax2.set_title("Force over samples")
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()