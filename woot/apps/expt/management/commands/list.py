# expt.command: data

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
		for experiment in Experiment.objects.all():
			print('mask_channels')
			for mask_channel in experiment.composites.get().mask_channels.all():
				print(mask_channel)

			print('channels')
			for channel in experiment.composites.get().channels.all():
				print(channel)
