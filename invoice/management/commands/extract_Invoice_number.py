from django.core.management.base import BaseCommand
from invoice.models import convertedPI


def extract_invoice_number(formatted_no):
    try:
        number = formatted_no.split("-")[1].split("/")[0]
        return int(number.lstrip("0") or "0")
    except (IndexError, AttributeError, ValueError):
        return None


class Command(BaseCommand):
    help = "Updates Invoice Number for all existing proforma records"

    def handle(self, *args, **options):
        count = 0

        for pi in convertedPI.objects.filter(formatted_invoice__isnull=False, invoice_number__isnull=True):
            pi.invoice_number = extract_invoice_number(pi.formatted_invoice)
            pi.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated: Invoice Number for entries {count}.'))