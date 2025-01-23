import nxenv


def execute():
	"""
	Rename the Marketing Campaign table to UTM Campaign table
	"""
	if nxenv.db.exists("DocType", "UTM Campaign"):
		return

	if not nxenv.db.exists("DocType", "Marketing Campaign"):
		return

	nxenv.rename_doc("DocType", "Marketing Campaign", "UTM Campaign", force=True)
	nxenv.reload_doctype("UTM Campaign", force=True)
