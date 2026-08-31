import re
from datetime import datetime, timedelta
from root import get_project_root
import sys
import os
import json


def list_of_str_to_tuples(obj_list: list) -> list:
    """Turns a list of stringed object data into a list of tupled object data."""
    new_list_of_tupled_obj = []
    for obj in obj_list:
        match = re.search(r"^1,(\d+?),2,(\d+?),3,(\d+?)$", obj)
        if match:
            obj_id = int(match.group(1))
            x_coor = int(match.group(2))
            y_coor = int(match.group(3))

            tupled_obj = (obj_id, x_coor, y_coor)
            new_list_of_tupled_obj.append(tupled_obj)

    return new_list_of_tupled_obj


def exit_program():
    """Exits the program while updating the cooldown_time.json data."""
    ROOT = get_project_root()
    
    # Get the cooldown_time.json path
    directory = os.path.join(ROOT, "request_cooldown")
    os.makedirs(directory, exist_ok=True)
    cooldown_path = os.path.join(directory, "cooldown_time.json")

    # Manage the long-term request cooldown timer. Exiting should allow the wait time to decrement
    with open(cooldown_path, "r") as cool:
        cooldown_data = json.load(cool)

    cooldown_data["cooldownDateDelta"] = (datetime.now() + timedelta(seconds=cooldown_data["cooldownTimerValue"])).isoformat()

    with open(cooldown_path, "w") as cool:
        json.dump(cooldown_data, cool)

    sys.exit()