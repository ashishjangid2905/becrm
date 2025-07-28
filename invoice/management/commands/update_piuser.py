from django.core.management.base import BaseCommand
from invoice.models import proforma
from teams.models import User

class Command(BaseCommand):
    help = "updates PI's user_name, email and contact for all existing proforma records where these are null"

    def handle(self, *args, **options):
        to_update = []

        queryset = proforma.objects.filter(user_name__isnull=True, user_email__isnull=True, user_contact__isnull=True)

        for pi in queryset:
            try:
                user = User.objects.get(pk=pi.user_id)
                pi.user_name = f'{user.first_name} {user.last_name}' if user.last_name else user.first_name
                pi.user_email = user.email
                pi.user_contact = getattr(user.profile, 'phone', None)
                to_update.append(pi)
            except User.DoesNotExist:
                self.stderr.write(f"User with ID {pi.user_id} does not exist.")
            except Exception as e:
                self.stderr.write(f"Error processing PI {pi.id}: {e}")

        if to_update:
            proforma.objects.bulk_update(to_update, ["user_name", "user_email", "user_contact"])
            self.stdout.write(self.style.SUCCESS(f"Successfully updated {len(to_update)} proforma records."))
        else:
            self.stdout.write("No proforma records needed updating.")
