import nxenv
from nxenv.model.rename_doc import rename_doc


def execute():
	if nxenv.db.table_exists("Email Alert Recipient") and not nxenv.db.table_exists(
		"Notification Recipient"
	):
		rename_doc("DocType", "Email Alert Recipient", "Notification Recipient")
		nxenv.reload_doc("email", "doctype", "notification_recipient")

	if nxenv.db.table_exists("Email Alert") and not nxenv.db.table_exists("Notification"):
		rename_doc("DocType", "Email Alert", "Notification")
		nxenv.reload_doc("email", "doctype", "notification")
