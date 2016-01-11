# expt.command: test

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import protrusions

# util
import math
import numpy as np
from optparse import make_option
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

			protrusion_dict = {}

			# for cell_id in protrusions:
			cell_id = '9'
			manual = []
			for frame in protrusions[cell_id]: # SET CELL ID
				cell_instance = series.cell_instances.get(cell__pk=cell_id, t=int(frame)-1)

				protrusion_prototypes = protrusions[cell_id][frame]
				for prototype in protrusion_prototypes[1:]: # SET PROTRUSION

					# get true orientation and length from manual ground truth
					orientation = (180 - prototype[1]) / 180 * math.pi
					orientation = orientation if orientation<math.pi else orientation - 2*math.pi
					length_pixels = prototype[0]
					length = np.abs((math.sin(orientation) * series.rmop + math.cos(orientation) * series.cmop) * length_pixels)

					manual.append((int(frame)-1, (length, orientation)))

					# get matches from mask protrusions of this cell instance
					for mask in cell_instance.masks.all():
						# this
						protrusion_match = min(mask.protrusions.all(), key=lambda p: np.abs(p.orientation - orientation)) if mask.protrusions.count() else None
						if protrusion_match is not None and np.abs(protrusion_match.orientation - orientation) < 0.2:
							if protrusion_match.channel.name in protrusion_dict:
								protrusion_dict[protrusion_match.channel.name].append((int(frame)-1, (protrusion_match.length, protrusion_match.orientation)))
							else:
								protrusion_dict[protrusion_match.channel.name] = [(int(frame)-1, (protrusion_match.length, protrusion_match.orientation))]

			# manual data
			manual_tokens = sorted(manual, key=lambda t: t[0])
			manual_frames = [token[0] for token in manual_tokens]
			manual_lengths = [token[1][0] for token in manual_tokens]

			manual_lengths = np.array(manual_lengths)

			manual_orientations = [token[1][1] for token in manual_tokens]

			plt.plot(manual_frames, manual_lengths, label='manual')

			# channel data
			channel_dict = {}
			max_difference = 0
			for channel_name in protrusion_dict:
				tokens = sorted(protrusion_dict[channel_name], key=lambda t: t[0])
				frames = [token[0] for token in tokens]
				lengths = [token[1][0] for token in tokens]
				orientations = [token[1][1] for token in tokens]
				channel_dict[channel_name] = {'lengths':np.array(lengths), 'frames':np.array(frames), 'orientations':np.array(orientations)}

			for channel_name in channel_dict:
				frames = channel_dict[channel_name]['frames']
				lengths = channel_dict[channel_name]['lengths']
				orientations = channel_dict[channel_name]['lengths']

				plt.plot(frames, lengths, label=channel_name)

			plt.legend()
			plt.show()

		else:
			print('Please enter an experiment')
