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
from os.path import join

spacer = ' ' *	20

### Command
class Command(BaseCommand):

	def handle(self, *args, **options):
		file1 = join(settings.SITE_ROOT, 'correct', '08_04_16.xls')
		file2 = join(settings.SITE_ROOT, 'correct', '12_02_16.xls')
		file3 = join(settings.SITE_ROOT, 'correct', '21_02_16.xls')

		for f in [file1, file2, file3]:
			track = []

			with open(f, 'rb') as of:
				lines = of.read().decode('mac-roman').split('\n')[1:-1]
				for i, line in enumerate(lines): # omit title line and final blank line
					line = line.split('\t')

					# details
					r = int(float(line[4]))
					c = int(float(line[3]))

					track.append((r,c))

			pr, pc = 0, 0
			print(f)
			for r,c in track:
				print('[{},{}],'.format(r - pr, c - pc))
				pr, pc = r, c
