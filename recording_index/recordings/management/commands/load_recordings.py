import datetime

import dateutil
from django.core.management import BaseCommand

from recordings.recording_utils import load_recordings


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("date", nargs="?", type=str)

    def handle(self, *args, **options):
        if options['date']:
            date = dateutil.parser.parse(options['date']).date()
        else:
            date = datetime.date.today()

        load_recordings(date)
