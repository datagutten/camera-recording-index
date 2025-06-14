import datetime
import os
import re
from typing import List

import dateutil
import pytz
from django.conf import settings
from django.db import IntegrityError

from . import models
from .video import duration_ffprobe

folder = os.path.dirname(os.path.realpath(__file__))

patterns = {
    'reolink': r'(\w+)_\d+_((\d{8})(\d{6}))\.(\w+)$',
    'dlink': r'(\w+)_((\d{8})_(\d{6}))\.(\w+)$',
}
video_extensions = ['mp4']

for vendor, pattern in patterns.items():
    patterns[vendor] = re.compile(pattern)


class RecordingFile:
    camera: str = None
    start: datetime.datetime = None
    end: datetime.datetime = None
    duration: int = None
    file: str

    def __init__(self, file: str):
        if not os.path.exists(file):
            raise FileNotFoundError(file)

        self.file = file
        data = self.parse_file_name(file)
        self.camera = data['camera']
        self.start = dateutil.parser.parse('%s %s' % (data['date'], data['time']))

    @staticmethod
    def parse_file_name(file: str):
        for vendor, pattern in patterns.items():
            matches = pattern.search(file)
            if matches:
                return {
                    'camera': matches.group(1),
                    'date': matches.group(3),
                    'time': matches.group(4),
                    'datetime': matches.group(2),
                }
        raise RuntimeError("Unable to parse file %s" % file)

    def _duration(self):
        duration_file = self.file + '.duration'
        if not os.path.exists(duration_file):
            duration = duration_ffprobe(self.file)
            with open(duration_file, 'w') as fp:
                fp.write(str(duration))
            return duration
        else:
            try:
                with open(duration_file, 'r') as fp:
                    return int(fp.read())
            except ValueError:
                os.unlink(duration_file)
                return self._duration()

    def get_duration(self):
        self.duration = self._duration()
        self.end = self.start + datetime.timedelta(seconds=self.duration)
        return self.duration

    def mtime(self):
        mtimestamp = os.path.getmtime(self.file)
        mtime = datetime.datetime.fromtimestamp(mtimestamp)
        return mtime


def load_recordings(date: datetime.date):
    local_tz = pytz.timezone(settings.TIME_ZONE)

    for camera in models.Camera.objects.all():
        recordings = find_videos(camera.path, date)
        tz = pytz.timezone(camera.timezone)

        for recording in recordings:
            if recording.start.date() < date:
                continue

            recording_db = models.Recording(
                camera=camera,
                start_time=recording.start.astimezone(tz),
                end_time=recording.end.astimezone(tz),
                mtime=recording.mtime().astimezone(local_tz),
                file=recording.file.replace('\\', '/'),
            )

            try:
                recording_db.save()
                print('Loaded %s' % recording_db)
            except IntegrityError:
                continue
            pass


def find_videos(base_folder: str = None, date: datetime.date = None) -> List[RecordingFile]:
    print('Scanning videos in %s' % base_folder)
    videos = []
    for entry in os.scandir(base_folder):
        if entry.is_file() and os.path.getsize(entry.path) == 0:
            os.unlink(entry.path)
            continue
        if entry.is_dir():
            videos += find_videos(entry.path, date)
        else:
            # print(entry.name)
            name, ext = os.path.splitext(entry.name.lower())
            if ext[1:] not in video_extensions:
                continue

            try:
                video = RecordingFile(entry.path)
                if date and video.start.date() != date:
                    continue
                video.get_duration()
                videos.append(video)
            except RuntimeError as e:
                print(e)
                continue
    return videos
