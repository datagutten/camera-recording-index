import os
import re
import subprocess

from django.conf import settings

stream_root = os.path.join(settings.VIDEO_ROOT, 'streaming')


def duration_ffprobe(file):
    if not os.path.exists(file):
        raise FileNotFoundError(file)
    file = os.path.realpath(file)

    process = subprocess.run(
        ['ffprobe', '-show_entries', 'format=duration', '-i', file], capture_output=True)

    if process.returncode != 0:
        raise RuntimeError(process.stderr)

    matches = re.search(rb'duration=([0-9:.]+)', process.stdout)
    duration = int(float(matches.group(1).decode()))
    return duration


def convert_to_hls(file: str):
    if not os.path.exists(file):
        raise FileNotFoundError(file)

    name, ext = os.path.splitext(file)
    name = os.path.basename(name)
    stream_path = os.path.join(stream_root, name)
    os.makedirs(stream_path, exist_ok=True)
    m3u8 = os.path.join(stream_path, name + '.m3u8')
    if not os.path.exists(m3u8):
        cmd = ['ffmpeg', '-i', file, '-c', 'copy', '-hls_time', '10', '-hls_list_size', '0', '-f', 'hls', m3u8]
        process = subprocess.run(cmd)
        process.check_returncode()
    return m3u8


def stream_url(m3u8_file: str):
    stream_path = os.path.relpath(m3u8_file, stream_root)
    stream_path = settings.STREAM_URL + stream_path.replace(os.path.sep, '/')

    return stream_path
