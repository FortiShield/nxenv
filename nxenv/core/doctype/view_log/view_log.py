# Copyright (c) 2018, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class ViewLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		viewed_by: DF.Data | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=180):
		from nxenv.query_builder import Interval
		from nxenv.query_builder.functions import Now

		table = nxenv.qb.DocType("View Log")
		nxenv.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))
