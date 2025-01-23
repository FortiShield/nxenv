# Copyright (c) 2015, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class HasRole(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		role: DF.Link | None
	# end: auto-generated types

	def before_insert(self):
		if nxenv.db.exists("Has Role", {"parent": self.parent, "role": self.role}):
			nxenv.throw(nxenv._("User '{0}' already has the role '{1}'").format(self.parent, self.role))
