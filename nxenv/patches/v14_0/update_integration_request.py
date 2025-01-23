import nxenv


def execute():
	doctype = "Integration Request"

	if not nxenv.db.has_column(doctype, "integration_type"):
		return

	nxenv.db.set_value(
		doctype,
		{"integration_type": "Remote", "integration_request_service": ("!=", "PayPal")},
		"is_remote_request",
		1,
	)
	nxenv.db.set_value(
		doctype,
		{"integration_type": "Subscription Notification"},
		"request_description",
		"Subscription Notification",
	)
