from get_level_data import get_level_data
from list_object_data import list_object_data
from notif_player import play
from root import get_project_root
from datetime import datetime
import sys
import os
import json
import time


# NOTE: bundle with this command (activate a venv first):
# pyinstaller --clean --onefile --hidden-import=_cffi_backend src/Match.py

def get_listed_obj_data_wrapper(id: int):
    """Takes a level ID and returns a tuple in this order:\n
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
                play(FULL_NOTIF_PATH)

                write_log(id, lvl_name, object_string=obj_str)
            else:
                match_percent = (matched_objs / len(comp_obj_list)) * 100
                if match_percent >= MIN_MATCH_THRESHOLD:    # We must exceed/equal the threshold first to write the partial find to disk

                    # This is a partial match
                    print("*Partial match found. Saving to LOGS > PARTIAL_FOUND > Partial_match_log.txt...*")
                    play(PARTIAL_NOTIF_PATH)

                    write_log(id, lvl_name, partial_match=True, percentage=f"{match_percent:.2f}")
        
        # If no object matched, go to the next iteration without doing anything else

    print("Search finished.")
    time.sleep(5)
    return


if __name__ == "__main__":
    ROOT = get_project_root()
    FULL_NOTIF_PATH = os.path.join(ROOT, "notif_sounds/Full_match.ogg")
    PARTIAL_NOTIF_PATH = os.path.join(ROOT, "notif_sounds/Partial_match.ogg")

    # The match-percentage threshold that must be exceeded for a level to be considered a partial match
    MIN_MATCH_THRESHOLD = 50.0
    
    try:
        comparison_obj_id = int(input("Provide the comparison level ID here >>> "))
        lower_bound = int(input("Starting level ID >>> "))
        id_amount = int(input("How many IDs are we searching? >>> "))

        # Let the search commence!
        print("\n--- Use CTRL+C to STOP scanning ---")
        print("\nGetting object data from comparison level ID...")

        # Access the cached comparison level download if available, otherwise make one for next time
        cache_dir = os.path.join(ROOT, "comp_cache/")
        os.makedirs(cache_dir, exist_ok=True)

        cache_path = os.path.join(cache_dir, f"comp_{comparison_obj_id}_cache.json")
        if not os.path.exists(cache_path):  # if the comparison level's filename not in cache

            # We want to convert the comparison data to a list
            comparison_obj_data = get_listed_obj_data_wrapper(comparison_obj_id)
            if comparison_obj_data: # make sure it's not NoneType (nonexistent level) before subscripting
                comparison_obj_list = comparison_obj_data[1]
                # Save list as a JSON file in cache
                with open(cache_path, "w") as cache:
                    json.dump(comparison_obj_list, cache)
            else:
                print("Comparison level ID is nonexistent. Closing the program...")
                time.sleep(5)
                sys.exit(1)

        else:   # if it does exist in cache
            # Load list back from the JSON file
            print("Loading comparison level data from local cache...")
            with open(cache_path, "r") as cache:
                comparison_obj_list = json.load(cache)

        print("\nComparing object data...")
        compare(comparison_obj_list, lower_bound, id_amount)
    except KeyboardInterrupt:
        print("\nClosing the program... (See LOGS > ID_log.txt)")

        time.sleep(5)
        sys.exit(0)