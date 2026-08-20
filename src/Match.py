from get_level_data import get_level_data
from list_object_data import list_object_data
from decode_level import decode
from notif_player import play
from root import get_project_root
from download import download
from datetime import datetime
from pathlib import Path
import sys
import os
import json
import time
import questionary
import math


ROOT = get_project_root()
SETTINGS = os.path.join(ROOT, "settings.json")
# Define all the keys that MUST be present in the settings file
REQUIRED_SETTINGS_KEYS = [
    "fullNotifSound",
    "partialNotifSound",
    "partialMatchPercentageThreshold",
]
FULL_NOTIF_PATH = os.path.join(ROOT, "notif_sounds/Full_match.ogg")
PARTIAL_NOTIF_PATH = os.path.join(ROOT, "notif_sounds/Partial_match.ogg")


###################################################################
def init_settings():
    """Initializes the settings.
    If settings.json doesn't already exist, it creates a fresh file. Then, it reads that JSON and returns it for use elsewhere."""

    # Initialize settings.json if nonexistent
    if not os.path.exists(SETTINGS):
        with open(SETTINGS, "w") as new_settings:
            json.dump(
                {
                    "fullNotifSound": True,
                    "partialNotifSound": True,
                    "partialMatchPercentageThreshold": 50.0,
                    }, new_settings
                )

    # Load the settings.json file
    with open(SETTINGS, "r") as read_settings:
        settings = json.load(read_settings)

    return settings
###################################################################


all_settings = init_settings()  # GLOBAL SETTINGS HERE
# Verify the existence of all settings keys, delete and rebuild settings.json if one is missing
if not all(key in all_settings for key in REQUIRED_SETTINGS_KEYS):
    os.remove(SETTINGS)
    all_settings = init_settings()  # OR GLOBAL SETTINGS HERE

# The match-percentage threshold that must be exceeded for a level to be considered a partial match
min_match_threshold = all_settings["partialMatchPercentageThreshold"]

# NOTE: bundle with this command (activate a venv first):
# pyinstaller --clean --onefile --hidden-import=_cffi_backend src/Match.py


def settings_options():
    """Manages the settings."""
    global min_match_threshold

    while True: # Settings loop
        try:
            choice = questionary.select(
                "Settings",
                choices=[
                    f"Full match notification sound: {'ON' if all_settings['fullNotifSound'] else 'OFF'}",
                    f"Partial match notification sound: {'ON' if all_settings['partialNotifSound'] else 'OFF'}",
                    f"Partial match percentage threshold: {all_settings['partialMatchPercentageThreshold']}%",
                    "-Back to main menu-",
                ]
            ).ask()
            
            if "Full match notification sound" in choice:
                # Flip the boolean state
                all_settings["fullNotifSound"] = not all_settings["fullNotifSound"]

            elif "Partial match notification sound" in choice:
                # Flip the boolean state
                all_settings["partialNotifSound"] = not all_settings["partialNotifSound"]

            elif "Partial match percentage threshold" in choice:
                # Get user to input new percent
                threshold_message = (
                    "Change the partial match percentage threshold (0% - 100%)\n"
                    "[Closer to 0% = More sensitive]\n"
                    "[Closer to 100% = More strict]\n"
                    ">>> "
                )
                while True: # Validate user input
                    try:
                        new_threshold = float(input(threshold_message))
                        if 0 <= new_threshold <= 100:
                            all_settings["partialMatchPercentageThreshold"] = new_threshold
                            min_match_threshold = all_settings["partialMatchPercentageThreshold"]
                            break
                        else:
                            print("\nInvalid input. Try again.")
                            continue
                    except ValueError:
                        print("\nInvalid input. Try again.")
                        continue

            elif choice == "-Back to main menu-":
                # Save changes
                with open(SETTINGS, "w") as settings:
                    json.dump(all_settings, settings)
                    
                return

        except TypeError:   # The user pressed CTRL+C, but it causes a TypeError here instead
            print("\nClosing the program...")

            time.sleep(2)
            sys.exit(0)


