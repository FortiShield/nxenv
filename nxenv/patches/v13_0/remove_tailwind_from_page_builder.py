# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	nxenv.reload_doc("website", "doctype", "web_page_block")
	# remove unused templates
	nxenv.delete_doc("Web Template", "Navbar with Links on Right", force=1)
	nxenv.delete_doc("Web Template", "Footer Horizontal", force=1)
