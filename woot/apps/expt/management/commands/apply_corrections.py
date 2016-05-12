# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import corrections, zlevels

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

		make_option('--series', # option that will appear in cmd
			action='store', # no idea
			dest='series', # refer to this in options variable
			default='', # some default
			help='Name of the series' # who cares
		),
	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# 0. get experiment and series
		experiment = Experiment.objects.get(name=options['expt'])
		series = experiment.series.get(name=options['series'])
		print('corrections ', experiment, series)

		# 1. get corrections
		experiment_corrections = corrections[experiment.name]

		# 2. for each cell mask, modify certain values
		for i, cell_mask in enumerate(series.cell_masks.all()):
			t = cell_mask.t

			correction_z = zlevels[str(series.name)]['out'][t] - zlevels[str(series.name)]['in'][t]
			cell_mask.z += correction_z

			if t>0:
				previous_value_r, previous_value_c = tuple(experiment_corrections[t-1])
				value_r, value_c = tuple(experiment_corrections[t])
				correction_r, correction_c = value_r - previous_value_r, value_c - previous_value_c

				# print(i+1, series.cell_masks.count(), correction_r, correction_c)
				#
				# if cell_mask.cell.pk == 324:
				# 	P_original = cell_mask.Location_Center_Y * cell_mask.series.rmop
				# 	P_corrected = (cell_mask.Location_Center_Y - correction_r) * cell_mask.series.rmop
				#
				# 	Q_original = cell_mask.Location_Center_X * cell_mask.series.cmop
				# 	Q_corrected = (cell_mask.Location_Center_X - correction_c) * cell_mask.series.cmop
				#
				# 	R_original = cell_mask.r * cell_mask.series.rmop
				# 	R_corrected = (cell_mask.r - correction_r) * cell_mask.series.rmop
				#
				# 	S_original = cell_mask.c * cell_mask.series.cmop
				# 	S_corrected = (cell_mask.c - correction_c) * cell_mask.series.cmop
				#
				# 	print(t, correction_r, correction_c, 'P', P_original, P_corrected, 'Q', Q_original, Q_corrected, 'R', R_original, R_corrected, 'S', S_original, S_corrected)

				cell_mask.r -= correction_r
				cell_mask.c -= correction_c
				cell_mask.Location_Center_Y -= correction_r
				cell_mask.Location_Center_X -= correction_c

			cell_mask.save()
