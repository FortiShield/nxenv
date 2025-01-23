import nxenv
from nxenv.model.rename_doc import rename_doc


def execute():
	if nxenv.db.table_exists("Workflow Action") and not nxenv.db.table_exists("Workflow Action Master"):
		rename_doc("DocType", "Workflow Action", "Workflow Action Master")
		nxenv.reload_doc("workflow", "doctype", "workflow_action_master")
