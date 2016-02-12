# expt.command: step01_input

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import *
from apps.expt.util import *

# util
import os
import re
from os.path import join, exists, splitext
from optparse import make_option
from subprocess import call

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

		make_option('--expt', # option that will appear in cmd
			action='store', # no idea
			dest='expt', # refer to this in options variable
			default='', # some default
			help='Name of the experiment to import' # who cares
		),

		make_option('--series', # option that will appear in cmd
			action='store', # no idea
			dest='series', # refer to this in options variable
			default='', # some default
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

			# 1. Convert track files to csv
			def load_track_file(path, region_name):
				track = [] # stores list of tracks that can then be put into the database

				with open(path, 'rb') as track_file:

					lines = track_file.read().decode('mac-roman').split('\n')[1:-1]
					for i, line in enumerate(lines): # omit title line and final blank line
						line = line.split('\t')

						# details
						index = int(float(line[0]))
						r = int(float(line[6]))
						c = int(float(line[5]))

						track.append((region_name, index, r, c))

				return track

			# for each track file in the track directory, if there is not a .csv file with the same name, then translate it into the new format
			tracks = []
			for file_name in [f for f in os.listdir(experiment.track_path) if ('.xls' in f and 'region' in f)]:
				# 1. parse name for region name
				xls_region_file_template = r'(?P<expt>.+)_s(?P<series>.+)_region-(?P<region_name>.+)\.xls'
				# 2. load track file
				if re.match(xls_region_file_template, file_name).group('series') == series_name:
					region_name = re.match(xls_region_file_template, file_name).group('region_name')
					tracks.append(load_track_file(join(experiment.track_path, file_name), region_name))

			# dump tracks into a template compliant csv file
			csv_file_name = '{}_s{}_{}_regions.csv'.format(experiment_name, series_name, random_string())
			with open(join(experiment.track_path, csv_file_name), 'w+') as out_file:
				out_file.write('expt,series,channel,region,index,r,c\n')
				for track in tracks:
					for marker in track:
						out_file.write('{},{},{},{},{},{},{}\n'.format(experiment_name, series_name,'-zbf', marker[0], marker[1],marker[2], marker[3]))

			# 2. Import tracks
			# select composite
			composite = series.composites.get()

			# add all track files to composite
			data_file_list = [f for f in os.listdir(composite.experiment.track_path) if (os.path.splitext(f)[1] in allowed_data_extensions and composite.experiment.path_matches_series(f, composite.series.name) and 'regions' in f)]

			for df_name in data_file_list:
				print('step02 | data file {}... '.format(df_name), end='\r')
				data_file, data_file_created, status = composite.get_or_create_data_file(composite.experiment.track_path, df_name)
				print('step02 | data file {}... {}'.format(df_name, status))

			### MARKERS
			print('removing previous region tracks...')
			composite.region_markers.all().delete()
			composite.region_track_instances.all().delete()
			composite.region_tracks.all().delete()
			series.region_masks.all().delete()
			series.region_instances.all().delete()
			series.regions.all().delete()

			for data_file in composite.data_files.filter(data_type='regions'):
				data = data_file.load()
				for t in range(composite.series.ts):
					for i, region_marker_prototype in enumerate(data):
						region_track, region_track_created = composite.region_tracks.get_or_create(experiment=composite.experiment,
																																											 series=composite.series,
																																											 composite=composite,
																																											 channel=composite.channels.get(name=region_marker_prototype['channel']),
																																											 name=region_marker_prototype['region'])

						region_track_instance, region_track_instance_created = region_track.instances.get_or_create(experiment=composite.experiment,
																																																				series=composite.series,
																																																				composite=composite,
																																																				channel=composite.channels.get(name=region_marker_prototype['channel']),
																																																				t=t)

						region_marker, region_marker_created = region_track_instance.markers.get_or_create(experiment=composite.experiment,
																																															 series=composite.series,
																																															 composite=composite,
																																															 channel=composite.channels.get(name=region_marker_prototype['channel']),
																																															 region_track=region_track,
																																															 region_track_index=int(region_marker_prototype['index']),
																																															 r=int(region_marker_prototype['r']),
																																															 c=int(region_marker_prototype['c']))

						print('step02 | processing marker t={}/{} ({}/{})... {} tracks, {} instances, {} markers'.format(t+1, composite.series.ts, i+1,len(data),composite.region_tracks.count(), composite.region_track_instances.count(), composite.region_markers.count()), end='\n' if t==composite.series.ts-1 and i==len(data)-1 else '\r')

			# 4. Segment zbf channel
			zbf_channel = composite.channels.get(name='-zbf')
			unique = zbf_channel.segment_regions(region_marker_channel_name='-zbf')

			# 5. re-run cell instance regions if necessary
			# region_mask_channel = composite.mask_channels.get(name__contains=unique)
			# if series.cells.count()>0:
			# 	for t in range(composite.series.ts):
			# 		# load region mask
			# 		region_mask_mask = region_mask_channel.masks.get(t=t)
			# 		region_mask = region_mask_mask.load()
			#
			# 		for cell_instance in series.cell_instances.filter(track_instance__t=t):
			#
			# 			# 3. create cell mask
			# 			region_gray_value_id = region_mask[cell_instance.r, cell_instance.c]
			# 			region_instance = composite.series.region_instances.filter(region_track_instance__t=t, mode_gray_value_id=region_gray_value_id)
			# 			if region_instance:
			# 				region_instance = region_instance[0]
			# 			else:
			# 				region_instance = None
			# 				for ri in composite.series.region_instances.filter(region_track_instance__t=t):
			# 					gray_value_ids = [ri_mask.gray_value_id for ri_mask in ri.masks.all()]
			# 					if region_instance is None and region_gray_value_id in gray_value_ids:
			# 						region_instance = ri
			#
			# 			# for now
			# 			cell_instance.region = region_instance.region if region_instance is not None else None
			# 			cell_instance.region_instance = region_instance if region_instance is not None else None
			# 			cell_instance.save()
			#
			# 	# make tile again
			# 	composite.create_tile(composite.current_zedge_unique)
			#
			# 	# print out new data file
			# 	series.export_data()

			# 6. Region tile
			composite.create_region_tile(unique)

		else:
			print('Please enter an experiment')
