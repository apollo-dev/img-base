# expt.command: list

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment

# util

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		experiment = Experiment.objects.get()

		composite = experiment.composites.get()

		print(experiment.cells.count())
		for cell in experiment.cells.all():
			print(cell.cell_instances.count())
