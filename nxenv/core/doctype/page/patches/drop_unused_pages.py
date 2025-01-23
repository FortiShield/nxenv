import nxenv


def execute():
	for name in ("desktop", "space"):
		nxenv.delete_doc("Page", name)
