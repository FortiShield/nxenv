# Copyright (c) 2023, Nxenv Technologies and contributors
# For license information, please see license.txt

import nxenv
from nxenv.model.document import Document
from nxenv.query_builder.utils import DocType


class CustomHTMLBlock(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.core.doctype.has_role.has_role import HasRole
		from nxenv.types import DF

		html: DF.Code | None
		private: DF.Check
		roles: DF.Table[HasRole]
		script: DF.Code | None
		style: DF.Code | None
	# end: auto-generated types

	pass


@nxenv.whitelist()
def get_custom_blocks_for_user(doctype, txt, searchfield, start, page_len, filters):
	# return logged in users private blocks and all public blocks
	customHTMLBlock = DocType("Custom HTML Block")

	condition_query = nxenv.qb.from_(customHTMLBlock)

	return (
		condition_query.select(customHTMLBlock.name).where(
			(customHTMLBlock.private == 0)
			| ((customHTMLBlock.owner == nxenv.session.user) & (customHTMLBlock.private == 1))
		)
	).run()
