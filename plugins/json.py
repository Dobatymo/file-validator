from __future__ import absolute_import, division, print_function, unicode_literals

from genutility.json import read_json
from plug import Filetypes

@Filetypes.plugin(["json"])
class JSON(object):
	def __init__(self):
		pass

	def validate(self, path, ext):
		try:
			read_json(path)
			return (0, "")
		except Exception as e:
			return (1, str(e))
