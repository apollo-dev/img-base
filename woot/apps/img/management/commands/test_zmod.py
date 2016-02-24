# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment, Series
from apps.expt.util import generate_id_token, str_value, random_string
from apps.img.util import cut_to_black, create_bulk_from_image_set, nonzero_mean, edge_image, scan_point, mask_edge_image
from apps.expt.data import *

# util
import os
import scipy
from os.path import join, exists, splitext
from optparse import make_option
from subprocess import call
import shutil as sh
import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imread, imsave, toimage
from scipy.ndimage import label
from scipy.ndimage.filters import gaussian_filter as gf
from scipy.ndimage.filters import convolve
from scipy.ndimage.measurements import center_of_mass as com
from scipy.stats.mstats import mode
from scipy.ndimage.morphology import binary_erosion as erode
from scipy.ndimage.morphology import binary_dilation as dilate
from scipy.ndimage import distance_transform_edt
from scipy.ndimage.measurements import label
from scipy.interpolate import interp2d
from skimage import exposure

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

		make_option('--expt', # option that will appear in cmd
			action='store', # no idea
			dest='expt', # refer to this in options variable
			default='260714-test', # some default
			help='Name of the experiment to import' # who cares
		),

		make_option('--series', # option that will appear in cmd
			action='store', # no idea
			dest='series', # refer to this in options variable
			default='15', # some default
			help='Name of the series' # who cares
		),

		make_option('--t', # option that will appear in cmd
			action='store', # no idea
			dest='t', # refer to this in options variable
			default='0', # some default
		),

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# vars
		experiment_name = options['expt']
		series_name = options['series']
		t = options['t']

		R = 1
		delta_z = -8
		# sigma = 5

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# select composite
			composite = series.composites.get()

			# load gfp
			gfp_gon = composite.gons.get(t=t, channel__name='0')
			gfp = exposure.rescale_intensity(gfp_gon.load() * 1.0)
			gfp = gf(gfp, sigma=2) # <<< SMOOTHING
			print('loaded gfp...')

			# load bf
			bf_gon = composite.gons.get(t=t, channel__name='1')
			bf = exposure.rescale_intensity(bf_gon.load() * 1.0)
			print('loaded bf...')

			gfp_max = np.max(gfp, axis=2)

			# normalise
			gfp_norm = np.rollaxis(gfp, 2).astype(float) / gfp_max.astype(float) # values are now normalised to 1.0
			gfp_norm = np.rollaxis(gfp_norm, 0, 3)

			# apply delta-z
			gfp_norm = np.roll(gfp_norm, -10, axis=2)

			# turn array into mask and apply to bf
			bf_masked = np.zeros(gfp_norm.shape)
			bf_masked[gfp_norm == 1] = bf[gfp_norm == 1]
			zbf = np.sum(bf_masked, axis=2)

			plt.imshow(zbf, cmap='Greys_r')
			plt.show()

		else:
			print('Please enter an experiment')
