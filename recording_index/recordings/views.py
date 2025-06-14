import datetime
from io import BytesIO
from typing import Union

import django
import pytz
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404

from recordings import models
from recordings import timeline_image as image
from recordings import video
from recordings.recording_utils import load_recordings

tz_local = pytz.timezone(settings.TIME_ZONE)


def load(request, date: str):
    date_obj = datetime.date.fromisoformat(date)
    load_recordings(date_obj)
    return HttpResponse('Loaded recordings')


def timeline(request):
    today = datetime.date.today()
    if request.GET.get('date'):
        date = datetime.date.fromisoformat(request.GET['date'])
    else:
        date = today

    start_obj = datetime.datetime.fromisoformat(date.isoformat() + 'T00:00:00').astimezone(tz_local)
    date_prev = date - datetime.timedelta(days=1)
    date_next = date + datetime.timedelta(days=1)
    cameras = models.Camera.objects.all()

    return render(request, 'recordings/timeline.html',
                  {
                      'cameras': cameras,
                      'date': date,
                      'date_prev': date_prev,
                      'date_next': date_next,
                      'today': today,
                      'config': {
                          'camera_height': settings.CAMERA_HEIGHT,
                          'stream_url': settings.STREAM_URL,
                          'seconds_per_pixel': settings.SECONDS_PER_PIXEL,
                          'start': start_obj.isoformat(),
                          'start_timestamp': start_obj.timestamp(),
                      }})


def timeline_image(request, camera, date):
    start_obj = datetime.datetime.fromisoformat(date + 'T00:00:00').astimezone(tz_local)
    end_obj = datetime.datetime.fromisoformat(date + 'T23:59:59').astimezone(tz_local)
    now = datetime.datetime.now().astimezone(tz_local)
    if end_obj > now:
        end_obj = now

    timeline_im = image.timeline_image_minutes(camera, start_obj, end_obj)
    if not timeline_im:
        return HttpResponse()

    img_io = BytesIO()
    timeline_im.save(img_io, 'PNG')
    img_io.seek(0)

    return HttpResponse(img_io, content_type='image/png')


def recording(request, camera: str, timestamp: str):
    time_obj = datetime.datetime.fromisoformat(timestamp)
    camera_obj: models.Camera = get_object_or_404(models.Camera, name=camera)
    recording_obj = camera_obj.get_closest_recording(time_obj)
    if not recording_obj:
        return django.http.HttpResponseNotFound('No recording found')

    try:
        m3u8 = video.convert_to_hls(recording_obj.file)
    except FileNotFoundError as e:
        return django.http.HttpResponseNotFound(str(e))
    except RuntimeError as e:
        return django.http.HttpResponseServerError(str(e))

    m3u8_url = video.stream_url(m3u8)

    return JsonResponse({'id': recording_obj.id,
                         'camera': recording_obj.camera.name,
                         'start_time': recording_obj.start_time.isoformat(),
                         'end_time': recording_obj.end_time.isoformat(),
                         'file': recording_obj.file,
                         'm3u8_url': m3u8_url})


def stream_url(request, recording_id: int):
    recording_obj = get_object_or_404(models.Recording, id=recording_id)
    m3u8 = video.convert_to_hls(recording_obj.file)
    return HttpResponse(video.stream_url(m3u8), content_type='text/plain')
