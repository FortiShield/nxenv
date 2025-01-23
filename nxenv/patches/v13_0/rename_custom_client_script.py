import nxenv
from nxenv.model.rename_doc import rename_doc


def execute():
	if nxenv.db.exists("DocType", "Client Script"):
		return

	nxenv.flags.ignore_route_conflict_validation = True
	rename_doc("DocType", "Custom Script", "Client Script")
	nxenv.flags.ignore_route_conflict_validation = False

	nxenv.reload_doctype("Client Script", force=True)
