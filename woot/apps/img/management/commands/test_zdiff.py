# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import *
from apps.expt.util import *

# util
import os
from os.path import join, exists, splitext
from optparse import make_option
from subprocess import call
import shutil as sh
from skimage import exposure
import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imsave

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

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# select composite
			composite = series.composites.get()

			zmean = exposure.rescale_intensity(composite.gons.get(channel__name='-zmean', t=t).load() * 1.0)
			zmod = exposure.rescale_intensity(composite.gons.get(channel__name='-zmod', t=t).load() * 1.0)

			zdiff = np.zeros(zmean.shape)
			for unique in np.unique(zmod):
				print(unique, len(np.unique(zmod)))
				zdiff[zmod==unique] = np.mean(zmean[zmod==unique]) / np.sum(zmean)

			plt.imshow(zdiff, cmap='Greys_r')
			plt.show()

			# imsave('zdiff.tiff', zdiff)

		else:
			print('Please enter an experiment')
