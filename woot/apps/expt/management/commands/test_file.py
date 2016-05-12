# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.img.models import Composite

# util
import numpy as np
from skimage import exposure
import matplotlib.pyplot as plt

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		path = '../../21_02_16_HUVEC_MB4175_s1{}.xls'
		for xls_file_name in [path.format(i) for i in [6,7]]:
			tracks = {} # stores list of tracks that can then be put into the database

			with open(xls_file_name, 'rb') as track_file:

				lines = track_file.read().decode('mac-roman').split('\n')[1:-1]
				for i, line in enumerate(lines): # omit title line and final blank line
					line = line.split('\t')

					# details
					track_id = int(float(line[1]))
					r = int(float(line[4]))
					c = int(float(line[3]))
					t = int(float(line[2])) - 1
					if r>=512 or c>=512:
						print(xls_file_name, track_id, t, r, c)

					if track_id in tracks:
						tracks[track_id].append((r,c,t))
					else:
						tracks[track_id] = [(r,c,t)]
			#
			# for key, value in tracks.items():
			# 	for r,c,t in value:
			# 		if r>=512 or c>=512:
			# 			print('key', t, r, c)
