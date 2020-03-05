from __future__ import unicode_literals
from plug import Filetypes

import configparser

@Filetypes.plugin(["ini"])
class INI(object):
	def __init__(self):
		pass

	def validate(self, path, ext):
		try:
			config = configparser.ConfigParser()
			config.read(path)
			return (0, "")
		except configparser.MissingSectionHeaderError as e:
			return (1, str(e))
		except Exception as e:
			return (1, str(e))
