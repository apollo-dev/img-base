# apps.expt.pipeline

'''
Text representation of a cell profiler pipeline that can be used to modify data processing.
'''

def prototype_pipeline(img_path, experiment_prefix, unique_key, primary_channel_name, secondary_channel_name):
	pipeline = ''
	pipeline += Header(7)
	pipeline += LoadImages(1, primary_channel_name, 'Images', 'Primary', 'ObjectName', 'OutlineName', input_location=img_path, show_window=False)
	pipeline += LoadImages(2, secondary_channel_name, 'Images', 'Secondary', 'ObjectName', 'OutlineName', input_location=img_path, show_window=False)
	pipeline += IdentifyPrimaryObjects(3, 'Primary', 'Markers')
	pipeline += IdentifySecondaryObjects(4, 'Markers', 'Cells', 'Secondary', 'OutlineName', threshold_correction_factor=1.0, background=True, show_window=True)
	pipeline += MeasureObjectSizeShape(5, 'Cells')
	pipeline += ExportToSpreadsheet(6, experiment_prefix)
	pipeline += SaveImages(7, 'Objects', 'ImageName', 'Cells', 'Secondary', unique_key)

	return pipeline

def marker_pipeline(experiment_prefix, unique_key, primary_channel_name, secondary_channel_name, threshold_correction_factor=1.2, background=True):

	pipeline = ''
	pipeline += Header(7)
	pipeline += LoadImages(1, primary_channel_name, 'Images', 'Primary', 'ObjectName', 'OutlineName')
	pipeline += LoadImages(2, secondary_channel_name, 'Images', 'Secondary', 'ObjectName', 'OutlineName')
	pipeline += IdentifyPrimaryObjects(3, 'Primary', 'Markers')
	pipeline += IdentifySecondaryObjects(4, 'Markers', 'Cells', 'Secondary', 'OutlineName', threshold_correction_factor=threshold_correction_factor, background=background)
	pipeline += MeasureObjectSizeShape(5, 'Cells')
	pipeline += ExportToSpreadsheet(6, experiment_prefix)
	pipeline += SaveImages(7, 'Objects', 'ImageName', 'Cells', 'Secondary', unique_key)

	return pipeline

def region_pipeline(experiment_prefix, unique_key, primary_channel_name, secondary_channel_name, threshold_correction_factor=1.2, background=True):

	pipeline = ''
	pipeline += Header(8)
	pipeline += LoadImages(1, primary_channel_name, 'Objects', 'ImageName', 'RegionMarkers', 'OutlineName')
	pipeline += LoadImages(2, secondary_channel_name, 'Images', 'Secondary', 'ObjectName', 'OutlineName')
	pipeline += MeasureObjectSizeShape(3, 'RegionMarkers')
	pipeline += FilterObjects(4, 'FilteredRegionMarkers', 'RegionMarkers')
	pipeline += IdentifySecondaryObjects(5, 'FilteredRegionMarkers', 'Regions', 'Secondary', 'OutlineName', threshold_correction_factor=threshold_correction_factor, background=background)
	pipeline += ExpandOrShrinkObjects(6, 'Regions', 'ExpandedRegions')
	pipeline += TrackObjects(7, 'ExpandedRegions')
	pipeline += SaveImages(8, 'Objects', 'ImageName', 'ExpandedRegions', 'Secondary', unique_key)

	return pipeline

def Header(module_count):
	return 'CellProfiler Pipeline: http://www.cellprofiler.org\n\
					Version:3\n\
					DateRevision:20140723173957\n\
					GitHash:6c2d896\n\
					ModuleCount:{module_count}\n\
					HasImagePlaneDetails:False\n\n'.format(module_count=module_count)

