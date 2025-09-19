## To delete all the addresses in the table before loading the updated/new file.
## Run from root.
## python manage.py delete_all_addresses

from django.core.management.base import BaseCommand
from address_lookup.models import Address

class Command(BaseCommand):
    help = 'Deletes all records in the Address table'

    def handle(self, *args, **kwargs):
        # Delete all records in the Address model
        deleted_count, _ = Address.objects.all().delete()

        # Print the result
        if deleted_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} address records.'))
        else:
            self.stdout.write(self.style.WARNING('No address records found to delete.'))
