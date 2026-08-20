from root import get_project_root
from fetch_level import fetch
from get_level_data import get_level_data
import os
import json
import time


ROOT = get_project_root()


def download(floor: int, amount: int):
    """Downloads levels from the server and caches them in DOWNLOADS as json files.\n
    floor: the starting level ID\n
    amount: the amount of IDs to download"""

    # Here's the master loop that handles mass level downloading
    ceiling = floor + amount
    for id in range(floor, ceiling):
        level_data = get_level_data(id)

        # check if there is any level data
        if level_data:
            level_name = level_data[0]
            level_string = level_data[2]
        else:
            # no level data means it's a nonexistent ID
            continue

        # Here we actually want the raw level string itself
        level_json = {"levelID": id, "levelName": level_name, "levelString": level_string}

        # write levels to disk
        directory = os.path.join(ROOT, "DOWNLOADED/")
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, f"{id}.json"), "w") as level:
            json.dump(level_json, level)

    print("Downloading finished. (See DOWNLOADED)")
    time.sleep(5)
    return


if __name__ == "__main__":
    try:
        print("--- Use CTRL+C to CLOSE at any time ---\n")

        lower_bound = int(input("Starting level ID >>> "))
        id_amount = int(input("How many IDs are we downloading? >>> "))

        # Let the downloading commence!
        print("\nDownloading levels from server...")

        download(lower_bound, id_amount)
    except KeyboardInterrupt:
        print("\nClosing the program... (See DOWNLOADED)")

        time.sleep(5)
        sys.exit(0)