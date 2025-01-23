# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from nxenv.model.document import Document


class SMSParameter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		header: DF.Check
		parameter: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		value: DF.Data
	# end: auto-generated types

	pass
