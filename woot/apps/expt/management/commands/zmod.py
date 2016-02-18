# expt.command: input

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import *
from apps.expt.util import *

# util
import os
from os.path import join, exists
from optparse import make_option
from subprocess import call
import shutil as sh

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

		make_option('--expt', # option that will appear in cmd
			action='store', # no idea
			dest='expt', # refer to this in options variable
			default='260714', # some default
			help='Name of the experiment to import' # who cares
		),

		make_option('--series', # option that will appear in cmd
			action='store', # no idea
			dest='series', # refer to this in options variable
			default='15', # some default
			help='Name of the series' # who cares
		),

		make_option('--r', # option that will appear in cmd
			action='store', # no idea
			dest='r', # refer to this in options variable
			default=3, # some default
		),

		make_option('--sigma', # option that will appear in cmd
			action='store', # no idea
			dest='sigma', # refer to this in options variable
			default=3, # some default
		),

		make_option('--dz', # option that will appear in cmd
			action='store', # no idea
			dest='dz', # refer to this in options variable
			default=-8, # some default
		),

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# 1. vars
		experiment_name = options['expt']
		series_name = options['series']
		R = int(options['r'])
		sigma = int(options['sigma'])
		dz = int(options['dz'])

		# 2. fail without experiment name or series name
		if experiment_name and series_name:

			# 3. get experiment
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)
			composite = series.composites.get()

			# 6. make zmod channels
			composite.create_zmod(R=R, delta_z=dz, sigma=sigma)

		else:
			print('input | Enter an experiment.')