def get_listed_obj_data_wrapper(id: int):
    """MAKES the comparison level's object list\n
    
    Combines get_level_data and list_object_data. Takes a level ID and returns a tuple in this order:\n
    Level name (0) | List of objects (1)\n
    If the level data doesn't exist, NoneType is returned instead"""

    # get level data, then the list of object data
    lvl_data = get_level_data(id)
    if not lvl_data:    # check for the data/ID's existence
        return      # return NoneType if nonexistent
    
    lvl_name = lvl_data[0]
    obj_data = lvl_data[1]
    obj_list = list_object_data(obj_data)

    return lvl_name, obj_list


def get_comp_obj_list(comp_obj_id: int):
    """RETRIEVES the comparison level's object list\n
    
    Determines whether to take the comparison object data from the server, or from cache.
    After that, it gets the object data from one of the two ways and returns a list of its object data.\n

    If the ID's file doesn't exist in cache, it will be fetched right from the server.\n
    If the ID's file is in cache, it will be loaded from there instead.\n
    If the comparison level ID is nonexistent, NoneType will be returned instead."""

    # Access the cached comparison level download if available, otherwise make one for next time
    cache_dir = os.path.join(ROOT, "comp_cache/")
    os.makedirs(cache_dir, exist_ok=True)

    cache_path = os.path.join(cache_dir, f"comp_{comp_obj_id}_cache.json")
    if not os.path.exists(cache_path):  # if the comparison level's filename not in cache

        # We want to convert the comparison data to a list
        comp_obj_data = get_listed_obj_data_wrapper(comp_obj_id)
        if comp_obj_data: # Make sure it's not NoneType (nonexistent level) before subscripting
            comp_obj_list = comp_obj_data[1]

            # Save list as a JSON file in cache
            with open(cache_path, "w") as cache:
                json.dump(comp_obj_list, cache)
        else:
            # Nonexistent comparison level
            return

    else:   # if it does exist in cache
        # Load list back from the JSON file
        print("Loading comparison level data from local cache...")
        with open(cache_path, "r") as cache:
            comp_obj_list = json.load(cache)

    return comp_obj_list


def write_log(id: int, lvl_name: str, exists=True, object_string="", partial_match=False, percentage=100.0):
    """Writes a log from the level ID, level name, an existence boolean (True by default), and, if it's a fully matching level, the object string.\n
    If the level is a full match (object_string fed in), the logs are written to /LOGS/FOUND\n
    If the level hasn't been matched yet (object_string not fed in), the log is written to /LOGS\n
    If the level is a partial match (object_string not fed in), the log is written to /LOGS/PARTIAL_FOUND\n
    partial_match: normally set to False, but update to true if you wish to include match percentage in the partial find's log\n
    percentage: the percentage value of the partial match that should be sent in"""

    if object_string:
        # Full match
        # write both the info and the object data to a unique folder
        directory = os.path.join(ROOT, f"LOGS/FOUND/{id}/")
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, "Info.txt"), "w") as info:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info.write(f"{id} | {lvl_name} | Match percentage: 100%            [ Logged: {timestamp} ]\n")

        with open(os.path.join(directory, "Object_data.txt"), "w") as objs:
            objs.write(object_string)

    elif partial_match:
        # Partial match
        # write only the info to /LOGS/PARTIAL_FOUND/Partial_match_log.txt
        directory = os.path.join(ROOT, "LOGS/PARTIAL_FOUND/")
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, "Partial_match_log.txt"), "a") as partial:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            partial.write(f"{id} | {lvl_name} | Match percentage: {percentage}%            [ Logged: {timestamp} ]\n")

    else:   # write the info to the general log
        directory = os.path.join(ROOT, "LOGS/")
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, "ID_log.txt"), "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"{id} | {lvl_name} | Real: {exists}            [ Logged: {timestamp} ]\n")


