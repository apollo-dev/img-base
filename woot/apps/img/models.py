# woot.apps.img.models

# django
from django.db import models

# local
from apps.expt.models import Experiment, Series
from apps.expt.util import generate_id_token, str_value, random_string
from apps.img.util import cut_to_black, create_bulk_from_image_set, nonzero_mean, edge_image, scan_point, mask_edge_image
from apps.expt.data import *

# util
import os
from os.path import exists, join
import re
import numpy as np
import scipy
from scipy.misc import imread, imsave, toimage
from scipy.ndimage import label
from scipy.ndimage.filters import gaussian_filter as gf
from scipy.ndimage.filters import convolve
from scipy.ndimage.measurements import center_of_mass as com
from scipy.stats.mstats import mode
from scipy.ndimage.morphology import binary_erosion as erode
from scipy.ndimage.morphology import binary_dilation as dilate
from scipy.ndimage import distance_transform_edt
from scipy.ndimage.measurements import label
from skimage import exposure
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import datetime as dt

### Models
# http://stackoverflow.com/questions/19695249/load-just-part-of-an-image-in-python
class Composite(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='composites')
	series = models.ForeignKey(Series, related_name='composites')

	# properties
	id_token = models.CharField(max_length=8)
	current_region_unique = models.CharField(max_length=8)
	current_zedge_unique = models.CharField(max_length=8)

	# methods
	def __str__(self):
		return '{}, {} > {}'.format(self.experiment.name, self.series.name, self.id_token)

	def save_data_file(self):
		# save data on all cell instances
		# data_file_name =
		# with op
		pass

	def get_or_create_data_file(self, root, file_name):

		# metadata
		template = self.templates.get(name='data')
		metadata = template.dict(file_name)

		if self.series.name == metadata['series']:
			data_file, data_file_created = self.data_files.get_or_create(experiment=self.experiment, series=self.series, template=template, id_token=metadata['id'], data_type=metadata['type'], url=join(root, file_name), file_name=file_name)
			return data_file, data_file_created, 'created.' if data_file_created else 'already exists.'
		else:
			return None, False, 'does not match series.'

	def shape(self, d=2):
		return self.series.shape(d)

	def create_zmod(self, R=5, delta_z=-8, sigma=5):
		# template
		template = self.templates.get(name='source') # SOURCE TEMPLATE

		# channels
		zmod_channel, zmod_channel_created = self.channels.get_or_create(name='-zmod')
		zmean_channel, zmean_channel_created = self.channels.get_or_create(name='-zmean')
		zbf_channel, zbf_channel_created = self.channels.get_or_create(name='-zbf')
		zcomp_channel, zcomp_channel_created = self.channels.get_or_create(name='-zcomp')

		# iterate over frames
		for t in range(self.series.ts):
			print('step01 | creating zmod, zmean, zbf, zcomp t{}/{}...'.format(t+1, self.series.ts), end='\r')

			# load gfp
			gfp_gon = self.gons.get(t=t, channel__name='0')
			gfp = exposure.rescale_intensity(gfp_gon.load() * 1.0)
			gfp = gf(gfp, sigma=sigma) # <<< SMOOTHING

			# load bf
			bf_gon = self.gons.get(t=t, channel__name='1')
			bf = exposure.rescale_intensity(bf_gon.load() * 1.0)

			# initialise images
			Z = np.zeros(self.series.shape(d=2), dtype=int)
			Zmean = np.zeros(self.series.shape(d=2))
			Zbf = np.zeros(self.series.shape(d=2))

			# loop over image
			Z = np.argmax(gfp, axis=2) + delta_z

			# outliers
			Z[Z<0] = 0
			Z[Z>self.series.zs-1] = self.series.zs-1

			# loop over levels
			for level in range(bf.shape[2]):
				bf[:,:,level] = convolve(bf[:,:,level], np.ones((R,R)))
				Zbf[Z==level] = bf[Z==level,level]

			Zmean = 1 - np.mean(gfp, axis=2) / np.max(gfp, axis=2)

			# images to channel gons
			zmod_gon, zmod_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=zmod_channel, t=t)
			zmod_gon.set_origin(0,0,0,t)
			zmod_gon.set_extent(self.series.rs, self.series.cs, 1)

			zmod_gon.array = Z
			zmod_gon.save_array(self.series.experiment.composite_path, template)
			zmod_gon.save()

			zmean_gon, zmean_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=zmean_channel, t=t)
			zmean_gon.set_origin(0,0,0,t)
			zmean_gon.set_extent(self.series.rs, self.series.cs, 1)

			zmean_gon.array = exposure.rescale_intensity(Zmean * 1.0)
			zmean_gon.save_array(self.series.experiment.composite_path, template)
			zmean_gon.save()

			zbf_gon, zbf_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=zbf_channel, t=t)
			zbf_gon.set_origin(0,0,0,t)
			zbf_gon.set_extent(self.series.rs, self.series.cs, 1)

			zbf_gon.array = Zbf
			zbf_gon.save_array(self.series.experiment.composite_path, template)
			zbf_gon.save()

	def create_selinummi(self, R=3):
		# template
		template = self.templates.get(name='source') # SOURCE TEMPLATE

		# channels
		bmod_channel, bmod_channel_created = self.channels.get_or_create(name='-bmod')

		# iterate over frames
		for t in range(self.series.ts):
			print('step01 | creating bmod t{}/{}...'.format(t+1, self.series.ts), end='\r')

			# load bf
			bf_gon = self.gons.get(t=t, channel__name='1')
			bf = exposure.rescale_intensity(bf_gon.load() * 1.0)

			# initialise images
			bmod = np.std(bf / np.dstack([np.max(bf, axis=2)] * bf.shape[2]), axis=2)

			# images to channel gons
			bmod_gon, bmod_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=bmod_channel, t=t)
			bmod_gon.set_origin(0,0,0,t)
			bmod_gon.set_extent(self.series.rs, self.series.cs, 1)

			bmod_gon.array = bmod
			bmod_gon.save_array(self.series.experiment.composite_path, template)
			bmod_gon.save()

	def create_max_gfp(self):
		# template
		template = self.templates.get(name='source') # SOURCE TEMPLATE

		# channels
		max_gfp_channel, max_gfp_channel_created = self.channels.get_or_create(name='-mgfp')

		# iterate over frames
		for t in range(self.series.ts):
			print('step01 | creating max_gfp t{}/{}...'.format(t+1, self.series.ts), end='\r')

			# load gfp
			gfp_gon = self.gons.get(t=t, channel__name='0')
			gfp = exposure.rescale_intensity(gfp_gon.load() * 1.0)
			gfp = gf(gfp, sigma=2) # <<< SMOOTHING

			# images to channel gons
			max_gfp_gon, max_gfp_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=max_gfp_channel, t=t)
			max_gfp_gon.set_origin(0,0,0,t)
			max_gfp_gon.set_extent(self.series.rs, self.series.cs, 1)

			max_gfp_gon.array = np.max(gfp, axis=2)
			max_gfp_gon.save_array(self.series.experiment.composite_path, template)
			max_gfp_gon.save()

	def create_bf_gfp(self, bf_ratio=0.1):
		# template
		template = self.templates.get(name='source') # SOURCE TEMPLATE

		# channels
		bfgfp_channel, bfgfp_channel_created = self.channels.get_or_create(name='-bfgfp')

		# iterate over frames
		for t in range(self.series.ts):
			print('step01 | creating bfgfp t{}/{}...'.format(t+1, self.series.ts), end='\r')

			# load bf
			zbf_gon = self.gons.get(t=t, channel__name='-zbf')
			zbf = exposure.rescale_intensity(zbf_gon.load() * 1.0)

			if len(zbf.shape)>2:
				if zbf.shape[2]>1:
					zbf = zbf[:,:,0]

			# load gfp
			mgfp_gon = self.gons.get(t=t, channel__name='-mgfp')
			mgfp = exposure.rescale_intensity(mgfp_gon.load() * 1.0)

			# mix
			bfgfp = mgfp * (1.0 - bf_ratio) + zbf * bf_ratio

			# images to channel gons
			bfgfp_gon, bfgfp_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=bfgfp_channel, t=t)
			bfgfp_gon.set_origin(0,0,0,t)
			bfgfp_gon.set_extent(self.series.rs, self.series.cs, 1)

			bfgfp_gon.array = bfgfp
			bfgfp_gon.save_array(self.series.experiment.composite_path, template)
			bfgfp_gon.save()

	def create_zedge(self, channel_unique_override):
		zedge_channel, zedge_channel_created = self.channels.get_or_create(name='-zedge')

		for t in range(self.series.ts):
			print('step02 | processing mod_zedge t{}/{}...'.format(t+1, self.series.ts), end='\r')

			zunique_mask = self.masks.get(channel__name__contains=channel_unique_override, t=t).load()
			zbf = exposure.rescale_intensity(self.gons.get(channel__name='-zbf', t=t).load() * 1.0)
			zedge = zbf.copy()

			if len(zedge.shape)>2:
				if zedge.shape[2]>1:
					zedge = zedge[:,:,0]

			binary_mask = zunique_mask>0
			outside_edge = distance_transform_edt(dilate(edge_image(binary_mask), iterations=4))
			outside_edge = 1.0 - exposure.rescale_intensity(outside_edge * 1.0)
			zedge *= outside_edge * outside_edge

			zedge_gon, zedge_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=zedge_channel, t=t)
			zedge_gon.set_origin(0,0,0,t)
			zedge_gon.set_extent(self.series.rs, self.series.cs, 1)

			zedge_gon.array = zedge.copy()
			zedge_gon.save_array(self.experiment.composite_path, self.templates.get(name='source'))
			zedge_gon.save()

		return zedge_channel

	def create_zunique(self):

		zunique_channel, zunique_channel_created = self.channels.get_or_create(name='-zunique')

		for t in range(self.series.ts):
			print('creating zunique t{}/{}'.format(t+1, self.series.ts), end='\r' if t<self.series.ts-1 else '\n')
			zmean = exposure.rescale_intensity(self.gons.get(channel__name='-zmean', t=t).load() * 1.0)
			zmod = exposure.rescale_intensity(self.gons.get(channel__name='-zmod', t=t).load() * 1.0)

			zunique = np.zeros(zmean.shape)
			for unique in np.unique(zmod):
				zunique[zmod==unique] = np.max(zmean[zmod==unique]) / np.sum(zmean)

			zunique = gf(zunique, sigma=3)

			if len(zunique.shape)>2:
				if zunique.shape[2]>1:
					zunique = zunique[:,:,0]

			zunique_gon, zunique_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=zunique_channel, t=t)
			zunique_gon.set_origin(0,0,0,t)
			zunique_gon.set_extent(self.series.rs, self.series.cs, 1)

			zunique_gon.array = zunique.copy()
			zunique_gon.save_array(self.experiment.composite_path, self.templates.get(name='source'))
			zunique_gon.save()

		return zunique_channel

	def create_tracking(self):

		tracking_channel, tracking_channel_created = self.channels.get_or_create(name='-tracking')

		if not exists(join(self.experiment.ij_path, self.series.name)):
			os.mkdir(join(self.experiment.ij_path, self.series.name))

		for t in range(self.series.ts):
			print('creating tracking t{}/{}'.format(t+1, self.series.ts), end='\r' if t<self.series.ts-1 else '\n')

			zbf = exposure.rescale_intensity(self.gons.get(channel__name='-zbf', t=t).load() * 1.0)

			if len(zbf.shape)>2:
				if zbf.shape[2]>1:
					zbf = zbf[:,:,0]

			gfp = exposure.rescale_intensity(self.gons.get(channel__name='0', t=t).load() * 1.0)

			gfp_projection = np.max(gfp, axis=2) # z projection of the gfp
			gfp_projection = gf(gfp_projection, sigma=1)

			tracking_img = gfp_projection * 0.5 + zbf * 0.5

			tracking_gon, tracking_gon_created = self.gons.get_or_create(experiment=self.experiment, series=self.series, channel=tracking_channel, t=t)
			tracking_gon.set_origin(0,0,0,t)
			tracking_gon.set_extent(self.series.rs, self.series.cs, 1)

			tracking_gon.array = tracking_img.copy()
			tracking_gon.save_array(join(self.experiment.ij_path, self.series.name), self.templates.get(name='source'))
			tracking_gon.save()

	def create_tile(self, channel_unique_override, top_channel='-zbf', side_channel='-zunique', main_channel='-zedge', region_list=[]):
		tile_path = join(self.experiment.video_path, 'tile', self.series.name, '{}-{}'.format(dt.datetime.now().strftime('%Y-%m-%d-%H-%M'), channel_unique_override))
		if not exists(tile_path):
			os.makedirs(tile_path)

		for t in range(self.series.ts):
			zbf_gon = self.gons.get(t=t, channel__name=top_channel)
			zcomp_gon = self.gons.get(t=t, channel__name=side_channel)
			zmean_gon = self.gons.get(t=t, channel__name=main_channel)
			mask_mask = self.masks.get(t=t, channel__name__contains=channel_unique_override)

			zbf = zbf_gon.load()
			zbf = zbf if len(zbf.shape)==2 or (len(zbf.shape)==2 and zbf.shape[2]==2) else np.squeeze(zbf[:,:,0])
			zcomp = zcomp_gon.load()
			zcomp = zcomp if len(zcomp.shape)==2 or (len(zcomp.shape)==2 and zcomp.shape[2]==2) else np.squeeze(zcomp[:,:,0])
			zmean = zmean_gon.load()
			zmean = zmean if len(zmean.shape)==2 or (len(zmean.shape)==2 and zmean.shape[2]==2) else np.squeeze(zmean[:,:,0])
			mask = mask_mask.load()

			# remove cells in regions
			if region_list:
				for cell_mask in mask_mask.cell_masks.exclude(region__name__in=region_list):
					mask[mask==cell_mask.gray_value_id] = 0 # delete masks from image if not in regions

			mask_outline = mask_edge_image(mask)

			zbf_mask_r = zbf.copy()
			zbf_mask_g = zbf.copy()
			zbf_mask_b = zbf.copy()

			zcomp_mask_r = zcomp.copy()
			zcomp_mask_g = zcomp.copy()
			zcomp_mask_b = zcomp.copy()

			# drawing
			# 1. draw outlines in red channel
			zbf_mask_r[mask_outline>0] = 255
			zbf_mask_g[mask_outline>0] = 0
			zbf_mask_b[mask_outline>0] = 0
			zcomp_mask_r[mask_outline>0] = 255
			zcomp_mask_g[mask_outline>0] = 0
			zcomp_mask_b[mask_outline>0] = 0

			# draw markers
			markers = self.markers.filter(track_instance__t=t, track__cell__isnull=False)
			for marker in markers:
				if hasattr(marker.track_instance, 'cell_instance'):
					if marker.track_instance.cell_instance.masks.filter(channel__name__contains=channel_unique_override):
						if region_list==[] or (marker.track_instance.cell_instance.masks.get(channel__name__contains=channel_unique_override).region is not None and marker.track_instance.cell_instance.masks.get(channel__name__contains=channel_unique_override).region.name in region_list):
							# 2. draw markers in blue channel
							zbf_mask_r[marker.r-2:marker.r+3,marker.c-2:marker.c+3] = 0
							zbf_mask_g[marker.r-2:marker.r+3,marker.c-2:marker.c+3] = 0
							zbf_mask_b[marker.r-2:marker.r+3,marker.c-2:marker.c+3] = 255
							zcomp_mask_r[marker.r-2:marker.r+3,marker.c-2:marker.c+3] = 0
							zcomp_mask_g[marker.r-2:marker.r+3,marker.c-2:marker.c+3] = 0
							zcomp_mask_b[marker.r-2:marker.r+3,marker.c-2:marker.c+3] = 255

							# 3. draw text in green channel
							blank_slate = np.zeros(zbf.shape)
							blank_slate_img = Image.fromarray(blank_slate)
							draw = ImageDraw.Draw(blank_slate_img)
							draw.text((marker.c+5, marker.r+5), '{}'.format(marker.track.cell.pk), font=ImageFont.load_default(), fill='rgb(0,0,255)')
							blank_slate = np.array(blank_slate_img)

							zbf_mask_r[blank_slate>0] = 0
							zbf_mask_g[blank_slate>0] = 255
							zbf_mask_b[blank_slate>0] = 0
							zcomp_mask_r[blank_slate>0] = 0
							zcomp_mask_g[blank_slate>0] = 255
							zcomp_mask_b[blank_slate>0] = 0

			# draw regions
			for region_instance in self.series.region_instances.filter(region_track_instance__t=t):
				# load mask
				mask = region_instance.masks.all()[0].load()
				# get mask outline
				mask_edge = edge_image(mask)

				# draw outlines in blue channel
				zbf_mask_r[mask_edge>0] = 0
				zbf_mask_g[mask_edge>0] = 0
				zbf_mask_b[mask_edge>0] = 255
				zcomp_mask_r[mask_edge>0] = 0
				zcomp_mask_g[mask_edge>0] = 0
				zcomp_mask_b[mask_edge>0] = 255

			# tile zbf, zbf_mask, zcomp, zcomp_mask
			top_half = np.concatenate((np.dstack([zbf, zbf, zbf]), np.dstack([zbf_mask_r, zbf_mask_g, zbf_mask_b])), axis=0)
			bottom_half = np.concatenate((np.dstack([zmean, zmean, zmean]), np.dstack([zcomp_mask_r, zcomp_mask_g, zcomp_mask_b])), axis=0)
			whole = np.concatenate((top_half, bottom_half), axis=1)

			imsave(join(tile_path, 'tile_{}_s{}_marker-{}_t{}.tiff'.format(self.experiment.name, self.series.name, channel_unique_override, str_value(t, self.series.ts))), whole)

	def create_region_tile(self, channel_unique_override, top_channel='-zbf', side_channel='-zunique', main_channel='-zunique'):
		tile_path = join(self.experiment.video_path, 'regions', self.series.name, channel_unique_override)
		if not exists(tile_path):
			os.makedirs(tile_path)

		for t in range(self.series.ts):
			zbf_gon = self.gons.get(t=t, channel__name=top_channel)
			zcomp_gon = self.gons.get(t=t, channel__name=side_channel)
			zmean_gon = self.gons.get(t=t, channel__name=main_channel)

			zbf = zbf_gon.load()
			zbf = zbf if len(zbf.shape)==2 or (len(zbf.shape)==2 and zbf.shape[2]==2) else np.squeeze(zbf[:,:,0])
			zcomp = zcomp_gon.load()
			zcomp = zcomp if len(zcomp.shape)==2 or (len(zcomp.shape)==2 and zcomp.shape[2]==2) else np.squeeze(zcomp[:,:,0])
			zmean = zmean_gon.load()
			zmean = zmean if len(zmean.shape)==2 or (len(zmean.shape)==2 and zmean.shape[2]==2) else np.squeeze(zmean[:,:,0])

			zbf_mask_r = zbf.copy()
			zbf_mask_g = zbf.copy()
			zbf_mask_b = zbf.copy()

			zcomp_mask_r = zcomp.copy()
			zcomp_mask_g = zcomp.copy()
			zcomp_mask_b = zcomp.copy()

			# draw regions
			for region_instance in self.series.region_instances.filter(region_track_instance__t=t):
				# load mask
				mask = region_instance.masks.all()[0].load()
				# get mask outline
				mask_edge = edge_image(mask)

				# draw outlines in blue channel
				zbf_mask_r[mask_edge>0] = 0
				zbf_mask_g[mask_edge>0] = 0
				zbf_mask_b[mask_edge>0] = 255
				zcomp_mask_r[mask_edge>0] = 0
				zcomp_mask_g[mask_edge>0] = 0
				zcomp_mask_b[mask_edge>0] = 255

			# tile zbf, zbf_mask, zcomp, zcomp_mask
			top_half = np.concatenate((np.dstack([zbf, zbf, zbf]), np.dstack([zbf_mask_r, zbf_mask_g, zbf_mask_b])), axis=0)
			bottom_half = np.concatenate((np.dstack([zmean, zmean, zmean]), np.dstack([zcomp_mask_r, zcomp_mask_g, zcomp_mask_b])), axis=0)
			whole = np.concatenate((top_half, bottom_half), axis=1)

			imsave(join(tile_path, 'tile_{}_s{}_region-{}_t{}.tiff'.format(self.experiment.name, self.series.name, channel_unique_override, str_value(t, self.series.ts))), whole)

