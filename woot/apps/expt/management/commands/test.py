# expt.command: data

# django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# local
from apps.img.models import Composite

# util
import numpy as np
from skimage import exposure
import matplotlib.pyplot as plt

spacer = ' ' *	20

### Command
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (

	)

	args = ''
	help = ''

	def handle(self, *args, **options):
		composite = Composite.objects.get()

		zmean_gon = composite.gons.get(channel__name='-zmean', t=0)
		zmod_gon = composite.gons.get(channel__name='-zmod', t=0)

		zmean = zmean_gon.load()
		zmod = zmod_gon.load()

		zunique = np.zeros(zmean.shape)
		for unique in np.unique(zmod):
			zunique[zmod==unique] = np.max(zmean[zmod==unique]) / np.sum(zmean)

		# zunique = gf(zunique, sigma=3)
		plt.imshow(zunique, cmap='Greys_r')
		plt.show()
