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
import matplotlib.pyplot as plt

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

	)

	args = ''
	help = ''

	def handle(self, *args, **options):

		# vars
		experiment_name = options['expt']
		series_name = options['series']

		# 1. create experiment and series
		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)
			composite = series.composites.get()

			# somehow generate five number series to plot for each cell
			cell_index = '20' # 4 8 9 10 11 20
			cell = series.cells.get(pk=cell_index)
			time_series = {}
			frames = sorted([int(frame) for frame in cells[cell_index]])
			for frame in frames:

				area = cells[cell_index][str(frame)]

				if 'manual' in time_series:
					time_series['manual'].append(area)
				else:
					time_series['manual'] = [area]

				cell_instance = cell.instances.get(t=frame)

				for channel in ['-zcomp-zmean-BE4XTNBJ', '-zcomp-zedge-8FBKJ3S8', '-zcomp-mgfp-M5M2PL1S', '-zcomp-bmod-VVP4L60K']:
					mask = cell_instance.masks.get(channel__name=channel)

					if channel in time_series:
						time_series[channel].append(mask.A())
					else:
						time_series[channel] = [mask.A()]

			channels = sorted([channel for channel in time_series])
			for channel in channels:
				plt.plot(frames, time_series[channel], label=channel[7:-9] if channel!='manual' else channel)


			plt.legend(loc=2,prop={'size':10})
			plt.ylabel('Area ($\mu m^2$)')
			plt.xlabel('Frame')
			plt.show()

		else:
			print('Please enter an experiment')
