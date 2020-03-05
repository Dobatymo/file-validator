from __future__ import unicode_literals
from plug import Filetypes

from genutility.json import read_json

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
