from root import get_project_root
from fetch_level import fetch
from decode_level import decode
import re
import os


ROOT = get_project_root()


def get_level_data(input_id: str):
    """Takes a level ID, downloads it, gets the data, and returns a tuple in this order:\n
    Level name (0) | Raw object string (1) | Raw level string (2)\n
    If the ID doesn't exist, NoneType is returned instead"""
    # fetch raw level string from RobTop's servers
    lvl_str = fetch(input_id)
    if lvl_str == "-1": # if ID is nonexistent, return NoneType
        return

    # decode the object data
    obj_str = decode(lvl_str)

    # get level name
    match = re.search(r"^1:\d+:2:([\w -]+)", lvl_str)
    if match:
        level_name = match.group(1)

    return level_name, obj_str, lvl_str


if __name__ == "__main__":
    level_id = input("Provide a GD level ID here >>> ")
    data = get_level_data(level_id)
    if data:
        temp_dir = os.path.join(ROOT, "temp_logs/")
        os.makedirs(temp_dir, exist_ok=True)

        with open(os.path.join(temp_dir, "level_data.txt"), "w") as f:
            f.write(f"ID: {level_id}\nName: {data[0]}\nObject string:\n{data[1]}\n")
        print("Level data written to temp_logs > level_data.txt!")
    else:
        print("This level doesn't exist.")