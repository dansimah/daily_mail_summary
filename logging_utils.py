from datetime import datetime


def log(message):
    """Prints a timestamped message and forces it to output immediately."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)
