from root import get_project_root
from datetime import datetime, timedelta
from curl_cffi import requests, curl
import time, sys, os, random, json
import etc


ROOT = get_project_root()
MAX_REQUESTS = 9999     # Would be 10,000, but it counts from 0, so 9,999
COOLDOWN_JSON = {"cooldownTimerValue": 14400, "cooldownDateDelta": None, "expirationTime": None}
url = "http://www.boomlings.com/database/downloadGJLevel22.php"


def block_user(cooldown_path) -> None:
    """Blocks the user and enforces a cooldown timer onto them."""
    if os.path.exists(cooldown_path):
        with open(cooldown_path, "r") as cool:
            # Get cooldown expiration time and reformat it from iso-format
            cooldown_data = json.load(cool)
            expiration_key = cooldown_data["expirationTime"]

        # Verify the existence of the expiration date
        if expiration_key:
            cooldown_expiration = datetime.fromisoformat(expiration_key)
        else:   # If the expirationTime is None
            cooldown_expiration = datetime.now() + timedelta(seconds=cooldown_data["cooldownTimerValue"])
            with open(cooldown_path, "w") as cool:
                cooldown_data["expirationTime"] = cooldown_expiration.isoformat()
                json.dump(cooldown_data, cool)

        # Negative time_left means cooldown has expired. If so, proceed like normal
        time_left = cooldown_expiration - datetime.now()
        if time_left.total_seconds() >= 0:
            print(f"\n{MAX_REQUESTS+1} requests reached. Cooldown must expire to make another request.")

            # Live countdown in terminal here
            while True:
                remaining_seconds = (cooldown_expiration - datetime.now()).total_seconds()
                if remaining_seconds < 0:
                    print("\n\n***Cooldown expired!***")
                    break

                # Break down the total seconds into hours, minutes, and seconds
                hours, remainder = divmod(int(remaining_seconds), 3600)
                minutes, seconds = divmod(remainder, 60)

                sys.stdout.write(f"\rTime remaining: {hours:02d}:{minutes:02d}:{seconds:02d}")
                sys.stdout.flush()
                time.sleep(1)

        return
    
    else:   # Execution should never reach this point!
        print("\nYour cooldown timer is missing. Closing... (see request_cooldown)")
        
        time.sleep(5)
        sys.exit(1) # Standard sys.exit() in this scenario


def fetch(level_id: str) -> str:
    """Fetches a level ID (in string form) from RobTop's servers and returns the level string.\n
    Nonexistent levels return -1 as a string."""

    # Verify that the user is allowed to request, and initialize requests left #
    directory = os.path.join(ROOT, "request_cooldown")
    os.makedirs(directory, exist_ok=True)

    # Read the request counter or initialize it, and also read or initialize cooldown
    counter_path = os.path.join(directory, "req_counter.json")
    cooldown_path = os.path.join(directory, "cooldown_time.json")
    if os.path.exists(counter_path):
        try:
            with open(counter_path, "r") as counter:
                request_counter = json.load(counter)[0]
        except json.decoder.JSONDecodeError:
            # For a corrupted req_counter.json file, rewrite it
            with open(counter_path, "w") as counter:
                json.dump([0], counter)
                request_counter = 0
    else:
        # For a nonexistent req_counter.json file, write it
        with open(counter_path, "w") as counter:
            json.dump([0], counter)
            request_counter = 0

    if not os.path.exists(cooldown_path):
        with open(cooldown_path, "w") as cool:
            # Initialize new data, cooldown JSON data here
            cooldown_data = COOLDOWN_JSON
            json.dump(cooldown_data, cool)
    else:
        with open(cooldown_path, "r") as cool:
            # Cooldown JSON data here
            cooldown_data = json.load(cool)

    # Block user if cooldown is still pending #
    if request_counter > MAX_REQUESTS:
        block_user(cooldown_path)
        # Reset everything
        request_counter = 0
        with open(cooldown_path, "w") as cool:
            # Write fresh data, cooldown JSON data here
            cooldown_data = COOLDOWN_JSON
            json.dump(cooldown_data, cool)
    ############################################################################

    # # Uncomment to activate fake requests
    # print("You made a request.")
    # # Tick counter up and write it
    # request_counter += 1
    # with open(counter_path, "w") as counter:
    #     json.dump([request_counter], counter)
    
    # if request_counter > MAX_REQUESTS:
    #     # Get the cooldown expiration time and iso-format it. Write new data over old data
    #     cooldown_expiration = (datetime.now() + timedelta(seconds=cooldown_data["cooldownTimerValue"])).isoformat()
    #     cooldown_data["expirationTime"] = cooldown_expiration
    #     with open(cooldown_path, "w") as cool:
    #         json.dump(cooldown_data, cool)
    # return "-1"
    # ######################################

    # The expanded dictionary uses the game client's raw validation handshake
    payload = {
        "levelID": level_id,        # The target level ID
        "secret": "Wmfd2893gb7",    # The base system configuration key
    }

    headers = {
        "User-Agent": "",
    }

    print(f"Connecting to server... (ID {level_id})")
    for connect_try in range(1, 4): # Three connection attempts
        try:    # Catch exception for no connection. If so, try another. If all tries fail, exit
            response = requests.post(url, data=payload, headers=headers, impersonate="chrome")
            break
        except curl.CurlError:
            if connect_try < 3: # Less than 3 tries or else exit
                print(f"Not connected/connection lost, trying again in 5 seconds... ({connect_try})")
                
                time.sleep(5)
                continue
            else:
                print(f"Not connected/connection lost, closing the program... ({connect_try})")

                time.sleep(5)
                etc.exit_program()

    # Tick counter up and write it. If > MAX_REQUESTS, write the cooldown expiration for next time as well
    request_counter += 1
    with open(counter_path, "w") as counter:
        json.dump([request_counter], counter)
    
    if request_counter > MAX_REQUESTS:
        # Get the cooldown expiration time and iso-format it. Write new data over old data
        cooldown_expiration = (
            datetime.now() + timedelta(seconds=cooldown_data["cooldownTimerValue"])
            ).isoformat()

        cooldown_data["expirationTime"] = cooldown_expiration
        with open(cooldown_path, "w") as cool:
            json.dump(cooldown_data, cool)
    ##############################################

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
        etc.exit_program()
    else:   # if we good
        level_string = response_text.strip()

        time.sleep(random.uniform(4.5, 5.5))   # intentional slowdown to avoid over-requesting + jitter
        # WARNING: DO NOT MITIGATE/REMOVE THIS COOLDOWN TIMER.
        # REQUESTING TOO FAST/MUCH WILL RESULT IN AN IP-BAN.

        # return the string, replacing newlines with spaces (in cases like ID 809914, which features a hacked newline)
        return level_string.replace("\n", " ")


if __name__ == "__main__":
    lvl_id = "188622"
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