import datetime
import os

from django.db import models
from recordings import recording_utils


class Camera(models.Model):
    name = models.CharField(max_length=255)
    path = models.FilePathField(path=os.getenv('VIDEO_ROOT'), allow_files=False, allow_folders=True)
    timezone = models.CharField(max_length=255, default=os.getenv('TZ'))

    def __str__(self):
        return self.name

    def recording_files(self, date: datetime.date = None):
        return recording_utils.find_videos(self.path, date)

    # https://stackoverflow.com/a/63437073/2630074
    def get_closest_recording(self, target_datetime: datetime.datetime) -> 'Recording':
        greater = self.recordings.filter(start_time__gte=target_datetime).first()
        less = self.recordings.filter(start_time__lte=target_datetime).order_by('-start_time').first()

        if greater and less:
            greater_datetime = getattr(greater, 'start_time')
            less_datetime = getattr(less, 'start_time')
            return greater if abs(greater_datetime - target_datetime) < abs(less_datetime - target_datetime) else less
        else:
            return greater or less


class Recording(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='recordings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    file = models.FilePathField(os.getenv('VIDEO_ROOT'), allow_files=True, allow_folders=False, unique=True)
    mtime = models.DateTimeField(null=True)

    def duration(self) -> datetime.timedelta:
        return self.end_time - self.start_time

    def next(self):
        return self.camera.recordings.filter(start_time__gte=self.end_time).first()

    class Meta:
        unique_together = ("camera", "start_time")
        ordering = ['start_time']

    def __str__(self):
        return '%s - %s' % (self.camera, self.start_time)
