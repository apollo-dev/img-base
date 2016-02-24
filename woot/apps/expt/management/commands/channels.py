# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment

# util
import numpy as np
from skimage import exposure
import matplotlib.pyplot as plt

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		for experiment in Experiment.objects.all():
			print('Experiment: {}'.format(experiment.name))
			for series in experiment.series.all():
				print('  Series: {}'.format(series.name))
				for composite in series.composites.all():
					print('    Composite: {}'.format(composite))
					print('      Image channels: {}'.format(composite.channels.count()))
					for channel in composite.channels.all():
						print('        Channel: {}'.format(channel))

					print('      Mask channels: {}'.format(composite.mask_channels.count()))
					for mask_channel in composite.mask_channels.all():
						print('        Channel: {}'.format(mask_channel))
