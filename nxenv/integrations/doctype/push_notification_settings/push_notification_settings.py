# Copyright (c) 2024, Nxenv Technologies and contributors
# For license information, please see license.txt

import nxenv
from nxenv import _
from nxenv.model.document import Document


class PushNotificationSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		api_key: DF.Data | None
		api_secret: DF.Password | None
		enable_push_notification_relay: DF.Check
	# end: auto-generated types

	def validate(self):
		self.validate_relay_server_setup()

	def validate_relay_server_setup(self):
		if self.enable_push_notification_relay and not nxenv.conf.get("push_relay_server_url"):
			nxenv.throw(
				_("The Push Relay Server URL key (`push_relay_server_url`) is missing in your site config"),
				title=_("Relay Server URL missing"),
			)
