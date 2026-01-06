#!/usr/bin/env python3
"""
Convert SRT subtitles to ASS format and burn-in with ffmpeg.
Based on BizCafe style guide: SUBTITLE_DESIGN_GUIDE.md

Uses BorderStyle=3 to automatically generate an opaque box around text.
"""

import re
import sys
import subprocess
from pathlib import Path


def parse_srt(srt_path):
    """Parse SRT file"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # SRT pattern: index, time, text
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n\d+\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    cues = []
    for idx, start, end, text in matches:
        # Convert to ASS format: , -> .
        start_ass = start.replace(',', '.')
        end_ass = end.replace(',', '.')
        # Convert newlines to ASS format
        text_ass = text.strip().replace('\n', '\\N')

        cues.append({
            'index': int(idx),
            'start': start_ass,
            'end': end_ass,
            'text': text_ass
        })

    return cues


def format_ass_time(time_str):
    """00:00:00.000 -> 0:00:00.00 (ASS format)"""
    parts = time_str.replace('.', ':').split(':')
    h, m, s, ms = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    cs = ms // 10  # centiseconds
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_ass(cues, video_width, video_height, output_path):
    """
    Generate ASS file (BizCafe style)
    - BorderStyle=3: Opaque box that automatically wraps text
    - Outline: Left/right padding
    - Shadow: Top/bottom padding
    - Alignment=2: Bottom center alignment
    """

    # Base settings (for 1440x810)
    base_width = 1440
    base_height = 810

    # Calculate scale
    scale_x = video_width / base_width
    scale_y = video_height / base_height
    scale = min(scale_x, scale_y)

    # Style parameters
    font_size = int(28 * scale)
    margin_v = int(50 * scale)
    outline = int(12 * scale)  # Left/right padding
    shadow = int(8 * scale)    # Top/bottom padding

    # ASS header
    # BorderStyle=3: Outline and Shadow act as box padding
    # OutlineColour: Box color (opaque black)
    # BackColour: Box background color (opaque black)
    ass_header = f"""[Script Info]
Title: BizCafe Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK KR,{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,{outline},{shadow},2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    for cue in cues:
        start = format_ass_time(cue['start'])
        end = format_ass_time(cue['end'])
        text = cue['text']

        # Single event for text + box (BorderStyle=3 handles it automatically)
        event = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
        events.append(event)

    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        f.write('\n'.join(events))

    print(f"ASS file generated: {output_path}")
    print(f"  - Resolution: {video_width}x{video_height}")
    print(f"  - Subtitle count: {len(cues)}")
    print(f"  - Font size: {font_size}px")
    print(f"  - Box padding: {outline}px (L/R), {shadow}px (T/B)")
    print(f"  - Bottom margin: {margin_v}px")

    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python burnin.py <video_path> <srt_path> [output_path]")
        sys.exit(1)

    video_path = sys.argv[1]
    srt_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None

    # Check file existence
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    if not Path(srt_path).exists():
        print(f"Error: Subtitle file not found: {srt_path}")
        sys.exit(1)

    print(f"\n=== Starting Subtitle Burn-in ===")
    print(f"Input video: {video_path}")
    print(f"Input subtitle: {srt_path}")

    # Get video resolution
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path],
            capture_output=True, text=True, check=True
        )
        width, height = map(int, result.stdout.strip().split(','))
    except Exception as e:
        print(f"Error: Cannot get video info: {e}")
        sys.exit(1)

    print(f"Video resolution: {width}x{height}")

    # Generate ASS file (save to videos/subtitles/ass/ directory)
    srt_file = Path(srt_path)
    # Find subtitles directory: srt is in subtitles/raw/ or subtitles/corrected/
    subtitles_dir = srt_file.parent.parent  # subtitles/
    ass_dir = subtitles_dir / "ass"
    ass_dir.mkdir(exist_ok=True)
    ass_path = str(ass_dir / srt_file.with_suffix('.ass').name)
    print(f"\n=== Converting SRT to ASS ===")

    try:
        cues = parse_srt(srt_path)
        generate_ass(cues, width, height, ass_path)
    except Exception as e:
        print(f"Error: ASS file generation failed: {e}")
        sys.exit(1)

    # Set output path (save to videos/burnin_output/ directory)
    if not output_path:
        video_file = Path(video_path)
        video_stem = video_file.stem
        # Find videos directory: video is in videos/raw/ or videos/cropped/
        videos_dir = video_file.parent.parent  # videos/
        output_dir = videos_dir / "burnin_output"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{video_stem}_burnin.mp4")

    print(f"\n=== Starting ffmpeg Burn-in ===")
    print(f"Output path: {output_path}")

    # Execute ffmpeg command
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f"ass={ass_path}",
            '-c:a', 'copy',
            '-y',
            output_path
        ]

        subprocess.run(cmd, check=True)

        print(f"\n=== Complete ===")
        print(f"Output file: {output_path}")

        # Check file size
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"File size: {size_mb:.1f} MB")

    except subprocess.CalledProcessError as e:
        print(f"Error: ffmpeg execution failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
