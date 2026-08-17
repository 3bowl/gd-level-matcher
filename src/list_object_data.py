import re


def list_object_data(obj_data: str) -> list:
    """Organizes decoded object strings into a list"""
    split_obj_data = obj_data.split(";")[1:-1]    # split at ;, cut off header index and last empty index

    # isolate only the first three keys (1,x,2,y,3,z) for each object
    list_obj_data = []
    for obj in split_obj_data:
        match = re.search(r"(1,\d+,2,\d+,3,\d+)", obj)
        if match:
            list_obj_data.append(match.group(1))

    return list_obj_data


if __name__ == "__main__":
    input_data = input("Supply a decoded object string >>> ")
    output_data = list_object_data(input_data)
    print()
    print(output_data)