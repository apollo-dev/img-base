# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import *
from apps.expt.util import *

# util
import os
from os.path import join, exists, splitext
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

		make_option('--flip_top', # option that will appear in cmd
			action='store_true', # no idea
			dest='flip_top', # refer to this in options variable
			default=False, # some default
			help='Name of the series' # who cares
		),

		make_option('--flip_z', # option that will appear in cmd
			action='store_true', # no idea
			dest='flip_z', # refer to this in options variable
			default=False, # some default
			help='Name of the series' # who cares
		),
	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# vars
		experiment_name = options['expt']
		series_name = options['series']
		flip_top = options['flip_top']
		flip_z = options['flip_z']

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# export
			print('exporting data...')
			series.export_data('UNIQUE00', region_list=[], new_centre=(0,0), flip_top=flip_top, flip_z=flip_z)

		else:
			print('Please enter an experiment')
