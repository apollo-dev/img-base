# apps.expt.util

# django
from django.db import models

# util
import random
import string
import re

# vars
chars = string.ascii_uppercase + string.digits

# methods
def generate_id_token(app_name, obj_name):

	Obj = models.get_model(app_name, obj_name)

	def get_id_token():
		return random_string()

	id_token = get_id_token()
	while Obj.objects.filter(id_token=id_token).count()>0:
		id_token = get_id_token()

	return id_token

def random_string():
	return ''.join([random.choice(chars) for _ in range(8)]) #8 character string

def series_metadata(file_name, series_name):

	def block(whole, start, end):
		start_block = whole[whole.index(start):]
		block = start_block[:start_block.index(end)]

		return block

	content = ''
	with open(file_name) as omexml:
		content = omexml.read()

	# 1. cut the block of text representing the series from the content
	series_block = block(content, 'Image:{}'.format(series_name), '</Image>')

	# 2. rs, cs, zs, ts, rmop, cmop, zmop
	# stored in the line
	# <Pixels ... PhysicalSizeX="3.829397265625" PhysicalSizeY="3.829397265625" PhysicalSizeZ="1.482" ... SizeC="2" SizeT="1" SizeX="256" SizeY="256" SizeZ="1">
	pixels_line = block(series_block, '<Pixels', '>')
	pixels_line_template = r'^<.+PhysicalSizeX="(?P<cmop>.+)" PhysicalSizeY="(?P<rmop>.+)" PhysicalSizeZ="(?P<zmop>.+)" SignificantBits=".+" SizeC=".+" SizeT="(?P<ts>.+)" SizeX="(?P<cs>.+)" SizeY="(?P<rs>.+)" SizeZ="(?P<zs>.+)" Type=".+"$'

	metadata = re.match(pixels_line_template, pixels_line).groupdict()

	# 3. finally, tpf. A little more complicated. Need to find the line in the planes section where C,T,Z = 0,1,0 -> then take DeltaT
	# <Plane DeltaT="458.7209987640381" PositionX="0.06314316103006" PositionY="0.04187452934148" PositionZ="0.0" TheC="0" TheT="1" TheZ="0"/>

	tpf_in_seconds = 0
	line_template = r'^<Plane DeltaT="(?P<delta_t>.+)" PositionX=".+" PositionY=".+" PositionZ=".+" TheC="(?P<c>.+)" TheT="(?P<t>.+)" TheZ="(?P<z>.+)"/>$'
	lines = [l for l in series_block.split('\n') if 'Plane DeltaT' in l]
	for line in lines:
		line_dict = re.match(line_template, line.strip()).groupdict()
		if (line_dict['c'], line_dict['t'], line_dict['z']) == ('0','1','0'):
			tpf_in_seconds = float(line_dict['delta_t'])

	metadata['tpf_in_seconds'] = tpf_in_seconds
	return metadata

def str_value(v, vs):
	v_str_len = len(str(v))
	vs_str_len = len(str(vs))

	diff = vs_str_len - v_str_len
	return '{}{}'.format('0'*diff, v)

def convert_track_file(path, name_with_index):
	# names
	index_template = r'(?P<name>.+)_n[0-9]+'
	alt = r'(?P<name>.+)'
	name_match = re.match(index_template, name_with_index) if re.match(index_template, name_with_index) is not None else re.match(alt, name_with_index)
	name = name_match.group('name')
	csv_file_name = '{}_{}_markers.csv'.format(join(path, name), random_string())
	xls_file_name = '{}.xls'.format(join(path, name_with_index))

	tracks = {} # stores list of tracks that can then be put into the database

	with open(xls_file_name, 'rb') as track_file:

		lines = track_file.read().decode('mac-roman').split('\n')[1:-1]
		for i, line in enumerate(lines): # omit title line and final blank line
			line = line.split('\t')

			# details
			track_id = int(float(line[1]))
			r = int(float(line[4]))
			c = int(float(line[3]))
			t = int(float(line[2])) - 1

			if track_id in tracks:
				tracks[track_id].append((r,c,t))
			else:
				tracks[track_id] = [(r,c,t)]

	with open(csv_file_name, 'w+') as out_file:
		out_file.write('expt,series,channel,id,t,r,c\n')
		for track_id, track in tracks.items():
			for frame in list(sorted(track, key=lambda t: t[2])):
				out_file.write('{},{},{},{},{},{},{}\n'.format(experiment_name,series_name,'-zcomp',track_id,frame[2],frame[0],frame[1]))
