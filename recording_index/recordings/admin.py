from django.contrib import admin

from recordings import models


@admin.register(models.Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ["name", "path", "timezone"]


@admin.register(models.Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_filter = ["camera"]
    list_display = ["camera", "start_time", "end_time"]
