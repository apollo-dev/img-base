# expt.command: input

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import *
from apps.expt.util import *
from apps.img.util import *

# util
import os
from os.path import join, exists
from optparse import make_option
from subprocess import call
import shutil as sh
import matplotlib.pyplot as plt
from skimage import exposure
from scipy.misc import imsave
import numpy as np
from numpy import unravel_index
from scipy.ndimage import distance_transform_edt
from scipy.ndimage.filters import gaussian_filter as gf
from scipy.ndimage.measurements import center_of_mass as com

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
		rc = {'com': [], 'dtc': [], 'marker': [], 'gfp': []}
		v = {'com': [(0,0)], 'dtc': [(0,0)], 'marker': [(0,0)], 'gfp': [(0,0)]}
		if experiment_name and series_name:

			# 3. get experiment
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)
			composite = series.composites.get()

			cell = experiment.cells.get(pk=22)
			first_t = -1
			print([cell_instance.t for cell_instance in cell.instances.order_by('t')])
			for cell_instance in cell.instances.order_by('t'):
				first_t = cell_instance.t if first_t==-1 else first_t

				# display
				mask, (r0, c0, rs, cs) = cut_to_black(cell_instance.masks.get().load())

				# load gfp source and cut with mask
				gfp_gon = composite.gons.get(channel__name='0', t=cell_instance.t)
				gfp = exposure.rescale_intensity(gfp_gon.load() * 1.0)

				gfp = gfp[r0:r0+rs , c0:c0+cs]

				mask_3D = np.dstack([mask for i in range(series.zs)])

				masked_gfp = np.ma.array(gf(gfp, sigma=2), mask=(mask_3D==0), fill_value=0)
				masked_gfp_filled = masked_gfp.filled()

				# load mean
				zmean = exposure.rescale_intensity(composite.gons.get(channel__name='-zmean', t=cell_instance.t).load() * 1.0)
				zmean = zmean[r0:r0+rs , c0:c0+cs]

				masked_zmean = np.ma.array(zmean, mask=(mask==0), fill_value=0)
				masked_zmean_filled = masked_zmean.filled()

				print(cell_instance.t)

				# find all centres
				# 1. com (centre of mass)
				com_r, com_c = com(mask)
				com_r, com_c = com_r+r0, com_c+c0
				print('com', com_r, com_c)

				# 2. nucleus

				# 3. dtc ()
				d = distance_transform_edt(mask)
				dtc_r, dtc_c = unravel_index(d.argmax(), d.shape)
				dtc_r, dtc_c = dtc_r+r0, dtc_c+c0
				print('dtc', dtc_r, dtc_c)

				# 4. marker
				marker_r, marker_c = cell_instance.track_instance.markers.get().r, cell_instance.track_instance.markers.get().c
				print('marker', marker_r, marker_c)

				# 5. gfp
				gfp_r, gfp_c = unravel_index(masked_zmean_filled.argmax(), masked_zmean_filled.shape)
				gfp_r, gfp_c = gfp_r+r0, gfp_c+c0
				print('gfp', gfp_r, gfp_c)

				# rc
				rc['com'].append((com_r, com_c))
				rc['dtc'].append((dtc_r, dtc_c))
				rc['marker'].append((marker_r, marker_c))
				rc['gfp'].append((gfp_r, gfp_c))

				if cell_instance.t > first_t:
					v['com'].append((com_r - rc['com'][cell_instance.t-first_t][0], com_c - rc['com'][cell_instance.t-first_t][1]))
					v['dtc'].append((dtc_r - rc['dtc'][cell_instance.t-first_t][0], rc['dtc'][cell_instance.t-first_t][1]))
					v['marker'].append((marker_r - rc['marker'][cell_instance.t-first_t][0], marker_c - rc['marker'][cell_instance.t-first_t][1]))
					v['gfp'].append((gfp_r - rc['gfp'][cell_instance.t-first_t][0], gfp_c - rc['gfp'][cell_instance.t-first_t][1]))

			print('rc')
			print(rc)
			print('v')
			print(v)

		else:
			print('input | Enter an experiment.')