class Template(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='templates')

	# properties
	name = models.CharField(max_length=255)
	rx = models.CharField(max_length=255)
	rv = models.CharField(max_length=255)

	# methods
	def __str__(self):
		return '{}: {}'.format(self.name, self.rx)

	def match(self, string):
		return re.match(self.rx, string)

	def dict(self, string):
		return self.match(string).groupdict()

### GONS
class Channel(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='channels')

	# properties
	name = models.CharField(max_length=255)

	# methods
	def __str__(self):
		return '{} > {}'.format(self.composite.id_token, self.name)

	def segment(self, marker_channel_name='-zunique', threshold_correction_factor=1.2, background=True):

		unique = random_string() # defines a single identifier for this run
		unique_key = '{}{}-{}'.format(marker_channel_name, self.name, unique)

		# setup
		print('getting marker channel')
		marker_channel = self.composite.channels.get(name=marker_channel_name)

		# 1. create primary from markers with marker_channel
		print('running primary')
		marker_channel_primary_name = marker_channel.primary(unique=unique)

		# 2. create pipeline and run
		print('run pipeline')
		self.composite.experiment.save_marker_pipeline(series_name=self.composite.series.name, primary_channel_name=marker_channel_primary_name, secondary_channel_name=self.name, threshold_correction_factor=threshold_correction_factor, background=background, unique=unique, unique_key=unique_key)
		self.composite.experiment.run_pipeline(series_ts=self.composite.series.ts)

		print('import masks')
		# 3. import masks and create new mask channel
		cp_out_file_list = [f for f in os.listdir(self.composite.experiment.cp_path) if (unique_key in f and '.tiff' in f)]
		# make new channel that gets put in mask path
		cp_template = self.composite.templates.get(name='cp')
		mask_template = self.composite.templates.get(name='mask')
		mask_channel = self.composite.mask_channels.create(name=unique_key)
		region_mask_channel = None
		if self.composite.mask_channels.all() and self.composite.current_region_unique:
			region_mask_channel = self.composite.mask_channels.get(name__contains=self.composite.current_region_unique)

		for cp_out_file in cp_out_file_list:
			array = imread(join(self.composite.experiment.cp_path, cp_out_file))
			metadata = cp_template.dict(cp_out_file)
			mask_channel.get_or_create_mask(array, int(metadata['t']))

		print('import data files')
		# 4. import datafiles and access data
		data_file_list = [f for f in os.listdir(self.composite.experiment.cp_path) if (unique in f and '.csv' in f)]
		for df_name in data_file_list:
			data_file, data_file_created, status = self.composite.get_or_create_data_file(self.composite.experiment.cp_path, df_name)

		# 5. create cells and cell instances from tracks
		cell_data_file = self.composite.data_files.get(id_token=unique, data_type='Cells')
		data = cell_data_file.load()

		# load masks and associate with grayscale id's
		for t in range(self.composite.series.ts):
			mask_mask = mask_channel.masks.get(t=t)
			mask = mask_mask.load()

			# load zmod image
			zmod_gon = self.composite.gons.get(t=t, channel__name='-zmod')
			zmod = exposure.rescale_intensity(zmod_gon.load() * 1.0) * self.composite.series.zs

			# load region mask
			if region_mask_channel is not None:
				region_mask_mask = region_mask_channel.masks.get(t=t)
				region_mask = region_mask_mask.load()

			t_data = list(filter(lambda d: int(d['ImageNumber'])-1==t, data))

			markers = marker_channel.markers.filter(track_instance__t=t)
			for marker in markers:
				# 1. create cell
				cell, cell_created = self.composite.experiment.cells.get_or_create(series=self.composite.series, track=marker.track)

				# 2. create cell instance
				cell_instance, cell_instance_created = cell.instances.get_or_create(experiment=cell.experiment,
																																						series=cell.series,
																																						track_instance=marker.track_instance,
																																						t=marker.track_instance.t)

				# 3. create cell mask
				gray_value_id = mask[marker.r, marker.c]
				region_instance = None
				if region_mask_channel is not None:
					region_gray_value_id = region_mask[marker.r, marker.c]
					region_instance = self.composite.series.region_instances.filter(region_track_instance__t=t, mode_gray_value_id=region_gray_value_id)
					if region_instance:
						region_instance = region_instance[0]
					else:
						region_instance = None
						for ri in self.composite.series.region_instances.filter(region_track_instance__t=t):
							gray_value_ids = [ri_mask.gray_value_id for ri_mask in ri.masks.all()]
							if region_instance is None and region_gray_value_id in gray_value_ids:
								region_instance = ri

				if gray_value_id!=0:
					cell_mask = cell_instance.masks.create(experiment=cell.experiment,
																								 series=cell.series,
																								 cell=cell,
																								 region=region_instance.region if region_instance is not None else None,
																								 region_instance=region_instance if region_instance is not None else None,
																								 channel=mask_channel,
																								 mask=mask_mask,
																								 marker=marker,
																								 gray_value_id=gray_value_id)

					cell_mask_data = list(filter(lambda d: int(d['ObjectNumber'])==cell_mask.gray_value_id, t_data))[0]

					# get z
					zmod_mask = zmod[mask==cell_mask.gray_value_id]
					average_z_position = int(zmod_mask.mean())

					# 4. assign data
					cell_mask.r = cell_mask.marker.r
					cell_mask.c = cell_mask.marker.c
					cell_mask.z = average_z_position
					cell_mask.t = t
					cell_mask.AreaShape_Area = float(cell_mask_data['AreaShape_Area']) if str(cell_mask_data['AreaShape_Area']) != 'nan' else -1.0
					cell_mask.AreaShape_Compactness = float(cell_mask_data['AreaShape_Compactness']) if str(cell_mask_data['AreaShape_Compactness']) != 'nan' else -1.0
					cell_mask.AreaShape_Eccentricity = float(cell_mask_data['AreaShape_Eccentricity']) if str(cell_mask_data['AreaShape_Eccentricity']) != 'nan' else -1.0
					cell_mask.AreaShape_EulerNumber = float(cell_mask_data['AreaShape_EulerNumber']) if str(cell_mask_data['AreaShape_EulerNumber']) != 'nan' else -1.0
					cell_mask.AreaShape_Extent = float(cell_mask_data['AreaShape_Extent']) if str(cell_mask_data['AreaShape_Extent']) != 'nan' else -1.0
					cell_mask.AreaShape_FormFactor = float(cell_mask_data['AreaShape_FormFactor']) if str(cell_mask_data['AreaShape_FormFactor']) != 'nan' else -1.0
					cell_mask.AreaShape_MajorAxisLength = float(cell_mask_data['AreaShape_MajorAxisLength']) if str(cell_mask_data['AreaShape_MajorAxisLength']) != 'nan' else -1.0
					cell_mask.AreaShape_MaxFeretDiameter = float(cell_mask_data['AreaShape_MaxFeretDiameter']) if str(cell_mask_data['AreaShape_MaxFeretDiameter']) != 'nan' else -1.0
					cell_mask.AreaShape_MaximumRadius = float(cell_mask_data['AreaShape_MaximumRadius']) if str(cell_mask_data['AreaShape_MaximumRadius']) != 'nan' else -1.0
					cell_mask.AreaShape_MeanRadius = float(cell_mask_data['AreaShape_MeanRadius']) if str(cell_mask_data['AreaShape_MeanRadius']) != 'nan' else -1.0
					cell_mask.AreaShape_MedianRadius = float(cell_mask_data['AreaShape_MedianRadius']) if str(cell_mask_data['AreaShape_MedianRadius']) != 'nan' else -1.0
					cell_mask.AreaShape_MinFeretDiameter = float(cell_mask_data['AreaShape_MinFeretDiameter']) if str(cell_mask_data['AreaShape_MinFeretDiameter']) != 'nan' else -1.0
					cell_mask.AreaShape_MinorAxisLength = float(cell_mask_data['AreaShape_MinorAxisLength']) if str(cell_mask_data['AreaShape_MinorAxisLength']) != 'nan' else -1.0
					cell_mask.AreaShape_Orientation = float(cell_mask_data['AreaShape_Orientation']) if str(cell_mask_data['AreaShape_Orientation']) != 'nan' else -1.0
					cell_mask.AreaShape_Perimeter = float(cell_mask_data['AreaShape_Perimeter']) if str(cell_mask_data['AreaShape_Perimeter']) != 'nan' else -1.0
					cell_mask.AreaShape_Solidity = float(cell_mask_data['AreaShape_Solidity']) if str(cell_mask_data['AreaShape_Solidity']) != 'nan' else -1.0
					cell_mask.Location_Center_X = float(cell_mask_data['Location_Center_X']) if str(cell_mask_data['Location_Center_X']) != 'nan' else 0
					cell_mask.Location_Center_Y = float(cell_mask_data['Location_Center_Y']) if str(cell_mask_data['Location_Center_Y']) != 'nan' else 0
					cell_mask.AreaShape_Zernike_0_0 = float(cell_mask_data['AreaShape_Zernike_0_0']) if str(cell_mask_data['AreaShape_Zernike_0_0']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_1_1 = float(cell_mask_data['AreaShape_Zernike_1_1']) if str(cell_mask_data['AreaShape_Zernike_1_1']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_2_0 = float(cell_mask_data['AreaShape_Zernike_2_0']) if str(cell_mask_data['AreaShape_Zernike_2_0']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_2_2 = float(cell_mask_data['AreaShape_Zernike_2_2']) if str(cell_mask_data['AreaShape_Zernike_2_2']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_3_1 = float(cell_mask_data['AreaShape_Zernike_3_1']) if str(cell_mask_data['AreaShape_Zernike_3_1']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_3_3 = float(cell_mask_data['AreaShape_Zernike_3_3']) if str(cell_mask_data['AreaShape_Zernike_3_3']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_4_0 = float(cell_mask_data['AreaShape_Zernike_4_0']) if str(cell_mask_data['AreaShape_Zernike_4_0']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_4_2 = float(cell_mask_data['AreaShape_Zernike_4_2']) if str(cell_mask_data['AreaShape_Zernike_4_2']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_4_4 = float(cell_mask_data['AreaShape_Zernike_4_4']) if str(cell_mask_data['AreaShape_Zernike_4_4']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_5_1 = float(cell_mask_data['AreaShape_Zernike_5_1']) if str(cell_mask_data['AreaShape_Zernike_5_1']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_5_3 = float(cell_mask_data['AreaShape_Zernike_5_3']) if str(cell_mask_data['AreaShape_Zernike_5_3']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_5_5 = float(cell_mask_data['AreaShape_Zernike_5_5']) if str(cell_mask_data['AreaShape_Zernike_5_5']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_6_0 = float(cell_mask_data['AreaShape_Zernike_6_0']) if str(cell_mask_data['AreaShape_Zernike_6_0']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_6_2 = float(cell_mask_data['AreaShape_Zernike_6_2']) if str(cell_mask_data['AreaShape_Zernike_6_2']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_6_4 = float(cell_mask_data['AreaShape_Zernike_6_4']) if str(cell_mask_data['AreaShape_Zernike_6_4']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_6_6 = float(cell_mask_data['AreaShape_Zernike_6_6']) if str(cell_mask_data['AreaShape_Zernike_6_6']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_7_1 = float(cell_mask_data['AreaShape_Zernike_7_1']) if str(cell_mask_data['AreaShape_Zernike_7_1']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_7_3 = float(cell_mask_data['AreaShape_Zernike_7_3']) if str(cell_mask_data['AreaShape_Zernike_7_3']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_7_5 = float(cell_mask_data['AreaShape_Zernike_7_5']) if str(cell_mask_data['AreaShape_Zernike_7_5']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_7_7 = float(cell_mask_data['AreaShape_Zernike_7_7']) if str(cell_mask_data['AreaShape_Zernike_7_7']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_8_0 = float(cell_mask_data['AreaShape_Zernike_8_0']) if str(cell_mask_data['AreaShape_Zernike_8_0']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_8_2 = float(cell_mask_data['AreaShape_Zernike_8_2']) if str(cell_mask_data['AreaShape_Zernike_8_2']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_8_4 = float(cell_mask_data['AreaShape_Zernike_8_4']) if str(cell_mask_data['AreaShape_Zernike_8_4']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_8_6 = float(cell_mask_data['AreaShape_Zernike_8_6']) if str(cell_mask_data['AreaShape_Zernike_8_6']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_8_8 = float(cell_mask_data['AreaShape_Zernike_8_8']) if str(cell_mask_data['AreaShape_Zernike_8_8']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_9_1 = float(cell_mask_data['AreaShape_Zernike_9_1']) if str(cell_mask_data['AreaShape_Zernike_9_1']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_9_3 = float(cell_mask_data['AreaShape_Zernike_9_3']) if str(cell_mask_data['AreaShape_Zernike_9_3']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_9_5 = float(cell_mask_data['AreaShape_Zernike_9_5']) if str(cell_mask_data['AreaShape_Zernike_9_5']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_9_7 = float(cell_mask_data['AreaShape_Zernike_9_7']) if str(cell_mask_data['AreaShape_Zernike_9_7']) != 'nan' else 0.0
					cell_mask.AreaShape_Zernike_9_9 = float(cell_mask_data['AreaShape_Zernike_9_9']) if str(cell_mask_data['AreaShape_Zernike_9_9']) != 'nan' else 0.0
					# cell_mask.find_protrusions()
					cell_mask.save()

		# 6. calculate cell velocities
		print('calculating velocities...')
		for cell in self.composite.experiment.cells.all():
			cell.calculate_velocities(unique)
			cell.calculate_confidences()

		return unique

	def segment_regions(self, region_marker_channel_name='-zbf', threshold_correction_factor=1.2, background=True):

		unique = random_string() # defines a single identifier for this run
		unique_key = '{}{}-{}'.format(region_marker_channel_name, self.name, unique)

		# setup
		region_marker_channel = self.composite.channels.get(name=region_marker_channel_name)

		# 1. create region primary
		print('running primary')
		region_marker_channel_primary_name = region_marker_channel.region_primary(unique=unique)

		# 2. create pipeline and run
		self.composite.experiment.save_region_pipeline(series_name=self.composite.series.name, primary_channel_name=region_marker_channel_primary_name, secondary_channel_name=self.name, threshold_correction_factor=threshold_correction_factor, background=background, unique=unique, unique_key=unique_key)
		self.composite.experiment.run_pipeline(series_ts=self.composite.series.ts, key='regions')

		# 3. import masks
		print('import masks')
		cp_out_file_list = [f for f in os.listdir(self.composite.experiment.cp_path) if (unique_key in f and '.tiff' in f)]
		# make new channel that gets put in mask path
		cp_template = self.composite.templates.get(name='cp')
		mask_template = self.composite.templates.get(name='mask')
		mask_channel = self.composite.mask_channels.create(name=unique_key)

		for cp_out_file in cp_out_file_list:
			array = imread(join(self.composite.experiment.cp_path, cp_out_file))
			metadata = cp_template.dict(cp_out_file)
			mask_channel.get_or_create_mask(array, int(metadata['t']))

		# 4. create regions and tracks
		print('create regions and tracks...')
		mask_mask = mask_channel.masks.get(t=0) # this is only the first mask. All others will have the same gray values.
		mask = mask_mask.load()

		for t in range(self.composite.series.ts):
			# mask_mask = mask_channel.masks.get(t=t) # this can be used if the regions are properly tracked.
			# mask = mask_mask.load()

			region_markers = region_marker_channel.region_markers.filter(region_track_instance__t=t)
			for region_marker in region_markers:
				# 1. create cell
				region, region_created = self.composite.experiment.regions.get_or_create(series=self.composite.series, region_track=region_marker.region_track, name=region_marker.region_track.name)

				# 2. create cell instance
				region_instance, region_instance_created = region.instances.get_or_create(experiment=region.experiment,
																																									series=region.series,
																																									region_track_instance=region_marker.region_track_instance)

				# 3. create cell mask
				# gray value id is only taken from the first frame since the regions are tracked
				# and will retain their id.
				gray_value_id = mask[region_marker.r, region_marker.c]
				region_mask = region_instance.masks.create(experiment=region.experiment,
																									 series=region.series,
																									 region=region,
																									 mask=mask_mask)
				region_mask.gray_value_id = gray_value_id
				region_mask.save()

			for region_track_instance in region_marker_channel.region_track_instances.filter(t=t):
				gray_value_ids = [region_mask.gray_value_id for region_mask in region_track_instance.region_instance.masks.filter(mask=mask_mask)]
				region_track_instance.region_instance.mode_gray_value_id = int(mode(gray_value_ids)[0][0])
				region_track_instance.region_instance.save()

		self.composite.current_region_unique = unique
		self.composite.save()

		return unique

	# methods
	def region_labels(self):
		return np.unique([region_marker.region_track.name for region_marker in self.region_markers.all()])

	def get_or_create_gon(self, array, t, r=0, c=0, z=0, rs=None, cs=None, zs=1, path=None):
		# self.defaults
		rs = self.composite.series.rs if rs is None else rs
		cs = self.composite.series.cs if cs is None else cs
		path = self.composite.experiment.composite_path if path is None else path

		# build
		gon, gon_created = self.gons.get_or_create(experiment=self.composite.experiment, series=self.composite.series, composite=self.composite, t=t)
		gon.set_origin(r,c,z,t)
		gon.set_extent(rs,cs,zs)

		gon.array = array
		gon.save_array(path, self.composite.templates.get(name='source'))
		gon.save()

		return gon, gon_created

	def primary(self, unique=''):
		if self.markers.count()!=0:
			channel_name = ''

			# 1. loop through time series
			marker_channel, marker_channel_created = self.composite.channels.get_or_create(name='{}-primary-{}'.format(self.name, unique))

			for t in range(self.composite.series.ts):
				print('primary for composite {} {} {} channel {} | t{}/{}'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name, t+1, self.composite.series.ts), end='\n' if t==self.composite.series.ts-1 else '\r')

				# load all markers for this frame
				markers = self.markers.filter(track_instance__t=t)

				# blank image
				blank = np.zeros(self.composite.shape())

				for i, marker in enumerate(markers):

					blank[marker.r-3:marker.r+2, marker.c-3:marker.c+2] = 255

				blank_gon, blank_gon_created = marker_channel.get_or_create_gon(blank, t)

			return marker_channel.name

		else:
			print('primary for composite {} {} {} channel {} | no markers have been defined.'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name))

	def region_primary(self, unique=''):
		if self.region_markers.count()!=0:

			# 1. loop through time series
			marker_channel, marker_channel_created = self.composite.channels.get_or_create(name='{}-regionprimary-{}'.format(self.name, unique))

			for t in range(self.composite.series.ts):
				print('primary for composite {} {} {} channel {} | t{}/{}'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name, t+1, self.composite.series.ts), end='\n' if t==self.composite.series.ts-1 else '\r')
				# blank image
				blank = np.ones(self.composite.shape())

				for region_track_name in set([rm.region_track.name for rm in self.region_markers.all()]):

					region_markers = self.region_markers.filter(region_track_instance__t=t, region_track__name=region_track_name)

					previous_region_marker = None
					first_region_marker = None
					for i, region_marker in enumerate(list(sorted(region_markers, key=lambda rm: rm.region_track_index))):

						img = Image.fromarray(blank)
						draw = ImageDraw.Draw(img)

						if previous_region_marker is not None:
							draw.line([(previous_region_marker.c, previous_region_marker.r), (region_marker.c, region_marker.r)], fill=0, width=5)

						previous_region_marker = region_marker
						if first_region_marker is None:
							first_region_marker = region_marker if region_marker.region_track_index==1 else None

						if i==len(region_markers)-1:
							draw.line([(region_marker.c, region_marker.r), (first_region_marker.c, first_region_marker.r)], fill=0, width=5)

						blank = np.array(img)

				# fill in holes in blank
				blank, n = label(blank)
				blank[blank==blank[0,0]] = 0

				# create gon
				blank_gon, blank_gon_created = marker_channel.get_or_create_gon(blank, t)

			return marker_channel.name

		else:
			print('region primary for composite {} {} {} channel {} | no region markers have been defined.'.format(self.composite.experiment.name, self.composite.series.name, self.composite.id_token, self.name))

	def outline(self, outline_channel=None):
		'''
		Use cells to overlay outlines on images. Take masks from outline_channel or same channel if None.
		'''

		pass

		# if outline_channel is None:
		#
		#
		# else:

	def tile_labels_and_outlines(self, label_channel=None):
		pass

class Gon(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='gons')
	series = models.ForeignKey(Series, related_name='gons')
	composite = models.ForeignKey(Composite, related_name='gons', null=True)
	template = models.ForeignKey(Template, related_name='gons', null=True)
	channel = models.ForeignKey(Channel, related_name='gons')
	gon = models.ForeignKey('self', related_name='gons', null=True)

	# properties
	id_token = models.CharField(max_length=8, default='')

	# 1. origin
	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	z = models.IntegerField(default=0)
	t = models.IntegerField(default=-1)

	# 2. extent
	rs = models.IntegerField(default=-1)
	cs = models.IntegerField(default=-1)
	zs = models.IntegerField(default=1)

	# 3. data
	array = None

	# methods
	def set_origin(self, r, c, z, t):
		self.r = r
		self.c = c
		self.z = z
		self.t = t
		self.save()

	def set_extent(self, rs, cs, zs):
		self.rs = rs
		self.cs = cs
		self.zs = zs
		self.save()

	def shape(self):
		if self.zs==1:
			return (self.rs, self.cs)
		else:
			return (self.rs, self.cs, self.zs)

	def t_str(self):
		return str('0'*(len(str(self.series.ts)) - len(str(self.t))) + str(self.t))

	def z_str(self, z=None):
		return str('0'*(len(str(self.series.zs)) - len(str(self.z if z is None else z))) + str(self.z if z is None else z))

	def load(self):
		self.array = []
		for path in self.paths.order_by('z'):
			array = imread(path.url)
			self.array.append(array)
		self.array = np.dstack(self.array).squeeze() # remove unnecessary dimensions
		return self.array

	def save_array(self, root, template):
		# 1. iterate through planes in bulk
		# 2. for each plane, save plane based on root, template
		# 3. create path with url and add to gon

		if not exists(root):
			os.makedirs(root)

		file_name = template.rv.format(self.experiment.name, self.series.name, self.channel.name, str_value(self.t, self.series.ts), '{}')
		url = join(root, file_name)

		if len(self.array.shape)==2:
			imsave(url.format(str_value(self.z, self.series.zs)), self.array)
			self.paths.create(composite=self.composite if self.composite is not None else self.gon.composite, channel=self.channel, template=template, url=url.format(str_value(self.z, self.series.zs)), file_name=file_name.format(str_value(self.z, self.series.zs)), t=self.t, z=self.z)

		else:
			for z in range(self.array.shape[2]):
				plane = self.array[:,:,z].copy()

				imsave(url.format(str_value(z+self.z, self.series.zs)), plane) # z level is offset by that of original gon.
				self.paths.create(composite=self.composite, channel=self.channel, template=template, url=url.format(str_value(self.z, self.series.zs)), file_name=file_name.format(str_value(self.z, self.series.zs)), t=self.t, z=z+self.z)

				# create gons
				gon = self.gons.create(experiment=self.composite.experiment, series=self.composite.series, channel=self.channel, template=template)
				gon.set_origin(self.r, self.c, z, self.t)
				gon.set_extent(self.rs, self.cs, 1)

				gon.array = plane.copy().squeeze()

				gon.save_array(self.experiment.composite_path, template)
				gon.save()

	def segment_primary(self, min_size, max_size):

		img = self.load().astype(np.float64) / 255.0

		# 1. threshold image
		binary_image = threshold_image(img)

		# 2. fill background holes in foreground objects
		def size_fn(size, is_foreground):
			return size < max_size
		binary_image = fill_labeled_holes(binary_image, size_fn=size_fn)

		# 3. perform recognition
		labeled_image, object_count = scipy.ndimage.label(binary_image, np.ones((3,3), bool))
		labeled_image, object_count, maxima_suppression_size, LoG_threshold, LoG_filter_diameter = separate_neighboring_objects(img, labeled_image, object_count, min_size, max_size)

		# 4. fill holes again
		labeled_image = fill_labeled_holes(labeled_image)
		return labeled_image, object_count

		# 5. create objects

	def segment_secondary(self, marker_channel_name):

		# 1. load image
		img = self.load().astype(np.float64) / 255.0
		mask = np.ones(img.shape)

		# 2. get primary objects
		labels_in = np.zeros(img.shape, dtype=float)
		marker_pks = np.array([marker.pk for marker in self.gon.composite.markers.filter(channel__name=marker_channel_name, track_instance__t=self.t)])
		for marker in self.gon.composite.markers.filter(channel__name=marker_channel_name, track_instance__t=self.t):
			labels_in[marker.r-3:marker.r+2, marker.c-3:marker.c+2] = marker.pk / marker_pks.max()

		objects_segmented = labels_in.copy()

		labels_touching_edge = np.hstack((labels_in[0,:], labels_in[-1,:], labels_in[:,0], labels_in[:,-1]))
		labels_touching_edge = np.unique(labels_touching_edge)
		is_touching = np.zeros(np.max(labels_in)+1, bool)
		is_touching[labels_touching_edge.astype(int)] = True
		is_touching = is_touching[labels_in.astype(int)]

		labels_in[(~ is_touching) & (objects_segmented == 0)] = 0 ### PRIMARY OBJECTS

		# 3. threshold image to be segmented
		thresholded_image = threshold_image(img)

		# 5. actually do segmentation
		labels_out, distance = propagate(img, labels_in, thresholded_image, 0.01)
		small_removed_segmented_out = fill_labeled_holes(labels_out)

		segmented_out = filter_labels(small_removed_segmented_out, objects_segmented)

		return segmented_out

### GON STRUCTURE AND MODIFICATION ###
class Path(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='paths')
	gon = models.ForeignKey(Gon, related_name='paths')
	channel = models.ForeignKey(Channel, related_name='paths')
	template = models.ForeignKey(Template, related_name='paths')

	# properties
	url = models.CharField(max_length=255)
	file_name = models.CharField(max_length=255)
	t = models.IntegerField(default=0)
	z = models.IntegerField(default=0)

	# methods
	def __str__(self):
		return '{}: {}'.format(self.composite.id_token, self.file_name)

	def load(self):
		return imread(self.url)

### MASKS
class MaskChannel(models.Model):
	# connections
	composite = models.ForeignKey(Composite, related_name='mask_channels')

	# properties
	name = models.CharField(max_length=255)

	# methods
	def __str__(self):
		return 'mask {} > {}'.format(self.composite.id_token, self.name)

	def get_or_create_mask(self, array, t, r=0, c=0, z=0, rs=None, cs=None, path=None):
		# self.defaults
		rs = self.composite.series.rs if rs is None else rs
		cs = self.composite.series.cs if cs is None else cs
		path = self.composite.experiment.composite_path if path is None else path

		# build
		mask, mask_created = self.masks.get_or_create(experiment=self.composite.experiment, series=self.composite.series, composite=self.composite, t=t)
		mask.set_origin(r,c,z,t)
		mask.set_extent(rs,cs)

		mask.array = array
		mask.save_array(path, self.composite.templates.get(name='mask'))
		mask.save()

		return mask, mask_created

class Mask(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='masks')
	series = models.ForeignKey(Series, related_name='masks')
	composite = models.ForeignKey(Composite, related_name='masks', null=True)
	channel = models.ForeignKey(MaskChannel, related_name='masks')
	template = models.ForeignKey(Template, related_name='masks', null=True)

	# properties
	id_token = models.CharField(max_length=8, default='')
	url = models.CharField(max_length=255)
	file_name = models.CharField(max_length=255)

	# 1. origin
	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	z = models.IntegerField(default=0)
	t = models.IntegerField(default=-1)

	# 2. extent
	rs = models.IntegerField(default=-1)
	cs = models.IntegerField(default=-1)

	# 3. data
	array = None

	# methods
	def set_origin(self, r, c, z, t):
		self.r = r
		self.c = c
		self.z = z
		self.t = t
		self.save()

	def set_extent(self, rs, cs):
		self.rs = rs
		self.cs = cs
		self.save()

	def shape(self):
		return (self.rs, self.cs)

	def t_str(self):
		return str('0'*(len(str(self.series.ts)) - len(str(self.t))) + str(self.t))

	def load(self):
		array = imread(self.url)
		self.array = (exposure.rescale_intensity(array * 1.0) * (len(np.unique(array)) - 1)).astype(int) # rescale to contain integer grayscale id's.
		return self.array

	def save_array(self, root, template):
		# 1. iterate through planes in bulk
		# 2. for each plane, save plane based on root, template
		# 3. create path with url and add to gon

		if not exists(root):
			os.makedirs(root)

		self.file_name = template.rv.format(self.experiment.name, self.series.name, self.channel.name, str_value(self.t, self.series.ts), str_value(self.z, self.series.zs))
		self.url = join(root, self.file_name)

		imsave(self.url, self.array)

### DATA
class DataFile(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='data_files')
	series = models.ForeignKey(Series, related_name='data_files')
	composite = models.ForeignKey(Composite, related_name='data_files')
	template = models.ForeignKey(Template, related_name='data_files')

	# properties
	id_token = models.CharField(max_length=8)
	data_type = models.CharField(max_length=255)
	url = models.CharField(max_length=255)
	file_name = models.CharField(max_length=255)

	data = []

	# methods
	def load(self):
		self.data = []
		with open(self.url) as df:
			headers = []
			for n, line in enumerate(df.readlines()):
				if n==0: # title
					headers = line.rstrip().split(',')
				else:
					line_dict = {}
					for i, token in enumerate(line.rstrip().split(',')):
						line_dict[headers[i]] = token
					self.data.append(line_dict)
		return self.data

	def save_data(self, data_headers):
		with open(self.url, 'w+') as df:
			df.write('{}\n'.format(','.join(data_headers)))
			for line in self.data:
				df.write(line)

		# parse cell profiler results spreadsheet into array that can be used to make cell instances
		# 1. generate dictionary keys from title line
		# 2. return array of dictionaries
