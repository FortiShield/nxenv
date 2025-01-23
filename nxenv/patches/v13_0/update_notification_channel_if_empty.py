# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	nxenv.reload_doc("Email", "doctype", "Notification")

	notifications = nxenv.get_all("Notification", {"is_standard": 1}, {"name", "channel"})
	for notification in notifications:
		if not notification.channel:
			nxenv.db.set_value("Notification", notification.name, "channel", "Email", update_modified=False)
			nxenv.db.commit()
