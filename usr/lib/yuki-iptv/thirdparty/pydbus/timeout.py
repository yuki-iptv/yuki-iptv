# https://github.com/LEW21/pydbus/tree/cc407c8b1d25b7e28a6d661a29f9e661b1c9b964
from gi.repository import GLib, GObject

def timeout_to_glib(timeout):
	if timeout is None:
		try:
			return GLib.MAXINT
		except AttributeError:
			# GLib < 2.46
			return GObject.G_MAXINT
	else:
		try:
			timeout = timeout.total_seconds()
		except AttributeError:
			pass
		return int(timeout * 1000)
