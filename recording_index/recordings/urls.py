from django.urls import path
from recordings import views

urlpatterns = [
    path('', views.timeline),
    path('recordings/<str:date>', views.timeline),
    path('timeline/<str:camera>/<str:date>/', views.timeline_image),
    path('recording/<str:camera>/<str:timestamp>', views.recording),
    path('stream_url/<int:recording_id>', views.stream_url, name='stream_url'),
    path('load/<str:date>', views.load, name='load'),

]
