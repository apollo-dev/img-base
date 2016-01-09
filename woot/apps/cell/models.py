# woot.apps.cell.models

# django
from django.db import models

# local
from apps.expt.models import Experiment, Series
from apps.img.models import Composite, Channel, Gon, Mask, MaskChannel
from apps.img.util import *

# util
import numpy as np
from scipy.ndimage.morphology import binary_dilation as dilate
from scipy.ndimage.filters import gaussian_filter as gf
from scipy.signal import find_peaks_cwt as find_peaks
import matplotlib.pyplot as plt

### Models
### MARKERS
class Track(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='tracks')
	series = models.ForeignKey(Series, related_name='tracks')
	composite = models.ForeignKey(Composite, related_name='tracks')
	channel = models.ForeignKey(Channel, related_name='tracks')

	# properties
	track_id = models.IntegerField(default=0)

class TrackInstance(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='track_instances')
	series = models.ForeignKey(Series, related_name='track_instances')
	composite = models.ForeignKey(Composite, related_name='track_instances')
	channel = models.ForeignKey(Channel, related_name='track_instances')
	track = models.ForeignKey(Track, related_name='instances')

	# properties
	t = models.IntegerField(default=0)

class Marker(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='markers')
	series = models.ForeignKey(Series, related_name='markers')
	composite = models.ForeignKey(Composite, related_name='markers')
	channel = models.ForeignKey(Channel, related_name='markers', null=True)
	gon = models.ForeignKey(Gon, related_name='markers', null=True)
	track = models.ForeignKey(Track, related_name='markers')
	track_instance = models.ForeignKey(TrackInstance, related_name='markers')

	# properties
	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	z = models.IntegerField(default=0)

### REGIONS
class RegionTrack(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='region_tracks')
	series = models.ForeignKey(Series, related_name='region_tracks')
	composite = models.ForeignKey(Composite, related_name='region_tracks')
	channel = models.ForeignKey(Channel, related_name='region_tracks')

	# properties
	name = models.CharField(max_length=255)

class RegionTrackInstance(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='region_track_instances')
	series = models.ForeignKey(Series, related_name='region_track_instances')
	composite = models.ForeignKey(Composite, related_name='region_track_instances')
	channel = models.ForeignKey(Channel, related_name='region_track_instances')
	region_track = models.ForeignKey(RegionTrack, related_name='instances')

	# properties
	t = models.IntegerField(default=0)

class RegionMarker(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='region_markers')
	series = models.ForeignKey(Series, related_name='region_markers')
	composite = models.ForeignKey(Composite, related_name='region_markers')
	channel = models.ForeignKey(Channel, related_name='region_markers')
	gon = models.ForeignKey(Gon, related_name='region_markers', null=True)
	region_track = models.ForeignKey(RegionTrack, related_name='markers')
	region_track_instance = models.ForeignKey(RegionTrackInstance, related_name='markers')
	region_track_index = models.IntegerField(default=-1) # stores position in chain.

	# properties
	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)

### REALITY
## REGION
class Region(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='regions')
	series = models.ForeignKey(Series, related_name='regions')
	region_track = models.OneToOneField(RegionTrack, related_name='regions')

	# properties
	name = models.CharField(max_length=255)

class RegionInstance(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='region_instances')
	series = models.ForeignKey(Series, related_name='region_instances')
	region = models.ForeignKey(Region, related_name='instances')
	region_track_instance = models.OneToOneField(RegionTrackInstance, related_name='region_instance')

	# properties
	mode_gray_value_id = models.IntegerField(default=0)

class RegionMask(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='region_masks')
	series = models.ForeignKey(Series, related_name='region_masks')
	region = models.ForeignKey(Region, related_name='masks')
	region_instance = models.ForeignKey(RegionInstance, related_name='masks')
	mask = models.ForeignKey(Mask, related_name='region_masks')

	# properties
	gray_value_id = models.IntegerField(default=0)
	area = models.IntegerField(default=0)

	# methods
	def load(self):
		mask = self.mask.load()
		mask[mask!=self.gray_value_id] = 0
		mask[mask>0] = 1
		return mask

## CELL
class Cell(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='cells')
	series = models.ForeignKey(Series, related_name='cells')
	track = models.OneToOneField(Track, related_name='cell')

	# properties
	confidence = models.FloatField(default=0.0)

	# methods
	def calculate_velocities(self, unique):
		previous_mask = None
		for cell_instance in self.instances.order_by('t'):
			if cell_instance.masks.filter(channel__name__contains=unique):
				mask = cell_instance.masks.get(channel__name__contains=unique)
				if previous_mask is None:
					mask.vr = 0
					mask.vc = 0
					mask.vz = 0
				else:
					# velocities
					mask.vr = mask.Location_Center_Y - previous_mask.Location_Center_Y
					mask.vc = mask.Location_Center_X - previous_mask.Location_Center_X
					mask.vz = mask.z - previous_mask.z

				mask.save()
				previous_mask = mask

	def calculate_confidences(self):
		pass
		# 1.

