# Copyright (c) 2021, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class WebhookRequestLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		data: DF.Code | None
		error: DF.Text | None
		headers: DF.Code | None
		reference_doctype: DF.Data | None
		reference_document: DF.Data | None
		response: DF.Code | None
		url: DF.Data | None
		user: DF.Link | None
		webhook: DF.Link | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=30):
		from nxenv.query_builder import Interval
		from nxenv.query_builder.functions import Now

		table = nxenv.qb.DocType("Webhook Request Log")
		nxenv.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))
