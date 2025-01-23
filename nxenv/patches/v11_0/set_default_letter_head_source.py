import nxenv


def execute():
	nxenv.reload_doctype("Letter Head")

	# source of all existing letter heads must be HTML
	nxenv.db.sql("update `tabLetter Head` set source = 'HTML'")
