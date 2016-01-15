# expt.command: input

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.data import *
from apps.expt.util import *
from apps.img.util import *
from apps.cell.models import Cell

# util
import os
import math
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

		cell = Cell.objects.get(pk=9)

		cell_instance = cell.instances.get(t=53)

		# 1. get masks and overlay them
		# cyan/aqua -> 0,255,255 (zunique)
		# red -> 255,0,0 (zedge)
		# green -> 0,128,0 (mgfp)
		# blue -> 0,0,255 (bmod)

		# bounds
		r0, c0, r1, c1 = 0, 750, 200, 950

		zunique_mask = cell_instance.masks.get(channel__name__contains='zunique')
		zedge_mask = cell_instance.masks.get(channel__name__contains='zedge')
		mgfp_mask = cell_instance.masks.get(channel__name__contains='mgfp')
		bmod_mask = cell_instance.masks.get(channel__name__contains='bmod')

		# load mask image and find edge
		mask = zedge_mask
		mask_img = mask.load()
		edge_img = edge_image(mask_img)

		# get list of points that lie on the edge: points_rc
		points_r, points_c = np.where(edge_img)
		points_rc = [list(lm) for lm in list(zip(points_r, points_c))]

		# sort points using a fixed radius
		count, max_count, sorted_points = roll_edge_v1(points_rc)

		cell_centre = np.array([mask.r, mask.c])
		distances = np.array([np.linalg.norm(cell_centre - np.array(p)) for p in sorted_points])
		angles = np.array([math.atan2((cell_centre - np.array(p))[0], (cell_centre - np.array(p))[1]) for p in sorted_points])
		argmin = np.argmin(distances)
		distances = np.roll(distances, -argmin)
		angles = np.roll(angles, -argmin)

		plt.plot(angles, distances)
		plt.ylabel('Distance from cell centre (pixels)')
		plt.xlabel('Angle (rad)')
		plt.show()
