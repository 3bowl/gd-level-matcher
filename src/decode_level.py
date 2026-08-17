import base64
import zlib
import re


def decode(level_str: str) -> str:
    """Takes a level string, isolates the object data, decodes/decompresses it, and returns that as a string"""
    # Step 1: isolate object data
    match = re.search(r"^1:\d+?:2:.*?:3:.*?:4:(.+?):5:", level_str)
    if match:
        encoded_obj_str = match.group(1)

    # Step 2: decode
    decoded_obj_str = base64.urlsafe_b64decode(encoded_obj_str)

    # Step 3: decompress
    try:
        decompressed_obj_str = zlib.decompress(decoded_obj_str, 16 + zlib.MAX_WBITS)
    except zlib.error:  # some levels may use a different compression system
        decompressed_obj_str = zlib.decompress(decoded_obj_str)

    # Step 4: decode bytes into string
    obj_str = decompressed_obj_str.decode("utf-8")

    return obj_str