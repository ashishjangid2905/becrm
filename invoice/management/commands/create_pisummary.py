from django.core.management.base import BaseCommand
from invoice.models import proforma
from invoice.custom_utils import update_or_create_summery


class Command(BaseCommand):
    help = "Creates or updates PiSummery for all existing proforma records"

    def handle(self, *args, **options):
        count = 0

        for pi in proforma.objects.filter(summary__isnull=True):
            update_or_create_summery(pi)
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} PiSummery entries.'))