def compare(comp_obj_list: list, floor: int, amount: int):
    """Compares comp_obj_list (comparison object list) to levels from a range of IDs, looping through them 1 by 1, attempting to find matches.\n
    comp_obj_list: the list of objects that will be compared with\n
    floor: the lower bound of the ID scan\n
    amount: the amount of IDs to scan"""
    global all_settings

    # Here's the master loop that handles ID ranges for matching
    ceiling = floor + amount
    for id in range(floor, ceiling):
        # nullify these, since they carry over from the previous iteration
        lvl_name = ""
        obj_str = ""

        data = get_level_data(id)   # Note how the search level's data won't be converted to lists! We want the raw string data here.

        if data:    # check for the existence of real data
            lvl_name = data[0]  # current level's name
            obj_str = data[1]  # current level's object data (in raw string form)

            write_log(id, lvl_name, exists=True)    # exists is set to either True/False, since we haven't matched yet
        else:
            write_log(id, lvl_name, exists=False)
            continue    # continue if nonexistent

        # THE OBJECT DATA COMPARISONS TAKE PLACE HERE #
        matched_objs = 0    # track the count of matched objects
        for comp_object in comp_obj_list:
            if comp_object in obj_str:  # obj_str = current level's object string
                matched_objs += 1
        ###############################################

        # After scanning the entire ID...
        if matched_objs != 0:
            # If execution reaches here, there was at least one object that matched up
            if matched_objs >= len(comp_obj_list):
                
                # This is a full match
                print(f"***Full match found! Saving to LOGS > FOUND > {id}...***")
                if all_settings["fullNotifSound"]:
                    play(FULL_NOTIF_PATH)

                write_log(id, lvl_name, object_string=obj_str)
            else:
                match_percent = (matched_objs / len(comp_obj_list)) * 100

                # We must exceed/equal the threshold first to write the partial find to disk
                # Just in case of floating point weirdness, we use math.isclose()
                if math.isclose(match_percent, min_match_threshold, rel_tol=0.001) or match_percent > min_match_threshold:

                    # This is a partial match
                    print("*Partial match found. Saving to LOGS > PARTIAL_FOUND > Partial_match_log.txt...*")
                    if all_settings["partialNotifSound"]:
                        play(PARTIAL_NOTIF_PATH)

                    write_log(id, lvl_name, partial_match=True, percentage=f"{match_percent:.2f}")
        
        # If no object matched, go to the next iteration without doing anything else

    print("Search finished. (See LOGS)")
    time.sleep(5)
    return


def compare_downloaded(comp_obj_list: list):
    """Compares comp_obj_list (comparison object list) to levels from /DOWNLOADED, looping through them 1 by 1, attempting to find matches.\n
    comp_obj_list: the list of objects that will be compared with"""
    global all_settings

    downloaded_dir = os.path.join(ROOT, "DOWNLOADED/")
    os.makedirs(downloaded_dir, exist_ok=True)

    # Here's the master loop that handles downloaded levels for matching
    downloaded_folder_path = Path(downloaded_dir)
    for level_path in downloaded_folder_path.glob("*.json"):
        # nullify these, since they carry over from the previous iteration
        lvl_id = ""
        lvl_name = ""
        lvl_str = ""
        obj_str = ""

        # Load level data dicts from DOWNLOADED/
        downloaded_level_path = os.path.join(downloaded_dir, level_path)
        with open(downloaded_level_path, "r") as downloaded:
            data = json.load(downloaded)
        
        lvl_id = data["levelID"]
        lvl_name = data["levelName"]
        lvl_str = data["levelString"]

        # Convert lvl_str to decoded object string
        obj_str = decode(lvl_str)

        print(f"Checking ID {lvl_id}...")
        write_log(lvl_id, lvl_name, exists=True)

        # THE OBJECT DATA COMPARISONS TAKE PLACE HERE #
        matched_objs = 0    # track the count of matched objects
        for comp_object in comp_obj_list:
            if comp_object in obj_str:  # obj_str = current level's object string
                matched_objs += 1
        ###############################################

        # After scanning the entire ID...
        if matched_objs != 0:
            # If execution reaches here, there was at least one object that matched up
            if matched_objs >= len(comp_obj_list):
                
                # This is a full match
                print(f"***Full match found! Saving to LOGS > FOUND > {lvl_id}...***")
                if all_settings["fullNotifSound"]:
                    play(FULL_NOTIF_PATH)

                write_log(lvl_id, lvl_name, object_string=obj_str)
            else:
                match_percent = (matched_objs / len(comp_obj_list)) * 100

                # We must exceed/equal the threshold first to write the partial find to disk
                # Just in case of floating point weirdness, we use math.isclose()
                if math.isclose(match_percent, min_match_threshold, rel_tol=0.001) or match_percent > min_match_threshold:

                    # This is a partial match
                    print("*Partial match found. Saving to LOGS > PARTIAL_FOUND > Partial_match_log.txt...*")
                    if all_settings["partialNotifSound"]:
                        play(PARTIAL_NOTIF_PATH)

                    write_log(lvl_id, lvl_name, partial_match=True, percentage=f"{match_percent:.2f}")
        
        # If no object matched, go to the next iteration without doing anything else

    print("Search finished. (See LOGS)")
    time.sleep(5)
    return


