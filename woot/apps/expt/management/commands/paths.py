# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# util

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		print('DATA ROOT: {}'.format(settings.DATA_ROOT))
