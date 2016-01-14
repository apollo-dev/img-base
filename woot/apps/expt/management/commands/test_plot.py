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
import matplotlib.patches as mpatches

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

				# mask CJYLE0RA > -zcomp-zunique-827TIRVT
				# mask CJYLE0RA > -zcomp-zedge-5BP2CN3L
				# mask CJYLE0RA > -zcomp-mgfp-WGF9KQWY
				# mask CJYLE0RA > -zcomp-bmod-WIO67XY9

				for channel in ['-zcomp-zunique-827TIRVT', '-zcomp-zedge-5BP2CN3L', '-zcomp-mgfp-WGF9KQWY', '-zcomp-bmod-WIO67XY9']:
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

			#
			# for channel_index, channel in enumerate(['-zcomp-bmod-WIO67XY9', '-zcomp-mgfp-WGF9KQWY', '-zcomp-zedge-5BP2CN3L', '-zcomp-zunique-827TIRVT']):
			# 	print(channel_index, channel)
			# 	difference = msd_dict[channel] / max_difference # inverse msd normalised to maximum difference
			# 	msd = 1 - ((difference ** 2) ** 0.5).mean()
			# 	# msd = np.mean(np.abs(difference)) # amd
			#
			# 	# msd = msd_dict[channel]
			# 	ax.bar(channel_index+1, msd if 'zunique' not in channel else msd+0.01, width=1, color=colours[channel_index])


			# -zcomp-zunique-827TIRVT data
			zunique_channel = '-zcomp-zunique-827TIRVT'
			zunique_difference = msd_dict[zunique_channel] / max_difference
			zunique_difference_abs = np.abs(zunique_difference)
			zunique_msd = 1 - np.mean(zunique_difference_abs)
			zunique_var = np.std(zunique_difference_abs)

			ax.add_patch(
				mpatches.Rectangle(
					(1, zunique_msd - 0.5*zunique_var),
					1,
					zunique_var,
					facecolor='cyan'
				)
			)

			# line through centre
			ax.plot([1,2],[zunique_msd,zunique_msd],color='black')

			# -zcomp-zedge-5BP2CN3L data
			zedge_channel = '-zcomp-zedge-5BP2CN3L'
			zedge_difference = msd_dict[zedge_channel] / max_difference
			zedge_difference_abs = np.abs(zedge_difference)
			zedge_msd = 1 - np.mean(zedge_difference_abs)
			zedge_var = np.std(zedge_difference_abs)

			ax.add_patch(
				mpatches.Rectangle(
					(2, zedge_msd - 0.5*zedge_var),
					1,
					zedge_var,
					facecolor='red'
				)
			)

			# line through centre
			ax.plot([2,3],[zedge_msd,zedge_msd],color='black')

			# -zcomp-mgfp-WGF9KQWY data
			mgfp_channel = '-zcomp-mgfp-WGF9KQWY'
			mgfp_difference = msd_dict[mgfp_channel] / max_difference
			mgfp_difference_abs = np.abs(mgfp_difference)
			mgfp_msd = 1 - np.mean(mgfp_difference_abs)
			mgfp_var = np.std(mgfp_difference_abs)

			ax.add_patch(
				mpatches.Rectangle(
					(3, mgfp_msd - 0.5*mgfp_var),
					1,
					mgfp_var,
					facecolor='green'
				)
			)

			# line through centre
			ax.plot([3,4],[mgfp_msd,mgfp_msd],color='black')

			# -zcomp-bmod-WIO67XY9 data
			bmod_channel = '-zcomp-bmod-WIO67XY9'
			bmod_difference = msd_dict[bmod_channel] / max_difference
			bmod_difference_abs = np.abs(bmod_difference)
			bmod_msd = 1 - np.mean(bmod_difference_abs)
			bmod_var = np.std(bmod_difference_abs)

			ax.add_patch(
				mpatches.Rectangle(
					(4, bmod_msd - 0.5*bmod_var),
					1,
					bmod_var,
					facecolor='blue'
				)
			)

			# line through centre
			ax.plot([4,5],[bmod_msd,bmod_msd],color='black')

			plt.xlim([0.5,5.5])
			plt.ylim([0.0,1.0])
			plt.ylabel('Inverse mean square difference from manual area')
			ax.set_xticks([1.5, 2.5, 3.5, 4.5])
			ax.set_xticklabels(['zVar', 'zEdge', 'mGFP', 'Selinummi'])
			plt.show()

		else:
			print('Please enter an experiment')
