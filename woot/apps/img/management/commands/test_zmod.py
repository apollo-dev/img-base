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
			default='260714', # some default
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

		R = 5
		delta_z = -8
		sigma = 5

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# select composite
			composite = series.composites.get()

			# load gfp
			gfp_gon = composite.gons.get(t=t, channel__name='0')
			gfp = exposure.rescale_intensity(gfp_gon.load() * 1.0)
			gfp = gf(gfp, sigma=sigma) # <<< SMOOTHING
			print('loaded gfp...')

			# load bf
			bf_gon = composite.gons.get(t=t, channel__name='1')
			bf = exposure.rescale_intensity(bf_gon.load() * 1.0)
			print('loaded bf...')

			# initialise images
			Z = np.zeros(composite.series.shape(d=2), dtype=int)
			Zmean = np.zeros(composite.series.shape(d=2))
			Zbf = np.zeros(composite.series.shape(d=2))

			Z = np.argmax(gfp, axis=2) + delta_z

			# outliers
			Z[Z<0] = 0
			Z[Z>composite.series.zs-1] = composite.series.zs-1

			# for level in range(bf.shape[2]):
			# 	print('level {}...'.format(level))
			# 	bf[:,:,level] = convolve(bf[:,:,level], np.ones((R,R)))
			# 	Zbf[Z==level] = bf[Z==level,level]
			#
			# Zmean = 1 - np.mean(gfp, axis=2) / np.max(gfp, axis=2)
			#
			# plt.imshow(Zbf, cmap='Greys_r')
			# plt.show()

			# imsave('zbf_sigma_too_high.tiff', Zbf)

		else:
			print('Please enter an experiment')
