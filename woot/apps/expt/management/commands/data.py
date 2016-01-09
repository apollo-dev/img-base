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

		make_option('--region', # option that will appear in cmd
			action='store', # no idea
			dest='region', # refer to this in options variable
			default='', # some default
			help='Name of the series' # who cares
		),

		make_option('--threshold', # option that will appear in cmd
			action='store', # no idea
			dest='threshold', # refer to this in options variable
			default='1.2', # some default
			help='Name of the series' # who cares
		),

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# vars
		experiment_name = options['expt']
		series_name = options['series']
		region_list = options['region'].split(',')
		if region_list==['']:
			region_list = []
		threshold_correction_factor = float(options['threshold'])

		if experiment_name!='' and series_name!='':
			experiment = Experiment.objects.get(name=experiment_name)
			series = experiment.series.get(name=series_name)

			# 2. Import tracks
			# select composite
			composite = series.composites.get()

			# convert track files if necessary
			for file_name in [f for f in os.listdir(experiment.track_path) if ('.xls' in f and 'region' not in f and '_s{}'.format(series_name) in f)]:
				name_with_index, ext = splitext(file_name)
				convert_track_file(composite, experiment.track_path, name_with_index)

			# add all track files to composite
			data_file_list = [f for f in os.listdir(composite.experiment.track_path) if (os.path.splitext(f)[1] in allowed_data_extensions and composite.experiment.path_matches_series(f, composite.series.name) and 'regions' not in f)]

			for df_name in data_file_list:
				print('step02 | data file {}... '.format(df_name), end='\r')
				data_file, data_file_created, status = composite.get_or_create_data_file(composite.experiment.track_path, df_name)
				if not data_file_created:
					os.remove(data_file.url)
					data_file.delete()
					status = 'deleted.'
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
																																								 t=int(marker_prototype['t']))

					marker, marker_created = track_instance.markers.get_or_create(experiment=composite.experiment,
																																				series=composite.series,
																																				composite=composite,
																																				channel=composite.channels.get(name=marker_prototype['channel']),
																																				track=track,
																																				r=int(marker_prototype['r']),
																																				c=int(marker_prototype['c']))

					print('step02 | processing marker ({}/{})... {} tracks, {} instances, {} markers'.format(i+1,len(data),composite.tracks.count(), composite.track_instances.count(), composite.markers.count()), end='\n' if i==len(data)-1 else '\r')

			if composite.channels.filter(name__contains='mgfp') and False:
				# segment using the gfp channels only
				mgfp_channel = composite.channels.get(name__contains='mgfp')
				mgfp_unique = mgfp_channel.segment(threshold_correction_factor=threshold_correction_factor)

				# tile
				print('creating tile...')
				composite.create_tile(mgfp_unique, side_channel='-mgfp', main_channel='-mgfp', region_list=region_list)

				# export
				print('exporting data...')
				composite.series.export_data(mgfp_unique, region_list=region_list)

			else:
				# segment
				composite.create_zunique()
				zunique_channel = composite.channels.get(name='-zunique')

				zunique_unique = zunique_channel.segment()
				zedge_channel = composite.create_zedge(channel_unique_override=zunique_unique)
				zedge_unique = zedge_channel.segment(marker_channel_name='-zcomp', threshold_correction_factor=threshold_correction_factor)

				composite.current_zedge_unique = zedge_unique
				composite.save()

				# tile
				print('creating tile...')
				composite.create_tile(composite.current_zedge_unique, region_list=region_list)

				# export
				print('exporting data...')
				composite.series.export_data(composite.current_zedge_unique, region_list=region_list)

		else:
			print('Please enter an experiment')
