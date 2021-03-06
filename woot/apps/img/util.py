# apps.img.util

# django

# local

# util
import scipy
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage.morphology import binary_erosion as erode
import math

def cut_to_black(array):
	# coordinates of non-black
	r0 = np.argmax(np.any(array, axis=1))
	r1 = array.shape[0] - np.argmax(np.any(array, axis=1)[::-1])
	c0 = np.argmax(np.any(array, axis=0))
	c1 = array.shape[1] - np.argmax(np.any(array, axis=0)[::-1])

	# return cut
	return array[r0:r1,c0:c1], (r0,c0,(r1-r0),(c1-c0))

def edge_image(array): # assumed to be binary
	return array - erode(array)

# tests
def box_overlaps_marker(mask, marker):
	# box boundaries a0, a1
	# marker coordinate b
	# test a0 < b < a1
	return mask.r < marker.r and mask.r + mask.rs > mask.r and mask.c < marker.c and mask.c + mask.cs > marker.c

def mask_overlaps_marker(loaded_mask, marker):
	# test marker point is true in loaded mask
	return loaded_mask[marker.r, marker.c]

def box_overlaps_box(mask1, mask2):
	# one of the corners of one of the boxes must be within the other box, so test all 8 corners
	edge1 = mask1.r < mask2.r
	edge2 = mask1.r + mask1.rs > mask2.r + mask2.rs
	edge3 = mask1.c < mask2.c
	edge4 = mask1.c + mask1.cs > mask2.c + mask2.cs

	return not edge1 and not edge2 and not edge3 and not edge4

def box_overlaps_mask(mask, loaded_mask):
	overlap = np.any(loaded_mask[mask.r:mask.r+mask.rs, mask.c:mask.c+mask.cs])
	return overlap

def mask_overlaps_mask(loaded_mask1, loaded_mask2):
	s = loaded_mask1.astype(int) + loaded_mask2.astype(int)
	return np.any(s==2) # doubled up areas of overlap

def mask_is_adjacent_to_mask(loaded_mask1, loaded_mask2):
	# test for overlap of dilated masks
	self_dilated_int_array = dilate(loaded_mask1.astype(int))
	mask_dilated_int_array = dilate(loaded_mask2.astype(int))

	s = self_int_array + mask_int_array
	return np.any(s==2) # doubled up areas of overlap

def nonzero_mean(img):
	mask = img<0
	masked = np.ma.array(img, mask=mask)
	return masked.mean()

def nonzero_mean_thresholded_binary(img):
	nzm = nonzero_mean(img)
	return (img>nzm).copy()

def nonzero_mean_thresholded_preserve(img):
	nzm = nonzero_mean(img)
	img[img<nzm] = 0
	return img.copy()

class _Bulk():
	def __init__(self, gon_set, gon_stack, accessor_dict):
		self.gon_set = gon_set
		self.gon_stack = gon_stack
		self.accessor_dict = accessor_dict
		self.rv = {value:key for key, value in accessor_dict.items()}

	def slice(self, z=None, pk=None):
		if z is None:
			return self.gon_stack[:,:,self.accessor_dict[pk]]
		else:
			return self.gon_stack[:,:,self.accessor_dict[self.gon_set.get(z=z).pk]]

def create_bulk_from_image_set(img_set):

	# load entire set of mask gons as 3D box with accessor dictionary
	gon_stack = None
	accessor_dict = {}

	for i, gon in enumerate(img_set):
		m = gon.load()
		accessor_dict[gon.pk] = i
		if gon_stack is None:
			gon_stack = m
		else:
			gon_stack = np.dstack([gon_stack, m])

	return _Bulk(img_set, gon_stack, accessor_dict)

def scan_point(img, rs, cs, r, c, size=0):
	r0 = r - size if r - size >= 0 else 0
	r1 = r + size + 1 if r + size + 1 <= rs else rs
	c0 = c - size if c - size >= 0 else 0
	c1 = c + size + 1 if c + size + 1 <= cs else cs

	column = img[r0:r1,c0:c1,:]
	column_1D = np.sum(np.sum(column, axis=0), axis=0)

	return column_1D

def mask_edge_image(mask_img):
	full_edge_img = np.zeros(mask_img.shape)
	for unique in [u for u in np.unique(mask_img) if u>0]:
		full_edge_img += edge_image(mask_img==unique)

	return full_edge_img>0

