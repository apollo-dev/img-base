# expt.command: test

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.expt.models import Experiment

# util
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

			for cell_pk in [4,9]:
				cell = series.cells.get(pk=cell_pk)
				for i, cell_mask in enumerate(cell.masks.filter(channel__name__contains='bmod')):
					status, number_of_protrusions = cell_mask.find_protrusions()
					print('{}, mask {}/{}, {}, {} protrusions'.format(cell_pk, i+1, cell.masks.filter(channel__name__contains='bmod').count(), status, number_of_protrusions))

		else:
			print('Please enter an experiment')
