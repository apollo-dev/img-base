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

		make_option('--pipeline', # option that will appear in cmd
			action='store', # no idea
			dest='pipeline', # refer to this in options variable
			default='', # some default
			help='Name of the series' # who cares
		),
	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# vars
		experiment_name = options['expt']
		series_name = options['series']
		pipeline = options['pipeline']
		unique_key = '_cp-zunique-bfgfp-UNIQUE00'
		unique = 'UNIQUE00'

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# check pipeline exists
			pipeline_path = join(experiment.pipeline_path, pipeline)
			if pipeline and not exists(pipeline_path):
				raise CommandError('entered pipeline does not exist: {}'.format(pipeline))

			# select composite
			composite = series.composites.get()

			# segment using the gfp channels only
			bfgfp_channel = composite.channels.get(name='-mgfp')
			bfgfp_unique = bfgfp_channel.segment(unique, unique_key, pipeline=pipeline)

			# tile
			print('creating tile...')
			composite.create_tile(bfgfp_unique, side_channel='-mgfp', main_channel='-mgfp', region_list=[])

			# export
			print('exporting data...')
			composite.series.export_data(bfgfp_unique, region_list=[])

		else:
			print('Please enter an experiment')
