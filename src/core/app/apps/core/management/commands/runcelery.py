import os
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload


def run_celery():
    subprocess.call("pkill celery".split())
    os.environ["WORKER"] = "1"
    subprocess.call("celery -A payments worker -E -l INFO".split())


class Command(BaseCommand):
    help = "Run Celery workers, restarting them on code changes."

    def handle(self, *args, **options):
        print("Starting celery worker with autoreload...")
        autoreload.run_with_reloader(run_celery)
