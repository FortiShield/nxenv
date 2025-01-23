# Copyright (c) 2020, Nxenv Technologies and contributors
# License: MIT. See LICENSE

# import nxenv
from nxenv.model.document import Document


class OAuthScope(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		scope: DF.Data | None
	# end: auto-generated types

	pass
