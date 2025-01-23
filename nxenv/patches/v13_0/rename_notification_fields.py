# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.utils.rename_field import rename_field


def execute():
	"""
	Change notification recipient fields from email to receiver fields
	"""
	nxenv.reload_doc("Email", "doctype", "Notification Recipient")
	nxenv.reload_doc("Email", "doctype", "Notification")

	rename_field("Notification Recipient", "email_by_document_field", "receiver_by_document_field")
	rename_field("Notification Recipient", "email_by_role", "receiver_by_role")
