import nxenv
from nxenv.desk.doctype.notification_settings.notification_settings import (
	create_notification_settings,
)


def execute():
	nxenv.reload_doc("desk", "doctype", "notification_settings")
	nxenv.reload_doc("desk", "doctype", "notification_subscribed_document")

	users = nxenv.get_all("User", fields=["name"])
	for user in users:
		create_notification_settings(user.name)
