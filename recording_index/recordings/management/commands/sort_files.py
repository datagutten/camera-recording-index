import os.path

from django.core.management import BaseCommand
from recordings import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("camera", nargs="?", type=str)

    def handle(self, *args, **options):
        camera_obj: models.Camera = models.Camera.objects.get(name=options['camera'])

        for recording in camera_obj.recordings.all():
            if os.path.dirname(recording.file) != camera_obj.path:
                continue  # File is not at root level
            date_path = camera_obj.path + "/" + recording.start_time.strftime("%Y/%m/%d")
            os.makedirs(date_path, exist_ok=True)
            date_file = '%s/%s' % (date_path, os.path.basename(recording.file))
            os.rename(recording.file, date_file)
            recording.file = date_file
            recording.save()
            if os.path.exists(recording.file + '.duration'):
                os.unlink(recording.file + '.duration')
