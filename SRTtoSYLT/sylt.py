import os
import shutil
import sys
from typing import List

import srt
from mutagen.id3 import ID3, SYLT, Encoding
from srt import Subtitle

# This didn't work because nearly no one supports SYLT yet... darn.

def duplicate_mp3(mp3_path: str) -> str:
    directory, filename = os.path.split(mp3_path)
    base, ext = os.path.splitext(filename)

    if ext.lower() == ".mp3":
        new_filename = f"{base}.SYLT{ext}"
        new_path = os.path.join(directory, new_filename)

        try:
            shutil.copy(mp3_path, new_path)
            return new_path
        except FileNotFoundError:
            print(f"Error: The file '{mp3_path}' does not exist.")
        except PermissionError:
            print(f"Error: Permission denied while accessing '{mp3_path}' or '{new_path}'.")
    else:
        raise ValueError("The file extension does not match 'ABC' case-insensitively.")
    sys.exit(1)

def process_sylt(srt_path: str, orig_mp3_path: str):
    mp3_path = duplicate_mp3(orig_mp3_path)

    with open(srt_path, "r", encoding="utf-8") as srt_file:
        srt_content = srt_file.read()

    try:
        srt_data: List[Subtitle] = srt.parse(srt_content, ignore_errors=False)
        # [Subtitle(
        #     index=raw_index,
        #     start=srt_timestamp_to_timedelta(raw_start),
        #     end=srt_timestamp_to_timedelta(raw_end),
        #     content=content,
        #     proprietary=proprietary,
        # ) ...]
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # https://id3.org/id3v2.3.0#Synchronised_lyrics.2Ftext
    tag = ID3(mp3_path)
    lyrics = list(map(lambda t: (t.content, int(t.start.total_seconds() * 1000)), srt_data))
    # I dont trust these values.
    tag.setall("SYLT", [SYLT(encoding=Encoding.UTF8, lang='eng', format=2, type=1, text=lyrics)])
    tag.save(v2_version=3)