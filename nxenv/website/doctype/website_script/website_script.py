# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class WebsiteScript(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		javascript: DF.Code | None
	# end: auto-generated types

	def on_update(self):
		"""clear cache"""
		nxenv.clear_cache(user="Guest")

		from nxenv.website.utils import clear_cache

		clear_cache()
