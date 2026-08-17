import os, sys


def get_project_root():
    """Returns the absolute path of the main project root folder. Works seamlessly during development (src/) and in production (dist/)."""
    if getattr(sys, 'frozen', False):
        # Running as a compiled .exe inside the 'dist' folder
        current_dir = os.path.dirname(sys.executable)
    else:
        # Running as raw code inside the 'src' folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
    # Go up exactly one level to step out of 'src' or 'dist'
    return os.path.abspath(os.path.join(current_dir, ".."))