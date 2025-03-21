# Copyright (c) 2024, Nxenv Technologies and contributors
# For license information, please see license.txt

import nxenv
from nxenv.model.document import Document


class UTMSource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		description: DF.SmallText | None
		slug: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		if self.slug:
			self.slug = nxenv.utils.slug(self.slug)
