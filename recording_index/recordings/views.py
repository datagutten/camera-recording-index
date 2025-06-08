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

tz_local = pytz.timezone(settings.TIME_ZONE)


def timeline(request):
    if request.GET.get('date'):
        date = request.GET['date']
    else:
        date = datetime.date.today().isoformat()

    start_obj = datetime.datetime.fromisoformat(date + 'T00:00:00').astimezone(tz_local)
    cameras = models.Camera.objects.all()

    return render(request, 'recordings/timeline.html',
                  {
                      'cameras': cameras,
                      'date': date,
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


# https://stackoverflow.com/a/63437073/2630074
def get_closest(
        *,
        qs: django.db.models.QuerySet,
        datetime_field: str,
        target_datetime: Union[datetime.datetime, datetime.date],
) -> django.db.models.Model:
    greater = qs.filter(**{
        f'{datetime_field}__gte': target_datetime,
    }).order_by(datetime_field).first()

    less = qs.filter(**{
        f'{datetime_field}__lte': target_datetime,
    }).order_by(f'-{datetime_field}').first()

    if greater and less:
        greater_datetime = getattr(greater, datetime_field)
        less_datetime = getattr(less, datetime_field)
        return greater if abs(greater_datetime - target_datetime) < abs(less_datetime - target_datetime) else less
    else:
        return greater or less


def recording(request, camera: str, timestamp: str):
    time_obj = datetime.datetime.fromisoformat(timestamp)
    recording_obj = get_closest(qs=models.Recording.objects.filter(camera__name=camera), datetime_field='start_time',
                                target_datetime=time_obj)
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