def LoadImages(module_num, channel_name, objects_or_images, image_name, object_name, outline_name, input_location=None, show_window=False):
	input_location = None
	input_file_location = 'Elsewhere...\x7C{}'.format(input_location) if input_location is not None else 'Default Input Folder\x7C'

	return 'LoadImages:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:11|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					File type to be loaded:individual images\n\
					File selection method:Text-Regular expressions\n\
					Number of images in each group?:3\n\
					Type the text that the excluded images have in common:Do not use\n\
					Analyze all subfolders within the selected folder?:None\n\
					Input image file location:{input_file_location}\n\
					Check image sets for unmatched or duplicate files?:Yes\n\
					Group images by metadata?:No\n\
					Exclude certain files?:No\n\
					Specify metadata fields to group by:\n\
					Select subfolders to analyze:\n\
					Image count:1\n\
					Text that these images have in common (case-sensitive):{channel_name}_\n\
					Position of this image in each group:1\n\
					Extract metadata from where?:None\n\
					Regular expression that finds metadata in the file name:\n\
					Type the regular expression that finds metadata in the subfolder path:\n\
					Channel count:1\n\
					Group the movie frames?:No\n\
					Grouping method:Interleaved\n\
					Number of channels per group:1\n\
					Load the input as images or objects?:{objects_or_images}\n\
					Name this loaded image:{image_name}\n\
					Name this loaded object:{object_name}\n\
					Retain outlines of loaded objects?:No\n\
					Name the outline image:{outline_name}\n\
					Channel number:1\n\
					Rescale intensities?:Yes\n\n'.format(show_window=show_window,
																							 module_num=module_num,
																							 input_file_location=input_file_location,
																							 channel_name=channel_name,
																							 objects_or_images=objects_or_images,
																							 image_name=image_name,
																							 object_name=object_name,
																							 outline_name=outline_name)

def FilterObjects(module_num, output_object_name, input_object_name, show_window=False):
	return 'FilterObjects:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:7|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Name the output objects:{output_object_name}\n\
					Select the object to filter:{input_object_name}\n\
					Select the filtering mode:Measurements\n\
					Select the filtering method:Limits\n\
					Select the objects that contain the filtered objects:None\n\
					Retain outlines of the identified objects?:No\n\
					Name the outline image:FilteredObjects\n\
					Rules file location:Elsewhere...\x7C\n\
					Rules file name:rules.txt\n\
					Class number:1\n\
					Measurement count:1\n\
					Additional object count:0\n\
					Assign overlapping child to:Both parents\n\
					Select the measurement to filter by:AreaShape_Area\n\
					Filter using a minimum measurement value?:Yes\n\
					Minimum value:100.0\n\
					Filter using a maximum measurement value?:No\n\
					Maximum value:1.0\n\n'.format(show_window=show_window, module_num=module_num, output_object_name=output_object_name, input_object_name=input_object_name)

def IdentifyPrimaryObjects(module_num, image_name, object_name, min_radius=3, max_radius=13, show_window=False):
	return 'IdentifyPrimaryObjects:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:10|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Select the input image:{image_name}\n\
					Name the primary objects to be identified:{object_name}\n\
					Typical diameter of objects, in pixel units (Min,Max):{min_radius},{max_radius}\n\
					Discard objects outside the diameter range?:Yes\n\
					Try to merge too small objects with nearby larger objects?:No\n\
					Discard objects touching the border of the image?:Yes\n\
					Method to distinguish clumped objects:Intensity\n\
					Method to draw dividing lines between clumped objects:Intensity\n\
					Size of smoothing filter:10\n\
					Suppress local maxima that are closer than this minimum allowed distance:7.0\n\
					Speed up by using lower-resolution image to find local maxima?:Yes\n\
					Name the outline image:PrimaryOutlines\n\
					Fill holes in identified objects?:After both thresholding and declumping\n\
					Automatically calculate size of smoothing filter for declumping?:Yes\n\
					Automatically calculate minimum allowed distance between local maxima?:Yes\n\
					Retain outlines of the identified objects?:No\n\
					Automatically calculate the threshold using the Otsu method?:Yes\n\
					Enter Laplacian of Gaussian threshold:0.5\n\
					Automatically calculate the size of objects for the Laplacian of Gaussian filter?:Yes\n\
					Enter LoG filter diameter:5.0\n\
					Handling of objects if excessive number of objects identified:Continue\n\
					Maximum number of objects:500\n\
					Threshold setting version:1\n\
					Threshold strategy:Adaptive\n\
					Thresholding method:Otsu\n\
					Select the smoothing method for thresholding:Automatic\n\
					Threshold smoothing scale:1.0\n\
					Threshold correction factor:1.0\n\
					Lower and upper bounds on threshold:0.0,1.0\n\
					Approximate fraction of image covered by objects?:0.01\n\
					Manual threshold:0.0\n\
					Select the measurement to threshold with:None\n\
					Select binary image:None\n\
					Masking objects:None\n\
					Two-class or three-class thresholding?:Two classes\n\
					Minimize the weighted variance or the entropy?:Weighted variance\n\
					Assign pixels in the middle intensity class to the foreground or the background?:Foreground\n\
					Method to calculate adaptive window size:Image size\n\
					Size of adaptive window:10\n\n'.format(show_window=show_window,
																								 module_num=module_num,
																								 image_name=image_name,
																								 object_name=object_name,
																								 min_radius=min_radius,
																								 max_radius=max_radius)

