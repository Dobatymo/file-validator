from __future__ import unicode_literals

from bs4 import BeautifulSoup
from genutility.file import read_file

from plug import Filetypes


@Filetypes.plugin(["htm", "html"])
class HTML(object):

	def __init__(self):
		pass

	def validate(self, path, ext):
		try:
			data = read_file(path, "rb")
			soup = BeautifulSoup(data, "lxml")
			return (0, "")
		except Exception as e:
			return (1, str(e.__class__.__name__) + ": " + str(e))
