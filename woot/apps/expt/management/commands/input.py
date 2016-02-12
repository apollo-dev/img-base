# expt.command: input

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment
from apps.expt.data import *
from apps.expt.util import *

# util
import os
from os.path import join, exists
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

		make_option('--lif', # option that will appear in cmd
			action='store', # no idea
			dest='lif', # refer to this in options variable
			default='', # some default
			help='Name of the .lif archive' # who cares
		),

		make_option('--r', # option that will appear in cmd
			action='store', # no idea
			dest='r', # refer to this in options variable
			default=5, # some default
		),

		make_option('--sigma', # option that will appear in cmd
			action='store', # no idea
			dest='sigma', # refer to this in options variable
			default=5, # some default
		),

		make_option('--dz', # option that will appear in cmd
			action='store', # no idea
			dest='dz', # refer to this in options variable
			default=-8, # some default
		),

		make_option('--region', # option that will appear in cmd
			action='store', # no idea
			dest='region', # refer to this in options variable
			default='', # some default
			help='Name of the series' # who cares
		),

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# 1. vars
		experiment_name = options['expt']
		series_name = options['series']
		lif_name = options['lif']
		R = int(options['r'])
		sigma = int(options['sigma'])
		dz = int(options['dz'])
		data_root = settings.DATA_ROOT
		lif_root = settings.LIF_ROOT
		bfconvert_path = join(data_root, 'bftools', 'bfconvert')
		showinf_path = join(data_root, 'bftools', 'showinf')

		# 2. fail without experiment name or series name
		if experiment_name and series_name:

			# 3. create experiment
			experiment, experiment_created = Experiment.objects.get_or_create(name=experiment_name)
			if experiment_created:
				# set metadata
				experiment.get_templates()
				print('input | experiment path exists, experiment {}...	created.'.format(experiment_name))
			else:
				print('input | experiment path exists, experiment {}... already exists.'.format(experiment_name))

			# 4. make experiment paths in data folder
			experiment.make_paths(join(data_root, experiment.name))

			# 5. create series
			print('input | series {}... '.format(series_name), end='\r')
			series, series_created = experiment.series.get_or_create(name=series_name)
			if series_created:
				print('input | series {}... created.'.format(series_name))
			else:
				print('input | series {}... already exists.'.format(series_name))

			# 6. extract lif if necessary
			if len(os.listdir(experiment.storage_path))==0:

				# extract lif
				lif_path = join(lif_root, lif_name)
				lif_template = '{}/{}_s%s_ch%c_t%t_z%z.tiff'.format(experiment.storage_path, experiment_name)

				# run extract
				print('input | Extracting lif...')
				call('{} {} {}'.format(bfconvert_path, lif_path, lif_template), shell=True)

			else:
				print('input | .lif already extracted for experiment {}, series {}; continuing... '.format(experiment_name, series_name))

			# 7. series metadata
			metadata_file_name = join(experiment.inf_path, '{}.txt'.format(experiment_name))

			if not exists(metadata_file_name):
				# run show inf
				lif_path = join(lif_root, lif_name)
				print('step01 | Extracting lif metadata for experiment {}... '.format(experiment_name))
				call('{} -nopix -omexml {} > {}'.format(showinf_path, lif_path, metadata_file_name), shell=True)

			metadata = series_metadata(metadata_file_name, series_name)

			series.rmop = float(metadata['rmop'])
			series.cmop = float(metadata['cmop'])
			series.zmop = float(metadata['zmop'])
			series.tpf = float(metadata['tpf_in_seconds']) / 60.0
			series.rs = int(metadata['rs'])
			series.cs = int(metadata['cs'])
			series.zs = int(metadata['zs'])
			series.ts = int(metadata['ts'])
			series.save()

			# 4. import specified series
			# for each path in the experiment folder, create new path if the series matches.
			for root in experiment.img_roots():

				img_files = [f for f in os.listdir(root) if (os.path.splitext(f)[1] in allowed_img_extensions and experiment.path_matches_series(f, series_name))]
				num_img_files = len(img_files)

				if num_img_files>0:
					for i, file_name in enumerate(img_files):
						path, path_created, path_message = experiment.get_or_create_path(series, root, file_name)
						print('step01 | adding image files in {}: ({}/{}) {} ...path {}{}'.format(root, i+1, num_img_files, file_name, path_message, spacer), end='\n' if i==num_img_files-1 else '\r')

				else:
					print('step01 | no files found in {}'.format(root))

			# 4a. correct series metadata if necessary
			series.ts = max(series.paths.all(), key=lambda p: p.t).t + 1
			series.save()

			# 5. composite
			print('step01 | creating composite for experiment {} series {}'.format(experiment_name, series_name))
			composite = series.compose() if series.composites.filter().count()==0 else series.composites.get()

			# 6. make zmod channels
			composite.create_zmod(R=R, delta_z=dz, sigma=sigma)
			composite.create_zunique()
			composite.create_tracking()

		else:
			print('input | Enter an experiment.')
