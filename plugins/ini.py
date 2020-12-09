from __future__ import generator_stop

import configparser
from typing import Tuple

from plug import Filetypes


@Filetypes.plugin(["ini"])
class INI(object):
	def __init__(self):
		pass

	def validate(self, path, ext):
		# type: (str, str) -> Tuple[int, str]

		try:
			config = configparser.ConfigParser()
			config.read(path)
			return (0, "")
		except configparser.MissingSectionHeaderError as e:
			return (1, str(e))
		except Exception as e:
			return (1, str(e))
