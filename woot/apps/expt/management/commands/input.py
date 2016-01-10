# expt.command: input

# django
from django.core.management.base import BaseCommand, CommandError

# local


# util


spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		pass
