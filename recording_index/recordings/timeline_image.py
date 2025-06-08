import datetime
import math

import pytz
from PIL import Image, ImageDraw
from django.conf import settings

from recordings import models

offsets = {}

tz_local = pytz.timezone(settings.TIME_ZONE)


def build_timeline(camera, start_obj, end_obj):
    timeline = {}
    recordings_objs = models.Recording.objects.filter(camera__name=camera, start_time__gte=start_obj,
                                                      end_time__lte=end_obj).order_by('start_time')

    recording: models.Recording
    for recording in recordings_objs:
        date = recording.start_time.date().isoformat()
        if date not in timeline:
            timeline[date] = {}
        timestamps = range(int(recording.start_time.timestamp()), int(recording.end_time.timestamp()))
        for timestamp in timestamps:
            if timestamp not in timeline[date]:
                timeline[date][timestamp] = [recording.camera.name]
            else:
                timeline[date][timestamp].append(recording.camera.name)

    return timeline


def timeline_image_minutes(camera_arg: models.Camera, start_obj: datetime.datetime, end_obj: datetime.datetime,
                           minute_width=1) -> Image:
    duration = end_obj - start_obj
    seconds_per_pixel = settings.SECONDS_PER_PIXEL
    width = math.ceil(duration.seconds / seconds_per_pixel) * minute_width
    camera_height = settings.CAMERA_HEIGHT

    im = Image.new("RGB", (width, camera_height), 'white')
    draw = ImageDraw.Draw(im)

    recording: models.Recording
    for recording in models.Recording.objects.filter(start_time__gte=start_obj, end_time__lte=end_obj,
                                                     camera__name=camera_arg).order_by(
        'start_time'):
        # minutes since start == X pixel
        duration = recording.duration()
        start_diff = recording.start_time - start_obj.astimezone(tz_local)
        start_x = math.floor(start_diff.total_seconds() / seconds_per_pixel)
        end_x = math.ceil(start_x + (duration.total_seconds() / seconds_per_pixel))
        draw.rectangle([(start_x, 0), (end_x, camera_height)], fill='red')
    return im


def timeline_image(start_obj: datetime.datetime, end_obj: datetime.datetime, second_width=1, camera_arg=None,
                   height=30) -> Image:
    duration = end_obj - start_obj
    width = duration.seconds * second_width
    timeline = build_timeline(camera_arg, start_obj, end_obj)

    im = Image.new("RGB", (width, height), 'white')
    draw = ImageDraw.Draw(im)

    x = 0
    for timestamp in range(int(start_obj.timestamp()), int(end_obj.timestamp())):
        time_obj = datetime.datetime.fromtimestamp(timestamp)
        date = time_obj.date().isoformat()
        if timestamp in timeline[date]:
            for camera in timeline[date][timestamp]:
                if camera_arg and camera_arg != camera:
                    continue

                if camera_arg:
                    offset = 0
                else:
                    offset = offsets[camera]
                draw.line((x, offset, x, offset + height), fill=128 + (offset * 10))
            last_time = time_obj
        x += second_width

    return im
