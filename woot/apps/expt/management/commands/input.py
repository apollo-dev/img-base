# expt.command: input

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment

# util
from subprocess import call

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		# 1. vars
		experiment_name = options['expt']
		series_name = options['series']
		lif_name = options['lif']
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
			if len(os.listdir(experiment.storage_path))==0 and len(os.listdir(experiment.composite_path))==0:

				# extract lif
				lif_path = join(lif_root, lif_name)
				lif_template = '{}/{}_s%s_ch%c_t%t_z%z.tiff'.format(experiment.storage_path, experiment_name)

				# run extract
				print('input | Extracting lif...')
				call('{} {} {}'.format(bfconvert, lif_path, lif_template), shell=True)

			else:
				print('input | .lif already extracted for experiment {}, series {}; continuing... '.format(experiment_name, series_name))

			# 7. series metadata
			metadata_file_name = join(experiment.inf_path, '{}.txt'.format(experiment_name))

			if not exists(metadata_file_name):
				# run show inf
				lif_path = join(lif_root, lif_name)
				print('step01 | Extracting lif metadata for experiment {}... '.format(experiment_name))
				call('{} -nopix -omexml {} > {}'.format(showinf, lif_path, metadata_file_name), shell=True)

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

			# 8. 

		else:
			print('input | Enter an experiment.')