def sort_edge(ref, points): # takes a list of tuples in the form [(r1, c1), (r2, c2), ... (rn, cn)]
	# polar_points = list(sorted([(math.sqrt((p[0] - ref[0])**2 + (p[1] - ref[1])**2), math.atan2(p[0], p[1])) for p in points], key=lambda p: p[0])) # from reference, sort by r
	polar_points = [(math.sqrt((p[0] - ref[0])**2 + (p[1] - ref[1])**2), math.pi + math.atan2(ref[1] - p[1], ref[0] - p[0])) for p in points]
	# start from knowledge about points
	# 1. points completely enclose an object, the object is a closed curve
	# 2. every point is on the edge of the object, no point can be enclosed or excluded by another pair of points
	# 3. the reference point in inside the object.
	class Point():
		def __init__(self, index, r, theta):
			self.index = index
			self.r = r
			self.theta = theta
			self.set = False

	max_r = max(polar_points, key=lambda p: p[0])[0]
	angles = 2*math.pi/len(polar_points) * np.arange(len(polar_points))
	original_points = [Point(0, r, theta) for (r, theta) in polar_points]
	test_points = [Point(i, max_r, theta) for i, theta in enumerate(angles)]

	# print([(o.r, o.theta) for o in original_points])
	# print([(t.r, t.theta) for t in test_points])
	# print('original')
	# for o in original_points:
	# 	print(o.r, o.theta)
	#
	# print('test')
	# for t in test_points:
	# 	print(t.r, t.theta)

	# for point in list(reversed(sorted(polar_points, key=lambda p: p[0]))):
	# 	not_set = list(filter(lambda t: not t.set, test_points))
	# 	print(len(not_set))
	# 	closest_point = min(not_set, key=lambda t: math.cos(t.theta-point[1]))
	# 	closest_point.set = True
	# 	closest_point.r = point[0]
	# 	test_points[closest_point.index] = closest_point

	for t in test_points:
		# filter
		not_set = list(filter(lambda o: not o.set, original_points))

		# get closest
		closest_point = min(not_set, key=lambda o: math.cos(o.theta-t.theta))

		# set properties
		closest_point.set = True


		# set lists
		test_points[closest_point.index] = closest_point
		original_points[i] = point

	# returns points sorted by position in edge
	# return [(int(ref[0] + test.r*math.sin(test.theta)), int(ref[1] + test.r*math.cos(test.theta))) for test in test_points]
	return [(int(ref[0] + point.r*math.sin(point.theta)), int(ref[1] + point.r*math.cos(point.theta))) for point in list(sorted(original_points, key=lambda p: p.index))]

def fold_edge(ref, points_rc):

	polar_points = [(math.sqrt((p[0] - ref[0])**2 + (p[1] - ref[1])**2), math.pi + math.atan2(ref[1] - p[1], ref[0] - p[0])) for p in points_rc]

	class Point():
		def __init__(self, index, r, theta):
			self.index = index
			self.r = r
			self.theta = theta
			self.set = False

		def rc(self, ref):
			return (int(ref[0] + self.r*math.cos(self.theta)), int(ref[1] + self.r*math.sin(self.theta)))

	min_r = (max(polar_points, key=lambda p: p[0])[0] - min(polar_points, key=lambda p: p[0])[0]) / len(polar_points)
	max_r = max(polar_points, key=lambda p: p[0])[0]
	min_angle = 2*math.pi/len(polar_points)
	angles = min_angle * np.arange(len(polar_points))
	original_points = [Point(i, r, theta) for i, (r, theta) in enumerate(polar_points)]
	max_theta = min(original_points, key=lambda o: max_r-o.r).theta
	test_points = [Point(i, max_r, theta+max_theta) for i, theta in enumerate(angles)]

	# check coordinate systems
	# max_theta = min(original_points, key=lambda o: max_r-o.r).theta
	# min_test = min(test_points, key=lambda t: abs(max_theta-t.theta))
	#
	# min_test.r += 100
	# test_points[min_test.index] = min_test

	folded_points = []
	last_match = None
	for t in test_points[:]:
		# each point can be deformed by dr, d-theta
		not_set = list(filter(lambda o: not o.set, original_points))
		if last_match is None:
			min_drdt = min(not_set, key=lambda o: (abs(o.r-t.r), abs(o.theta-t.theta))) # just find the maximum radius point
		else:
			min_drdt = min(not_set, key=lambda o: (math.sqrt(o.r**2 + last_match.r**2 - 2*o.r*last_match.r*math.cos(o.theta-last_match.theta))))

		# return to test
		t.r = min_drdt.r
		t.theta = min_drdt.theta
		test_points[t.index] = t

		# return to original
		min_drdt.set = True
		original_points[min_drdt.index] = min_drdt

		# set last
		last_match = min_drdt

	return [t.rc(ref) for t in test_points]

def edge_fall(ref, points_rc):

	points_rc = [(ref[0] - point[0], ref[1] - point[1]) for point in points_rc]

	class Point():
		previous_point = None
		next_point = None
		a = np.array([0.0,0.0])
		v = np.array([0.0,0.0])

		def __init__(self, r, c, index=0):
			self.r = np.array([r,c], dtype=float)
			self.index = index

		def update(self, a, h):
			self.a = a
			# self.r, self.v =

		def rc(self):
			return self.r[0] + ref[0], self.r[1] + ref[1]

	# get outer point
	max_rc = max(points_rc, key=lambda p: math.sqrt(p[0]**2 + p[1]**2))
	max_r = math.sqrt(max_rc[0]**2 + max_rc[1]**2)

	# get angles for circle
	angle_delta = 2 * math.pi / len(points_rc)

	# get list of points
	anchor_points = [Point(r,c) for r,c in points_rc]
	test_points = [Point(max_r * math.sin(theta), max_r * math.cos(theta), index=i) for i, theta in enumerate(angle_delta * np.arange(len(points_rc)))]

	# integrate
	# h = 2
	# for step in range(5):
	# 	print(step)
	# 	for test in test_points:
	# 		# 1. calculate acceleration from anchor points
	# 		a = np.array([0.0,0.0])
	# 		for anchor in anchor_points:
	# 			diff = test.r - anchor.r
	# 			a += -diff / (np.linalg.norm(diff)**3)
	#
	# 		test.update(a, h)
	# 		test_points[test.index] = test

	return [test.rc() for test in test_points]

