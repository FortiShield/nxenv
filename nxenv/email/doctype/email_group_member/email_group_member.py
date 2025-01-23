# Copyright (c) 2015, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class EmailGroupMember(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		email: DF.Data
		email_group: DF.Link
		unsubscribed: DF.Check
	# end: auto-generated types

	def after_delete(self):
		email_group = nxenv.get_doc("Email Group", self.email_group)
		email_group.update_total_subscribers()

	def after_insert(self):
		email_group = nxenv.get_doc("Email Group", self.email_group)
		email_group.update_total_subscribers()


def after_doctype_insert():
	nxenv.db.add_unique("Email Group Member", ("email_group", "email"))
