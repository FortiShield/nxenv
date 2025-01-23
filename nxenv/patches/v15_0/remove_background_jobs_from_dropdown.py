import nxenv


def execute():
	item = nxenv.db.exists("Navbar Item", {"item_label": "Background Jobs"})
	if not item:
		return

	nxenv.delete_doc("Navbar Item", item)
