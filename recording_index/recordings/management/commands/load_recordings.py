import datetime

import dateutil
import pytz
from django.conf import settings
from django.core.management import BaseCommand
from django.db import IntegrityError

import recordings.recording_utils as camera_recordings
from recordings import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("date", nargs="?", type=str)

    def handle(self, *args, **options):
        if options['date']:
            date = dateutil.parser.parse(options['date']).date()
        else:
            date = datetime.date.today()
        local_tz = pytz.timezone(settings.TIME_ZONE)

        for camera in models.Camera.objects.all():
            recordings = camera_recordings.find_videos(camera.path, date)
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
