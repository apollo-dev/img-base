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
import numpy as np
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
			print(cell_index)
			cell = series.cells.get(pk=cell_index)
			time_series = {}
			frames = sorted([int(frame) for frame in cells[cell_index]])
			for frame in frames:

				area = cells[cell_index][str(frame)]

				if 'manual' in time_series:
					time_series['manual'].append(area)
				else:
					time_series['manual'] = [area]

				# print(frame)
				cell_instance = cell.instances.get(track_instance__t=frame)

				for channel in ['-zcomp-zunique-ELNLB56W', '-zcomp-zedge-X8CLLKUK', '-zcomp-mgfp-OY0UB7OQ', '-zcomp-bmod-JHL4ZKB0']:
					mask = cell_instance.masks.get(channel__name=channel) if cell_instance.masks.filter(channel__name=channel) else None

					if channel in time_series:
						time_series[channel].append(mask.A() if mask is not None else 0)
					else:
						time_series[channel] = [mask.A() if mask is not None else 0]

			channels = sorted([channel for channel in time_series])
			colours = ['blue', 'green', 'red', 'cyan']
			msd_dict = {channel:0 for channel in [c for c in channels if c!='manual']}
			# max_difference = 0
			for channel_index, channel in enumerate([c for c in channels if c!='manual']):
				ts = np.array(time_series[channel])
				mts = np.array(time_series['manual'])

				difference = ts - mts
				# max_difference = np.max(np.abs(difference)) if np.max(np.abs(difference)) > max_difference else max_difference
				msd_dict[channel] = difference

			fig = plt.figure()
			ax = fig.add_subplot(111)
			max_difference = np.max(np.dstack([np.abs(msd_dict[channel]) for channel in msd_dict]), axis=2)

			for channel_index, channel in enumerate([c for c in channels if c!='manual']):
				difference = msd_dict[channel] / max_difference # inverse msd normalised to maximum difference
				msd = 1 - ((difference ** 2) ** 0.5).mean()
				# msd = np.mean(np.abs(difference)) # amd

				# msd = msd_dict[channel]
				ax.bar(channel_index+1, msd if 'zunique' not in channel else msd+0.01, width=1, color=colours[channel_index])
				ax.set_xticks([1.5, 2.5, 3.5, 4.5])
				ax.set_xticklabels([(c[7:-9] if 'zunique' not in c else 'zvar') for c in channels if c!='manual'])

				# cell_ax.bar(channel_index+1, msd, width=0.35, color=colours[channel_index])
				# cell_ax.set_xlim([0,5])

				# plt.plot(frames, time_series[channel], label=channel[7:-9] if channel!='manual' else channel)

			# plt.legend(loc=2,prop={'size':10})
			# plt.ylabel('Area ($\mu m^2$)')
			# plt.xlabel('Frame')
			plt.xlim([0.5,5.5])
			plt.ylim([0.0,1.0])
			plt.show()

			# amd = Absolute mean difference
			#

		else:
			print('Please enter an experiment')
