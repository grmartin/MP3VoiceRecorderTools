import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# noinspection PyProtectedMember
from mutagen.id3 import ID3, ID3NoHeaderError, TXXX

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

CTIME_KEY = "grm:CreationDate"
MTIME_KEY = "grm:ModificationDate"

def get_time_as_utc(local_timestamp: datetime) -> datetime:
    return local_timestamp.astimezone(timezone.utc)

# The desc and text fields on `TXXX` are dynamically bound.
# noinspection PyUnresolvedReferences
def add_custom_tags_if_not_set(file_path):
    creation_time = get_time_as_utc(datetime.fromtimestamp(os.path.getctime(file_path)))
    modification_time = get_time_as_utc(datetime.fromtimestamp(os.path.getmtime(file_path)))

    creation_date = creation_time.strftime(DATE_TIME_FORMAT)
    modification_date = modification_time.strftime(DATE_TIME_FORMAT)

    try:
        audio = ID3(file_path)
    except ID3NoHeaderError:
        audio = ID3()

    existing_creation_date = None
    existing_modification_date = None

    for frame in audio.values():
        if isinstance(frame, TXXX):
            if frame.desc == CTIME_KEY:
                existing_creation_date = frame.text[0]
            elif frame.desc == MTIME_KEY:
                existing_modification_date = frame.text[0]

    if not existing_creation_date:
        audio.add(TXXX(desc=CTIME_KEY, text=[creation_date]))
        print(f"Set '{CTIME_KEY}' to {creation_date}")
    else:
        print(f"'{CTIME_KEY}' already set to {existing_creation_date}, skipping.")

    if not existing_modification_date:
        audio.add(TXXX(desc=MTIME_KEY, text=[modification_date]))
        print(f"Set '{MTIME_KEY}' to {modification_date}")
    else:
        print(f"'{MTIME_KEY}' already set to {existing_modification_date}, skipping.")

    audio.save(file_path)
    print(f"Finished processing {file_path}")

def process_mp3(path):
    add_custom_tags_if_not_set(path)

def process_files_in_directory(root_path):
    """
    Recursively loop through all files in the root directory and process MP3 files.
    """
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            # Check if the file is an MP3
            if filename.lower().endswith(".mp3"):
                full_path = os.path.join(dirpath, filename)
                process_mp3(os.path.abspath(str(full_path)))


def identify_and_process_paths(paths):
    """
    Identify paths as MP3 files or directories/drives, and process them accordingly.
    """
    for path in paths:
        path_obj = Path(path)

        if path_obj.exists():  # Check if the path exists
            if path_obj.is_file() and path_obj.suffix.lower() == '.mp3':  # Check if it's an MP3 file
                process_mp3(str(path_obj))
            elif path_obj.is_dir():  # Check if it's a directory
                process_files_in_directory(str(path_obj))
            elif os.name == 'nt' and os.path.splitdrive(path)[1] == "\\":  # Check if it's a drive (Windows-specific)
                process_files_in_directory(str(path_obj))
            else:
                print(f"Ignored: {path} (not an MP3 file, directory, or drive)")
        else:
            print(f"Ignored: {path} (path does not exist)")

# Example usage
if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_paths = sys.argv[1:]  # Get paths from command-line arguments
        identify_and_process_paths(input_paths)
    else:
        print("Please drag and drop mp3 files/directories onto this script or pass them as arguments.")
    input()