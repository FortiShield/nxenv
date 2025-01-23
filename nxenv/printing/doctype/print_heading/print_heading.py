# Copyright (c) 2017, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class PrintHeading(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		description: DF.SmallText | None
		print_heading: DF.Data
	# end: auto-generated types

	pass