if __name__ == "__main__":
    try:
        while True: # Master loop
            # Let the user decide which mode they want
            choice = questionary.select(
                "Choose a mode:",
                choices=[
                "Scan levels from server",
                "Scan downloaded levels",
                "Download levels",
                "Settings",
                "-EXIT-"
                ]
            ).ask()
            ##########################################

            if choice == "Scan levels from server":
                print("--- Use CTRL+C to CLOSE at any time ---\n")

                while True: # Validate user input
                    try:
                        comparison_obj_id = int(input("Provide the comparison level ID here >>> "))
                        lower_bound = int(input("Starting level ID >>> "))
                        id_amount = int(input("How many IDs are we searching? >>> "))
                        break
                    except ValueError:
                        print("\nInvalid input. Try again.")
                        continue

                # Confirmation
                user_confirmation = input("You're about to scan levels from the live server. Proceed? (Y/n) >>> ")
                if (
                    user_confirmation.upper().strip() != "Y"
                    and user_confirmation.upper().strip() != "YES"
                ):
                    continue    # Go back to main menu

                # Let the search commence!
                print("\nGetting object data from comparison level ID...")
                comparison_obj_list = get_comp_obj_list(comparison_obj_id)

                if comparison_obj_list: # If there is a list
                    print("\nComparing object data...")
                    compare(comparison_obj_list, lower_bound, id_amount)
                else:   # If there's None
                    print("Comparison level ID is nonexistent. Closing the program...")
                    time.sleep(5)
                    sys.exit(1)

                sys.exit(0)

            elif choice == "Scan downloaded levels":
                print("--- Use CTRL+C to CLOSE at any time ---\n")

                while True: # Validate user input
                    try:
                        comparison_obj_id = int(input("Provide the comparison level ID here >>> "))
                        break
                    except ValueError:
                        print("\nInvalid input. Try again.")
                        continue

                # Confirmation
                user_confirmation = input("You're about to scan all downloaded levels. Proceed? (Y/n) >>> ")
                if (
                    user_confirmation.upper().strip() != "Y"
                    and user_confirmation.upper().strip() != "YES"
                ):
                    continue    # Go back to main menu

                # Let the search commence!
                print("\nGetting object data from comparison level ID...")
                comparison_obj_list = get_comp_obj_list(comparison_obj_id)

                if comparison_obj_list: # If there is a list
                    print("\nComparing object data...")
                    compare_downloaded(comparison_obj_list)
                else:   # If there's None
                    print("Comparison level ID is nonexistent. Closing the program...")
                    time.sleep(5)
                    sys.exit(1)

                sys.exit(0)

            elif choice == "Download levels":
                print("--- Use CTRL+C to CLOSE at any time ---\n")

                while True: # Validate user input
                    try:
                        lower_bound = int(input("Starting level ID >>> "))
                        id_amount = int(input("How many IDs are we downloading? >>> "))
                        break
                    except ValueError:
                        print("\nInvalid input. Try again.")
                        continue

                # Confirmation
                user_confirmation = input("You're about to download levels. Proceed? (Y/n) >>> ")
                if (
                    user_confirmation.upper().strip() != "Y"
                    and user_confirmation.upper().strip() != "YES"
                ):
                    continue    # Go back to main menu

                # Let the downloading commence!
                print("\nDownloading levels from server...")
                download(lower_bound, id_amount)

                sys.exit(0)

            elif choice == "Settings":
                settings_options()

            elif choice == "-EXIT-":
                print("\nClosing the program...")

                time.sleep(2)
                sys.exit(0)

    except KeyboardInterrupt:
        print("\nClosing the program... (See LOGS)")

        time.sleep(5)
        sys.exit(0)