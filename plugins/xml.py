from __future__ import unicode_literals
from plug import Filetypes

from xml.etree.ElementTree import parse, ParseError

@Filetypes.plugin(["xml", "xsl"])
class XML(object):
	def __init__(self):
		pass

	def validate(self, path, ext):
		try:
			et = parse(path)
			return (0, "")
		except ParseError as e:
			return (1, str(e))
		except Exception as e:
			return (1, str(e))
