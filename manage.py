# !/usr/bin/env python
from os import environ
import sys

if __name__ == '__main__':
	# set settings variable based on env
	environ.setdefault('DJANGO_SETTINGS_MODULE', 'woot.settings')

	### If in a production or staging environment, the settings module should be called explicitly:
	# ~$ python manage.py --settings=woot.settings.production

	# start django
	from django.core.management import execute_from_command_line
	execute_from_command_line(sys.argv)
