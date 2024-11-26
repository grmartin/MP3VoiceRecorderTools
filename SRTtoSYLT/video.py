
import os
import shutil
import sys
import tempfile
from typing import List, Tuple

import srt
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from moviepy import AudioFileClip, ImageClip, TextClip, CompositeVideoClip
from srt import Subtitle
import numpy as np

MAX_WIDTH = 480
XY_PAD = 50
TARGET_FONT_SIZE = 14

def find_font_by_name(font_name: str, default = False) -> str:
    font_prop: FontProperties = font_manager.FontProperties(family=font_name)
    font_path = font_manager.findfont(font_prop, fallback_to_default=default)
    return font_path

def calculate_line_breaks(subtitle: Subtitle, max_width: int, font: ImageFont.FreeTypeFont) -> (Subtitle, str, int):
    text = subtitle.content

    # Create a dummy image and drawing context
    image = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(image)

    # Split the text into words
    words = text.split()
    lines = []
    current_line = []
    total_height = 0

    # Measure height for a single line of text
    _, line_height = draw.textbbox((0, 0), "A", font=font)[2:]  # Height of one line of text

    for word in words:
        # Test the width of the current line with the new word added
        test_line = ' '.join(current_line + [word])
        width, _ = draw.textbbox((0, 0), test_line, font=font)[2:]  # Measure text width

        if width > max_width and current_line:
            # If the line exceeds the max width, finalize the current line
            lines.append(' '.join(current_line))
            total_height += line_height  # Add height for this completed line
            current_line = [word]  # Start a new line with the current word
        else:
            current_line.append(word)

    # Add any remaining words as the last line
    if current_line:
        lines.append(' '.join(current_line))
        total_height += line_height  # Add height for the last line

    # Join lines into a single string with newlines
    formatted_text = '\n'.join(lines)

    return subtitle, formatted_text, total_height

def gen_bg_image(height: int):
    size = (MAX_WIDTH+XY_PAD, height+XY_PAD)  # w,h
    color = (0, 0, 0)  # r,g,b

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_file_path = temp_file.name

    def _cleanup():
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    try:
        black_image = Image.new('RGB', size, color)
        black_image.save(temp_file_path)
    except Exception as e:
        print(f"gen_bg_image: Error: {e}")
        _cleanup()
        sys.exit(1)

    return temp_file_path, _cleanup

def create_text_image(text, font_path, font_size, image_size):
    """
    Create a transparent image with sharp text using Pillow.
    """
    # Create a transparent RGBA image
    img = Image.new("RGBA", image_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load the font
    font = ImageFont.truetype(font_path, font_size)

    # Calculate text bounding box for centering
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    text_x = (image_size[0] - text_width) // 2
    text_y = (image_size[1] - text_height) // 2

    # Draw the text onto the image
    draw.multiline_text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255), align="center")

    return img

def create_video_with_subtitles(mp3_file, srt_file, new_filename):
    max_height = MAX_WIDTH

    ftfont = ImageFont.truetype(find_font_by_name("Arial", True), TARGET_FONT_SIZE+2)

    audio = AudioFileClip(mp3_file)

    with open(srt_file, "r", encoding="utf-8") as f:
        srt_content = f.read()

    subtitles_with_sizes: List[Tuple[Subtitle, str, int]] = list(map(lambda l: calculate_line_breaks(l, int(MAX_WIDTH/2)-XY_PAD, ftfont), list(srt.parse(srt_content))))
    subtitles : List[Tuple[Subtitle, str]]= []

    for subtitle_tup in subtitles_with_sizes:
        if subtitle_tup[2] > max_height:
            max_height = subtitle_tup[2]
        subtitles.append((subtitle_tup[0], subtitle_tup[1]))

    del subtitles_with_sizes

    image_file, cleanup_image = gen_bg_image(max_height)

    try:
        image = ImageClip(image_file, duration=audio.duration)

        video_with_audio = image.with_audio(audio)

        subtitle_clips = []

        for (subtitle, content) in subtitles:
            start_time = subtitle.start.total_seconds()
            end_time = subtitle.end.total_seconds()

            subtitle_img = np.array(create_text_image(
                content,
                font_path=ftfont.path,
                font_size=ftfont.size*2,
                image_size=(image.size[0], image.size[1])  # Subtitle area height is ~1/6th of video height
            ))

            # Convert Pillow image to MoviePy ImageClip
            subtitle_clip = (
                ImageClip(subtitle_img)
                .with_duration(end_time - start_time)
                .with_start(start_time)
                .with_position("center")  # Position at center of the frame
            )

            subtitle_clips.append(subtitle_clip)

        final_video = CompositeVideoClip([video_with_audio] + subtitle_clips)

        shutil.copy(srt_file, f"{new_filename}.srt")
        final_video.write_videofile(f"{new_filename}.mp4", fps=24)

        #
        #
        # (
        #     ffmpeg
        #     .output(ffmpeg.input(f"{new_filename}.mp4"), ffmpeg.input(srt_file),
        #         f"{new_filename}.tmp.mp4",
        #         c="copy",  # Copy video and audio streams without re-encoding
        #         c_s="mov_text",  # Use mov_text codec for MP4-compatible subtitles
        #         extra_args=['-map', '0', '-map', '1'],
        #         **{
        #             "metadata:s:s:0": f"language=eng"  # Set subtitle language metadata
        #         }
        #     )
        #     .run(overwrite_output=True)
        # )# Overwrite if temp file exists
        # os.replace(f"{new_filename}.tmp.mp4", f"{new_filename}.mp4")

    except Exception as e:
        print(f"create_video_with_subtitles: Error: {e}")
        cleanup_image()
        sys.exit(1)

def list_available_fonts():
    font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')

    fonts = []
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path)
            fonts.append((font.getname(), font_path))
        except Exception as e:
            # Skip fonts that cannot be loaded
            continue

    return fonts

def process_video(srt_path:str, mp3_path:str):
    ###### Debugging
    # # List all available fonts
    # available_fonts = list_available_fonts()
    #
    # # Print the results
    # for font_name, font_path in available_fonts:
    #     print(f"Font Name: {font_name[0]} {font_name[1]}, Path: {font_path}")
    #

    directory, filename = os.path.split(mp3_path)
    base, ext = os.path.splitext(filename)

    new_filename = os.path.join(directory, f"{base}_OST")

    create_video_with_subtitles(mp3_path, srt_path, new_filename)
