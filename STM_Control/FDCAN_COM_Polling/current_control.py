import serial
import matplotlib.pyplot as plt

PORT = '/dev/cu.usbmodem102'
BAUD     = 115200
SAMPLES  = 400

def read_itest_data():
    desired = []
    actual  = []

    print(f"Connecting to {PORT} at {BAUD} baud...")

    with serial.Serial(PORT, BAUD, timeout=5) as ser:
        print("Connected. Sending 'A' to trigger ITEST...\n")
        ser.reset_input_buffer()
        
        # Trigger the ITEST sequence
        ser.write(b'A')

        while len(desired) < SAMPLES:
            line = ser.readline().decode('utf-8').strip()

            if not line:
                continue

            parts = line.split(',')
            if len(parts) == 2:
                try:
                    d = int(parts[0].strip())
                    a = int(parts[1].strip())
                    desired.append(d)
                    actual.append(a)
                    print(f"Sample {len(desired):03d}/{SAMPLES} | "
                          f"Desired: {d:4d} mA | Actual: {a:4d} mA")
                except ValueError:
                    continue

    return desired, actual

def plot_results(desired, actual):
    samples = range(len(desired))

    plt.figure(figsize=(12, 5))
    plt.plot(samples, desired, label='Desired (mA)', linestyle='--', color='blue')
    plt.plot(samples, actual,  label='Actual (mA)',  linestyle='-',  color='red')
    plt.xlabel('Sample Index')
    plt.ylabel('Current (mA)')
    plt.title('ITEST: Desired vs Actual Current')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('itest_results.png')
    print("\nPlot saved as itest_results.png")
    plt.show()

def save_csv(desired, actual):
    with open('itest_results.csv', 'w') as f:
        f.write("desired_mA,actual_mA\n")
        for d, a in zip(desired, actual):
            f.write(f"{d},{a}\n")
    print("Data saved to itest_results.csv")

if __name__ == "__main__":
    desired, actual = read_itest_data()
    print(f"\nReceived {len(desired)} samples successfully.")
    save_csv(desired, actual)
    plot_results(desired, actual)