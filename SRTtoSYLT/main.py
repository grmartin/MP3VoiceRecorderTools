
import argparse
import sys

from video import process_video


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Process an SRT file and encode it as SYLT within a MP3 file."
    )

    # Add positional arguments for the two file inputs
    parser.add_argument(
        "files",
        nargs="*",
        help="Provide exactly two files: one .srt and one .mp3",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Check the number of arguments
    if len(args.files) != 2:
        print("Error: You must provide exactly two files (one .srt and one .mp3).")
        parser.print_help()
        sys.exit(1)

    # Extract file paths
    file_1, file_2 = args.files

    # Validate file extensions
    srt_file = None
    mp3_file = None

    for file in [file_1, file_2]:
        if file.lower().endswith(".srt"):
            srt_file = file
        elif file.lower().endswith(".mp3"):
            mp3_file = file

    if not srt_file or not mp3_file:
        print("Error: You must provide one .srt file and one .mp3 file.")
        parser.print_help()
        sys.exit(1)

    process_video(srt_file, mp3_file)

if __name__ == '__main__':
    main()