class CellInstance(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='cell_instances')
	series = models.ForeignKey(Series, related_name='cell_instances')
	cell = models.ForeignKey(Cell, related_name='instances')
	region = models.ForeignKey(Region, related_name='cell_instances', null=True)
	region_instance = models.ForeignKey(RegionInstance, related_name='cell_instances', null=True)
	track_instance = models.OneToOneField(TrackInstance, related_name='cell_instance')

	# properties
	confidence = models.FloatField(default=0.0)

	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	z = models.IntegerField(default=0)
	t = models.IntegerField(default=0)

	vr = models.IntegerField(default=0)
	vc = models.IntegerField(default=0)
	vz = models.IntegerField(default=0)

	def __str__(self):
		return str(self.t)

class CellMask(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='cell_masks')
	series = models.ForeignKey(Series, related_name='cell_masks')
	cell = models.ForeignKey(Cell, related_name='masks')
	cell_instance = models.ForeignKey(CellInstance, related_name='masks')
	region = models.ForeignKey(Region, related_name='cell_masks', null=True)
	region_instance = models.ForeignKey(RegionInstance, related_name='cell_masks', null=True)
	channel = models.ForeignKey(MaskChannel, related_name='cell_masks')
	mask = models.ForeignKey(Mask, related_name='cell_masks')
	marker = models.ForeignKey(Marker, related_name='cell_masks')

	# properties
	gray_value_id = models.IntegerField(default=0)
	confidence = models.FloatField(default=0.0)
	region_condition = models.CharField(max_length=255)
	average_radius = models.FloatField(default=0.0)

	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	z = models.IntegerField(default=0)
	t = models.IntegerField(default=0)

	vr = models.IntegerField(default=0)
	vc = models.IntegerField(default=0)
	vz = models.IntegerField(default=0)

	# 4. cell profiler
	AreaShape_Area = models.IntegerField(default=0)
	AreaShape_Compactness = models.FloatField(default=0.0)
	AreaShape_Eccentricity = models.FloatField(default=0.0)
	AreaShape_EulerNumber = models.FloatField(default=0.0)
	AreaShape_Extent = models.FloatField(default=0.0)
	AreaShape_FormFactor = models.FloatField(default=0.0)
	AreaShape_MajorAxisLength = models.FloatField(default=0.0)
	AreaShape_MaximumRadius = models.FloatField(default=0.0)
	AreaShape_MeanRadius = models.FloatField(default=0.0)
	AreaShape_MedianRadius = models.FloatField(default=0.0)
	AreaShape_MinorAxisLength = models.FloatField(default=0.0)
	AreaShape_Orientation = models.FloatField(default=0.0)
	AreaShape_Perimeter = models.FloatField(default=0.0)
	AreaShape_Solidity = models.FloatField(default=0.0)
	Location_Center_X = models.FloatField(default=0.0)
	Location_Center_Y = models.FloatField(default=0.0)

	# methods
	def R(self):
		return self.r*self.series.rmop

	def C(self):
		return self.c*self.series.cmop

	def Z(self):
		return self.z*self.series.zmop

	def T(self):
		return self.t*self.series.tpf

	def V(self):
		return np.sqrt(self.VR()**2 + self.VC()**2)

	def VR(self):
		return self.vr*self.series.rmop / self.series.tpf

	def VC(self):
		return self.vc*self.series.cmop / self.series.tpf

	def VZ(self):
		return self.vz*self.series.zmop / self.series.tpf

	def A(self):
		return self.AreaShape_Area*self.series.rmop*self.series.cmop

	def raw_line(self):
		return '{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{} \n'.format(self.experiment.name,
																																																	self.series.name,
																																																	self.cell.pk,
																																																	self.r,
																																																	self.c,
																																																	self.z,
																																																	self.t,
																																																	self.vr,
																																																	self.vc,
																																																	self.vz,
																																																	self.region.name,
																																																	self.AreaShape_Area,
																																																	self.AreaShape_Compactness,
																																																	self.AreaShape_Eccentricity,
																																																	self.AreaShape_EulerNumber,
																																																	self.AreaShape_Extent,
																																																	self.AreaShape_FormFactor,
																																																	self.AreaShape_MajorAxisLength,
																																																	self.AreaShape_MaximumRadius,
																																																	self.AreaShape_MeanRadius,
																																																	self.AreaShape_MedianRadius,
																																																	self.AreaShape_MinorAxisLength,
																																																	self.AreaShape_Orientation,
																																																	self.AreaShape_Perimeter,
																																																	self.AreaShape_Solidity)
	def line(self):
		return '{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(self.experiment.name,
																																																		self.series.name,
																																																		self.cell.pk,
																																																		self.R(),
																																																		self.C(),
																																																		self.Z(),
																																																		self.t,
																																																		self.T(),
																																																		self.VR(),
																																																		self.VC(),
																																																		self.VZ(),
																																																		self.region.name,
																																																		self.A(),
																																																		self.AreaShape_Compactness,
																																																		self.AreaShape_Eccentricity,
																																																		self.AreaShape_EulerNumber,
																																																		self.AreaShape_Extent,
																																																		self.AreaShape_FormFactor,
																																																		self.AreaShape_MajorAxisLength,
																																																		self.AreaShape_MaximumRadius,
																																																		self.AreaShape_MeanRadius,
																																																		self.AreaShape_MedianRadius,
																																																		self.AreaShape_MinorAxisLength,
																																																		self.AreaShape_Orientation,
																																																		self.AreaShape_Perimeter,
																																																		self.AreaShape_Solidity)
	def load(self):
		mask = self.mask.load()
		mask[mask!=self.gray_value_id] = 0
		mask[mask>0] = 1
		return mask

	def find_protrusions(self):
		# load mask image and find edge
		mask_img = self.load()
		edge_img = edge_image(mask_img)

		# get list of points that lie on the edge: points_rc
		points_r, points_c = np.where(edge_img)
		points_rc = [list(lm) for lm in list(zip(points_r, points_c))]

		# sort points using a fixed radius
		count, max_count, sorted_points = roll_edge_v1(points_rc)

		if count<max_count:
			# get cell centre and calculate distances of edge points from this point
			cell_centre = np.array([self.r, self.c])
			distances = np.array([np.linalg.norm(cell_centre - np.array(p)) for p in sorted_points])

			# smooth to aid peak finding and shift the points to leave the smallest distance at zero
			argmin = np.argmin(distances)
			distances = np.roll(distances, -argmin)
			distances = gf(distances, sigma=2)

			# find peaks
			peaks = find_peaks(distances, np.array([9]))

			# shift peaks back to their original positions
			true_peaks = np.array(peaks) + argmin
			true_peaks[true_peaks>=len(sorted_points)] -= len(sorted_points) # rotate

			# find end points
			protrusion_end_points = [sorted_points[peak] for peak in true_peaks]

			# create new protrusion for each end point
			for protrusion_end_point in protrusion_end_points:
				relative_end_point = cell_centre - np.array(protrusion_end_point)

				# parameters
				r = relative_end_point[0]
				c = relative_end_point[1]
				length_from_centre = np.linalg.norm(relative_end_point * self.series.scaling()) # in microns
				length_from_mean = length_from_centre - np.mean(distances)
				orientation_from_horizontal = math.atan2(relative_end_point[0], relative_end_point[1])

				# print(self.cell_instance.pk, self.pk, r, c, length_from_centre, orientation_from_horizontal)

				protrusion, protrusion_created = self.protrusions.get_or_create(experiment=self.experiment,
																																				series=self.series,
																																				cell=self.cell,
																																				cell_instance=self.cell_instance,
																																				channel=self.channel,
																																				region=self.region,
																																				region_instance=self.region_instance,
																																				r=r,
																																				c=c)
				if protrusion_created:
					protrusion.length = length_from_centre
					protrusion.length_from_mean = length_from_mean
					protrusion.orientation = orientation_from_horizontal
					protrusion.save()

			return 'success', len(protrusion_end_points)
		else:
			return 'success', 0

class Protrusion(models.Model):
	# connections
	experiment = models.ForeignKey(Experiment, related_name='protrusions')
	series = models.ForeignKey(Series, related_name='protrusions')
	cell = models.ForeignKey(Cell, related_name='protrusions')
	cell_instance = models.ForeignKey(CellInstance, related_name='protrusions')
	cell_mask = models.ForeignKey(CellMask, related_name='protrusions')
	channel = models.ForeignKey(MaskChannel, related_name='protrusions')
	region = models.ForeignKey(Region, related_name='protrusions', null=True)
	region_instance = models.ForeignKey(RegionInstance, related_name='protrusions', null=True)

	# properties
	r = models.IntegerField(default=0)
	c = models.IntegerField(default=0)
	length = models.FloatField(default=0.0)
	length_from_mean = models.FloatField(default=0.0)
	orientation = models.FloatField(default=0.0)
