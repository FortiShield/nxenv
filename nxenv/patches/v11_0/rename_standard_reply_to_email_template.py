import nxenv
from nxenv.model.rename_doc import rename_doc


def execute():
	if nxenv.db.table_exists("Standard Reply") and not nxenv.db.table_exists("Email Template"):
		rename_doc("DocType", "Standard Reply", "Email Template")
		nxenv.reload_doc("email", "doctype", "email_template")
