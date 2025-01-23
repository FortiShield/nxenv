import nxenv
from nxenv.utils import cint


def execute():
	nxenv.reload_doctype("Dropbox Settings")
	check_dropbox_enabled = cint(nxenv.db.get_single_value("Dropbox Settings", "enabled"))
	if check_dropbox_enabled == 1:
		nxenv.db.set_single_value("Dropbox Settings", "file_backup", 1)
