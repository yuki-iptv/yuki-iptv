# https://github.com/LEW21/pydbus/tree/cc407c8b1d25b7e28a6d661a29f9e661b1c9b964
try:
	isident = str.isidentifier
except Exception:
	import re

	isidentre = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")
	def isident(s):
		return isidentre.match(s) is not None

def filter_identifier(name):
	name = name.replace("-", "_")

	safe_name = ""
	for c in name:
		if not safe_name:
			if isident(c):
				safe_name += c
		else:
			if isident("a" + c):
				safe_name += c
	return safe_name