def roll_edge_v1(points_rc, ball_radius=3):

	# 1. get outer point
	max_rc = max(points_rc, key=lambda p: np.linalg.norm(p))
	max_r = np.linalg.norm(max_rc)
	anchor = np.array(max_rc)

	# 2. define ball
	# - ball has a constant radius
	# - ball pivots about last confirmed point until another point is encountered. If no point is found, end the track.
	# - keep a log of points encountered in order
	ball_centre = list(np.array(max_rc) + (ball_radius * np.array(max_rc) / np.linalg.norm(max_rc)).astype(int)) # initially R from centre to max_rc + ball_radius
	anchor_list = [max_rc]

	class Ball():

		def __init__(self, radius, centre, anchor):
			self.radius = radius # only given as an integer.
			self.centre = centre # integer np array
			self.anchor = anchor # integer np array

		def rotate(self):
			# get radius list relative to anchor
			anchor_radius_list = self.radius_list()
			relative_centre = self.centre - self.anchor
			radius_list_index = anchor_radius_list.index(relative_centre.tolist())
			radius_list_index = radius_list_index if radius_list_index > 0 else len(anchor_radius_list)-1 # full rotation
			new_centre = anchor_radius_list[radius_list_index-1]

			# angle traversed
			# angle_traversed = math.acos(np.dot(np.array(new_centre), np.array(relative_centre)) / (np.linalg.norm(new_centre) * np.linalg.norm(relative_centre)))

			self.centre = np.array(new_centre) + self.anchor

		def search(self):
			# get radius list relative to centre
			centre_radius_list = self.radius_list()
			relative_centre = self.centre - self.anchor

			points_around_centre = [(np.array(lm)+self.centre).tolist() for lm in centre_radius_list]

			# The difference here is that we need to go the opposite direction from the centre rotation.
			# To do this, we need to find the centre point in the array and take everything until that point, but reversed.
			# This is in the manner of a ships compass in measuring distances on a map.
			index_of_anchor = points_around_centre.index(self.anchor.tolist())

			# 1. order points by angle from anchor position


			# 2.
			# points_to_search = list(reversed(points_around_centre[:index_of_anchor])) + list(reversed(points_around_centre[index_of_anchor+1:]))
			points_to_search = points_around_centre[index_of_anchor+1:] + points_around_centre[:index_of_anchor] if index_of_anchor!=len(points_around_centre)-1 else points_around_centre[:-1]

			new_anchor = None
			# print(self.anchor)
			for p in points_to_search:
				# print(p, new_anchor is None, p in points_rc, p not in anchor_list, new_anchor is None and p in points_rc and p not in anchor_list)
				# anchor_list.append(p)
				if new_anchor is None and p in points_rc and p not in anchor_list:
					# print('new anchor: {}'.format(p))
					new_anchor = p

			if new_anchor is not None:
				anchor_difference = np.array(new_anchor) - self.anchor
				# print(self.centre)
				# self.centre += anchor_difference # move centre linearly with changing anchor
				# print(self.centre)
				self.anchor = np.array(new_anchor)
				anchor_list.append(new_anchor)

			self.rotate()

		def radius_list(self):
			# return array of points that are a distance between [radius-1, radius]
			rl = []
			for i in range(-self.radius-1, self.radius+1):
				for j in range(-self.radius-1, self.radius+1):
					if 0 <= np.linalg.norm([i,j])-self.radius+1 < 1:
						rl.append([i,j])

			return list(sorted(rl, key=lambda r: math.atan2(r[0], r[1])))

	ball = Ball(ball_radius, ball_centre, anchor)

	# algorithm
	# 1. filter points to only include those within one ball diameter from the anchor
	# 2. initial check to see if other points are within the ball
	# 3. if points within, move the ball backwards by -0.5 * delta_theta
	# 4. check + move
	# 5. add points that are exactly a radius away to the list
	# 6. set anchor to any new point encountered

	i = 0
	while (np.linalg.norm(np.array(max_rc) - np.array(anchor_list[-1]))>0.5*ball_radius or len(anchor_list)<2*ball_radius) and i<len(ball.radius_list())*len(points_rc):
		# print(i, len(anchor_list))
		i += 1
		ball.search()

	anchor_list = anchor_list[::ball_radius]

	return i, len(ball.radius_list())*len(points_rc), anchor_list
