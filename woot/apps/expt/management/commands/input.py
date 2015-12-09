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
from os.path import join, exists
from optparse import make_option
from subprocess import call
import shutil as sh

spacer = ' ' *  20

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

    make_option('--lif', # option that will appear in cmd
      action='store', # no idea
      dest='lif', # refer to this in options variable
      default='', # some default
      help='Name of the .lif archive' # who cares
    ),

  )

  args = ''
  help = ''

  def handle(self, *args, **options):

    # vars
    experiment_name = options['expt']
    series_name = options['series']
    lif_name = options['lif']
    data_root = settings.DATA_ROOT
    lif_root = settings.LIF_ROOT
    bfconvert = join(data_root, 'bftools', 'bfconvert')
    showinf = join(data_root, 'bftools', 'showinf')

    # 1. create experiment and series
    if experiment_name!='' and series_name!='':
      experiment, experiment_created = Experiment.objects.get_or_create(name=experiment_name)
      if experiment_created:
        # set metadata
        experiment.get_templates()
        print('step01 | experiment path exists, experiment {}...  created.'.format(experiment_name))
      else:
        print('step01 | experiment path exists, experiment {}... already exists.'.format(experiment_name))

      print('step01 | series {}... '.format(series_name), end='\r')
      series, series_created = experiment.series.get_or_create(name=series_name)
      if series_created:
        print('step01 | series {}... created.'.format(series_name))
      else:
        print('step01 | series {}... already exists.'.format(series_name))

      experiment.make_paths(join(data_root, experiment.name))

      # 2. if lif is not extracted, do it.
      if len(os.listdir(experiment.storage_path))==0 and len(os.listdir(experiment.composite_path))==0:

        # extract lif
        lif_path = join(lif_root, lif_name)
        lif_template = '{}/{}_s%s_ch%c_t%t_z%z.tiff'.format(experiment.storage_path, experiment_name)

        # run extract
        print('step01 | Extracting lif ')
        call('{} {} {}'.format(bfconvert, lif_path, lif_template), shell=True)

      else:
        print('step01 | .lif already extracted for experiment {}, series {}; continuing... '.format(experiment_name, series_name))

      # 3. series measurements
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
      composite = series.compose()

      # 6. make zmod channels
      if composite.channels.filter(name='-zmod').count()==0:
        mod = composite.mods.create(id_token=generate_id_token('img', 'Mod'), algorithm='mod_zmod')

        # Run mod
        print('step01 | processing mod_zmod...', end='\r')
        mod.run()
        print('step01 | processing mod_zmod... done.{}'.format(spacer))

      else:
        print('step01 | zmod already exists...')

      # 7. copy zcomp (for tracking) to ij directory
      for gon in composite.channels.get(name='-zcomp').gons.all():
        if not exists(join(composite.experiment.ij_path, series.name)):
          os.mkdir(join(composite.experiment.ij_path, series.name))
        sh.copy2(gon.paths.get().url, join(composite.experiment.ij_path, series.name, gon.paths.get().file_name))

      # 8. copy zmean (for checking) to mean directory
      for gon in composite.channels.get(name='-zmean').gons.all():
        if not exists(join(composite.experiment.base_path, 'mean', series.name)):
          os.makedirs(join(composite.experiment.base_path, 'mean', series.name))
        sh.copy2(gon.paths.get().url, join(composite.experiment.base_path, 'mean', series.name, gon.paths.get().file_name))

      # 9. copy single zbf image from beginning of time series to regions path for tracking
      region_tracking_gon = composite.channels.get(name='-zbf').gons.get(t=0)
      sh.copy2(region_tracking_gon.paths.get().url, join(composite.experiment.regions_path, '{}_s{}_region_tracking.tiff'.format(experiment.name, series.name)))

    else:
      print('Please enter an experiment')