def IdentifySecondaryObjects(module_num, primary_object_name, secondary_object_name, image_name, outline_name, threshold_correction_factor=1.2, background=True, show_window=False):

	background = 'Background' if background is True else 'Foreground'

	return 'IdentifySecondaryObjects:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:9|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Select the input objects:{primary_object_name}\n\
					Name the objects to be identified:{secondary_object_name}\n\
					Select the method to identify the secondary objects:Propagation\n\
					Select the input image:{image_name}\n\
					Number of pixels by which to expand the primary objects:10\n\
					Regularization factor:0.05\n\
					Name the outline image:{outline_name}\n\
					Retain outlines of the identified secondary objects?:No\n\
					Discard secondary objects touching the border of the image?:No\n\
					Discard the associated primary objects?:No\n\
					Name the new primary objects:FilteredNuclei\n\
					Retain outlines of the new primary objects?:No\n\
					Name the new primary object outlines:FilteredNucleiOutlines\n\
					Fill holes in identified objects?:Yes\n\
					Threshold setting version:1\n\
					Threshold strategy:Adaptive\n\
					Thresholding method:Otsu\n\
					Select the smoothing method for thresholding:Automatic\n\
					Threshold smoothing scale:1.0\n\
					Threshold correction factor:{threshold_correction_factor}\n\
					Lower and upper bounds on threshold:0.0,1.0\n\
					Approximate fraction of image covered by objects?:0.01\n\
					Manual threshold:0.0\n\
					Select the measurement to threshold with:None\n\
					Select binary image:None\n\
					Masking objects:None\n\
					Two-class or three-class thresholding?:Three classes\n\
					Minimize the weighted variance or the entropy?:Weighted variance\n\
					Assign pixels in the middle intensity class to the foreground or the background?:{background}\n\
					Method to calculate adaptive window size:Image size\n\
					Size of adaptive window:10\n\n'.format(show_window=show_window,
																								 module_num=module_num,
																								 primary_object_name=primary_object_name,
																								 secondary_object_name=secondary_object_name,
																								 image_name=image_name,
																								 outline_name=outline_name,
																								 threshold_correction_factor=threshold_correction_factor,
																								 background=background)

def MeasureObjectSizeShape(module_num, object_name, show_window=False):
	return 'MeasureObjectSizeShape:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:1|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Select objects to measure:{object_name}\n\
					Calculate the Zernike features?:Yes\n\n'.format(show_window=show_window,
																													module_num=module_num,
																													object_name=object_name)

def ExportToSpreadsheet(module_num, experiment_prefix, show_window=False):
	return 'ExportToSpreadsheet:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:11|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Select the column delimiter:Comma (",")\n\
					Add image metadata columns to your object data file?:No\n\
					Limit output to a size that is allowed in Excel?:No\n\
					Select the measurements to export:No\n\
					Calculate the per-image mean values for object measurements?:No\n\
					Calculate the per-image median values for object measurements?:No\n\
					Calculate the per-image standard deviation values for object measurements?:No\n\
					Output file location:Default Output Folder\x7C\n\
					Create a GenePattern GCT file?:No\n\
					Select source of sample row name:Metadata\n\
					Select the image to use as the identifier:None\n\
					Select the metadata to use as the identifier:None\n\
					Export all measurement types?:Yes\n\
					Press button to select measurements to export:\n\
					Representation of Nan/Inf:NaN\n\
					Add a prefix to file names?:Yes\n\
					Filename prefix\x3A{experiment_prefix}\n\
					Overwrite without warning?:Yes\n\
					Data to export:Do not use\n\
					Combine these object measurements with those of the previous object?:No\n\
					File name:DATA.csv\n\
					Use the object name for the file name?:Yes\n\n'.format(show_window=show_window,
																																 module_num=module_num,
																																 experiment_prefix=experiment_prefix)

