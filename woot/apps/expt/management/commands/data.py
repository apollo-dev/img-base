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

			# 2. Import tracks
			# select composite
			composite = series.composites.get()

			# add all track files to composite
			data_file_list = [f for f in os.listdir(composite.experiment.track_path) if (os.path.splitext(f)[1] in allowed_data_extensions and composite.experiment.path_matches_series(f, composite.series.name) and 'regions' not in f)]

			for df_name in data_file_list:
				print('step02 | data file {}... '.format(df_name), end='\r')
				data_file, data_file_created, status = composite.get_or_create_data_file(composite.experiment.track_path, df_name)
				print('step02 | data file {}... {}'.format(df_name, status))

			for data_file in composite.data_files.filter(data_type='markers'):
				data = data_file.load()
				for i, marker_prototype in enumerate(data):
					track, track_created = composite.tracks.get_or_create(experiment=composite.experiment,
																																series=composite.series,
																																composite=composite,
																																channel=composite.channels.get(name=marker_prototype['channel']),
																																track_id=marker_prototype['id'])

					track_instance, track_instance_created = track.instances.get_or_create(experiment=composite.experiment,
																																								 series=composite.series,
																																								 composite=composite,
																																								 channel=composite.channels.get(name=marker_prototype['channel']),
																																								 t=int(marker_prototype['t'])-1)

					marker, marker_created = track_instance.markers.get_or_create(experiment=composite.experiment,
																																				series=composite.series,
																																				composite=composite,
																																				channel=composite.channels.get(name=marker_prototype['channel']),
																																				track=track,
																																				r=int(marker_prototype['r']),
																																				c=int(marker_prototype['c']))

					print('step02 | processing marker ({}/{})... {} tracks, {} instances, {} markers'.format(i+1,len(data),composite.tracks.count(), composite.track_instances.count(), composite.markers.count()), end='\n' if i==len(data)-1 else '\r')

			# 3. Generate zDiff channel
			zdiff_channel = composite.create_zdiff()

			# 4. Segment zdiff channel
			zdiff_unique = zdiff_channel.segment(marker_channel_name='-zcomp')

			# 5. Generate zEdge channel
			zedge_channel = composite.create_zedge(channel_unique_override=zdiff_unique)

			# 6. Segment zEdge channel
			zedge_unique = zedge_channel.segment(marker_channel_name='-zcomp', threshold_correction_factor=1.2)

			# 8. Tile mod
			composite.current_zedge_unique = zedge_unique
			composite.save()

			composite.create_tile(channel_unique_override=zedge_unique)

		else:
			print('Please enter an experiment')