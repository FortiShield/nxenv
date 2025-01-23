# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	"""Add missing Twilio patch.

	While making Twilio as a standaone app, we missed to delete Twilio records from DB through migration. Adding the missing patch.
	"""
	nxenv.delete_doc_if_exists("DocType", "Twilio Number Group")
	if twilio_settings_doctype_in_integrations():
		nxenv.delete_doc_if_exists("DocType", "Twilio Settings")
		nxenv.db.delete("Singles", {"doctype": "Twilio Settings"})


def twilio_settings_doctype_in_integrations() -> bool:
	"""Check Twilio Settings doctype exists in integrations module or not."""
	return nxenv.db.exists("DocType", {"name": "Twilio Settings", "module": "Integrations"})
