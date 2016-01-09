# expt.command: test

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.img.util import cut_to_black, nonzero_mean, edge_image, sort_edge, fold_edge, edge_fall, roll_edge_v1

# util
import os
import math
import numpy as np
from os.path import join, exists, splitext
from optparse import make_option
from subprocess import call
import shutil as sh
import matplotlib.pyplot as plt
from scipy.signal import find_peaks_cwt as find_peaks
from scipy.ndimage.filters import gaussian_filter as gf

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

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# cell_instance = series.cell_instances.get(t=48, cell__pk=4)
			# cell_instance = series.cell_instances.get(t=49, cell__pk=9)
			# cell_instance = series.cell_instances.get(pk=198)

			# load mask image
			# 1. for each cell mask, load mask image
			outlines = {}
			colours = ['red','green','blue','purple']
			for i, cell_mask in enumerate(cell_instance.masks.filter(channel__name__contains='zunique')):
				mask_img = cell_mask.load()

				# get edge
				edge_img = edge_image(mask_img)

				# get list of points
				points_r, points_c = np.where(edge_img)
				points = [list(lm) for lm in list(zip(points_r, points_c))]

				sorted_points = roll_edge_v1(points)

				# plot distances in order
				cell_centre = np.array([cell_mask.r, cell_mask.c])
				distances = np.array([np.linalg.norm(cell_centre - np.array(p)) for p in sorted_points])
				argmin = np.argmin(distances)
				distances = np.roll(distances, -argmin)
				distances = gf(distances, sigma=2)
				# plt.plot(distances)
				# plt.scatter(cell_mask.c, cell_mask.r)

				# find peaks in distance array
				peaks = find_peaks(distances, np.array([9]))
				# plt.scatter(peaks, [distances[peak] for peak in peaks])

				# roll back to find true peak positions
				true_peaks = np.array(peaks) + argmin
				true_peaks[true_peaks>=len(sorted_points)] -= len(sorted_points)

				# find end point of protrusions
				protrusion_end_points = [sorted_points[peak] for peak in true_peaks]

				for protrusion_end_point in protrusion_end_points:
					print('new protrusion for cell mask {} for cell instance {}'.format(cell_mask.pk, cell_instance.pk))
					relative_end_point = cell_centre - np.array(protrusion_end_point)
					print(cell_centre, protrusion_end_point)
					print('length from centre: {} microns'.format(np.linalg.norm(relative_end_point * series.scaling())))
					print('orientation: {} degrees'.format(180 / math.pi * math.atan2(relative_end_point[0], relative_end_point[1])))

				# plt.scatter([sorted_points[peak][1] for peak in true_peaks], [sorted_points[peak][0] for peak in true_peaks])

				# plot outlines to check
				plt.plot([point[1] for point in sorted_points], [point[0] for point in sorted_points], label='radius: 2')
				# plt.scatter(points_c, points_r, label=cell_mask.channel.name, color=colours[i])

			# plt.legend()
			# plt.axis('equal')
			plt.show()

		else:
			print('Please enter an experiment')
