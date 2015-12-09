# apps.expt.data

'''
Specific experiment and series information in the form of lists of prototype objects
'''
import os

### Image file extensions
allowed_img_extensions = (
  '.tiff',
)

allowed_data_extensions = (
  '.csv',
)

### image filename templates
templates = {
  'source':{
    'rx':r'^(?P<experiment>.+)_s(?P<series>.+)_ch(?P<channel>.+)_t(?P<t>[0-9]+)_z(?P<z>[0-9]+)\.(?P<extension>.+)$',
    'rv':r'{}_s{}_ch{}_t{}_z{}.tiff',
  },
  'mask':{
    'rx':r'^(?P<experiment>.+)_s(?P<series>.+)_ch(?P<channel>.+)_t(?P<t>[0-9]+)\.(?P<extension>.+)$',
    'rv':r'{}_s{}_ch{}_t{}.tiff',
  },
  'cp':{
    'rx':r'^(?P<experiment>.+)_s(?P<series>.+)_ch-(?P<channel>.+)_t(?P<t>[0-9]+)_z(?P<z>[0-9]+)_cp-(?P<secondary_channel>.+)\.(?P<extension>.+)$',
    'rv':r'{}_s{}_ch-{}_t{}_z{}_cp-{}.tiff',
  },
  'data':{
    'rx':r'^(?P<experiment>.+)_s(?P<series>.+)_(?P<id>[A-Z0-9]{8})_(?P<type>.+)\.csv$',
    'rv':r'{}_s{}_{}_{}.csv',
  },
  'pipeline':{
    'rx':r'^(?P<name>.+)_(?P<id>[A-Z0-9]{8})\.cppipe$',
    'rv':r'{}_{}.cppipe',
  }
}

### Default paths
default_paths = {
  'storage':'img/storage/',
  'composite':'img/composite/',
  'cp':'img/cp/',
  'ij':'ij/',
  'regions':'regions/',

  'plot':'plot/',
  'track':'track/',
  'data':'data/',
  'pipeline':'pipelines/',
  'video':'video/',
  'inf':'inf/',
}

# headers
headers = [
  'experiment',
  'series',
  'cell id',
  'r (um)',
  'c (um)',
  'z (um)',
  'frame',
  't (min)',
  'vr (um/min)',
  'vc (um/min)',
  'vz (um/min)',
  'v (um/min)',
  'region.index',
  'Area (um^2)',
  'AreaShape_Compactness',
  'AreaShape_Eccentricity',
  'AreaShape_EulerNumber',
  'AreaShape_FormFactor',
  'AreaShape_Orientation',
  'AreaShape_Solidity',
]
