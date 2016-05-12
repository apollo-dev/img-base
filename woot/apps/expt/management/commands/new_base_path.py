# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import corrections

# util
import numpy as np
from skimage import exposure
import matplotlib.pyplot as plt
from optparse import make_option

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('--expt', # option that will appear in cmd
			action='store', # no idea
			dest='expt', # refer to this in options variable
			default='', # some default
			help='Name of the experiment to import' # who cares
		),
	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# 0. get experiment and series
		experiment = Experiment.objects.get(name=options['expt'])

		experiment.make_paths('/Users/nicholaspiano/Desktop/img/{}'.format(experiment.name))
		experiment.save()
