from root import get_project_root
from datetime import datetime
import requests, time, sys, os


ROOT = get_project_root()
url = "http://www.boomlings.com/database/downloadGJLevel22.php"


def fetch(level_id: str) -> str:
    """Fetches a level ID (in string form) from RobTop's servers and returns the level string.\n
    Nonexistent levels return -1 as a string."""
    # The expanded dictionary uses the game client's raw validation handshake
    payload = {
        "levelID": level_id,        # The target level ID
        "secret": "Wmfd2893gb7",  # The base system configuration key
    }

    headers = {
        "User-Agent": "",
    }

    print(f"Connecting to server... (ID {level_id})")
    for connect_try in range(1, 4): # Three connection attempts
        try:    # Catch exception for no connection. If so, try another. If it fails three times, quit
            response = requests.post(url, data=payload, headers=headers)
            break
        except requests.exceptions.ConnectionError:
            if connect_try < 3:
                print(f"Not connected/connection lost, trying again in 5 seconds... ({connect_try})")
                time.sleep(5)
                continue
            else:
                print(f"Not connected/connection lost, closing the program... ({connect_try})")
                time.sleep(5)
                sys.exit(1)

    response_text = response.text

    # the moment of truth
    if "<body>" in response_text:   # in case Cloudflare gets in the way
        dir = os.path.join(ROOT, "LOGS/")
        os.makedirs(dir, exist_ok=True)

        with open(os.path.join(dir, "Recent_error_log.txt"), "w") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"*** Culprit level ID: {level_id} [ Logged: {timestamp} ]***")
            log.write(f"\n\n{response_text}")
        print("Cloudflare interception, closing the program... (see LOGS > Recent_error_log.txt)")

        time.sleep(5)
        sys.exit(1)
    else:   # if we good
        level_string = response_text.strip()

        time.sleep(5)   # intentional slowdown to avoid over-requesting
        # WARNING: DO NOT MITIGATE/REMOVE THIS COOLDOWN TIMER.
        # REQUESTING TOO FAST COULD RESULT IN AN IP-BAN.

        # return the string      
        return level_string


if __name__ == "__main__":
    lvl_id = "128"
    lvl_string = fetch(lvl_id)

    # verify the level's existence before writing
    if lvl_string != "-1":
        temp_dir = os.path.join(ROOT, "temp_logs/")
        os.makedirs(temp_dir, exist_ok=True)

        with open(os.path.join(temp_dir, "level_string.txt"), "w") as f:
            f.write(lvl_string)
        print("Written to temp_logs > level_string.txt!")
    else:
        print("This level doesn't exist.")