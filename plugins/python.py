from __future__ import generator_stop

from typing import Tuple

from plug import Filetypes


@Filetypes.plugin(["py", "pyw"])
class Python(object):
	def __init__(self):
		pass

	def validate(self, path, ext):
		# type: (str, str) -> Tuple[int, str]

		try:
			with open(path, "rb") as fr:
				compile(fr.read(), "<file>", "exec")
			return (0, "")
		except (SyntaxError, TypeError) as e:
			return (1, str(e))