def Smooth(module_num, input_image_name, output_image_name, typical_artifact_diameter=16.0, show_window=False):
	return 'Smooth:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:2|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Select the input image:{input_image_name}\n\
					Name the output image:{output_image_name}\n\
					Select smoothing method:Smooth Keeping Edges\n\
					Calculate artifact diameter automatically?:Yes\n\
					Typical artifact diameter:{typical_artifact_diameter}\n\
					Edge intensity difference:0.1\n\
					Clip intensities to 0 and 1?:Yes\n\n'.format(show_window=show_window,
																											 module_num=module_num,
																											 input_image_name=input_image_name,
																											 output_image_name=output_image_name,
																											 typical_artifact_diameter=typical_artifact_diameter)

def ExpandOrShrinkObjects(module_num, input_object_name, output_object_name, show_window=False):
	return 'ExpandOrShrinkObjects:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:1|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Select the input objects:{input_object_name}\n\
					Name the output objects:{output_object_name}\n\
					Select the operation:Expand objects until touching\n\
					Number of pixels by which to expand or shrink:1\n\
					Fill holes in objects so that all objects shrink to a single point?:No\n\
					Retain the outlines of the identified objects?:No\n\
					Name the outline image:ShrunkenNucleiOutlines\n\n'.format(show_window=show_window,
																																		module_num=module_num,
																																		input_object_name=input_object_name,
																																		output_object_name=output_object_name)

def TrackObjects(module_num, object_name, show_window=False):
	return 'TrackObjects:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:5|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
			Choose a tracking method:Overlap\n\
			Select the objects to track:{object_name}\n\
			Select object measurement to use for tracking:None\n\
			Maximum pixel distance to consider matches:50\n\
			Select display option:Color and Number\n\
			Save color-coded image?:No\n\
			Name the output image:TrackedCells\n\
			Select the motion model:Both\n\
			Number of standard deviations for search radius:3.0\n\
			Search radius limit, in pixel units (Min,Max):2.0,10.0\n\
			Run the second phase of the LAP algorithm?:Yes\n\
			Gap cost:40\n\
			Split alternative cost:40\n\
			Merge alternative cost:40\n\
			Maximum gap displacement, in frames:5\n\
			Maximum split score:50\n\
			Maximum merge score:50\n\
			Maximum gap:5\n\
			Filter objects by lifetime?:No\n\
			Filter using a minimum lifetime?:Yes\n\
			Minimum lifetime:1\n\
			Filter using a maximum lifetime?:No\n\
			Maximum lifetime:100\n\n'.format(show_window=show_window,
																			 module_num=module_num,
																			 object_name=object_name)

def SaveImages(module_num, objects_or_images, image_name, object_name, prefix_image, unique_key, show_window=False):
	return 'SaveImages:[module_num:{module_num}|svn_version:\'Unknown\'|variable_revision_number:11|show_window:{show_window}|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]\n\
					Select the type of image to save:{objects_or_images}\n\
					Select the image to save:{image_name}\n\
					Select the objects to save:{object_name}\n\
					Select the module display window to save:None\n\
					Select method for constructing file names:From image filename\n\
					Select image name for file prefix:{prefix_image}\n\
					Enter single file name:OrigBlue\n\
					Number of digits:4\n\
					Append a suffix to the image file name?:Yes\n\
					Text to append to the image name:_cp{unique_key}\n\
					Saved file format:tiff\n\
					Output file location:Default Output Folder|\n\
					Image bit depth:8\n\
					Overwrite existing files without warning?:Yes\n\
					When to save:Every cycle\n\
					Rescale the images? :No\n\
					Save as grayscale or color image?:Grayscale\n\
					Select colormap:gray\n\
					Record the file and path information to the saved image?:No\n\
					Create subfolders in the output folder?:No\n\
					Base image folder:Elsewhere...|\n\
					Saved movie format:avi\n\n'.format(show_window=show_window,
																						 module_num=module_num,
																						 objects_or_images=objects_or_images,
																						 image_name=image_name,
																						 object_name=object_name,
																						 prefix_image=prefix_image,
																						 unique_key=unique_key)
