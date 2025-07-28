from django.core.management.base import BaseCommand
from lead.models import leads
import re
from lead.utils import update_lead_full_address


class Command(BaseCommand):
    help = "Update Full Address in leads"

    def handle(self, *args, **options):

        count = 0

        for lead in leads.objects.all():
            update_lead_full_address(lead)
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated {count} Leads entries.")
        )
