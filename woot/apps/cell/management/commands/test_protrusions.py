# expt.command: test

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.img.util import cut_to_black, nonzero_mean, edge_image, sort_edge, fold_edge, edge_fall, roll_edge

# util
import os
import numpy as np
from os.path import join, exists, splitext
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

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			cell_instance = series.cell_instances.get(t=43, cell__pk=9) # nice protrusion with visible brightfield

			# load mask image
			# 1. for each cell mask, load mask image
			outlines = {}
			colours = ['red','green','blue','purple']
			for i, cell_mask in enumerate(cell_instance.masks.filter(channel__name__contains='zedge')):
				mask_img = cell_mask.load()

				# get edge
				edge_img = edge_image(mask_img)

				# get list of points
				points_r, points_c = np.where(edge_img)
				points = list(zip(points_r, points_c))
				sorted_points = roll_edge(np.array([cell_mask.r, cell_mask.c]), points)
				# sorted_points = sort_edge((cell_mask.r, cell_mask.c), points)
				# sorted_points = fold_edge((cell_mask.r, cell_mask.c), points)
				# sorted_points = edge_fall((cell_mask.r, cell_mask.c), points)
				plt.plot([point[1] for point in sorted_points], [point[0] for point in sorted_points], label=cell_mask.channel.name, color=colours[i])
				plt.scatter(points_c, points_r, label=cell_mask.channel.name, color=colours[i])

			# plt.legend()
			plt.axis('equal')
			plt.show()

		else:
			print('Please enter an experiment')
