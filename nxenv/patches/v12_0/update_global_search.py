import nxenv
from nxenv.desk.page.setup_wizard.install_fixtures import update_global_search_doctypes


def execute():
	nxenv.reload_doc("desk", "doctype", "global_search_doctype")
	nxenv.reload_doc("desk", "doctype", "global_search_settings")
	update_global_search_doctypes()
