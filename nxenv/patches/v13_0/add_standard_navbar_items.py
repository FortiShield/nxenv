import nxenv
from nxenv.utils.install import add_standard_navbar_items


def execute():
	# Add standard navbar items for ERPNext in Navbar Settings
	nxenv.reload_doc("core", "doctype", "navbar_settings")
	nxenv.reload_doc("core", "doctype", "navbar_item")
	add_standard_navbar_items()
