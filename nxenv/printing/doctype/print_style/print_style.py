# Copyright (c) 2017, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class PrintStyle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		css: DF.Code
		disabled: DF.Check
		preview: DF.AttachImage | None
		print_style_name: DF.Data
		standard: DF.Check
	# end: auto-generated types

	def validate(self):
		if (
			self.standard == 1
			and not nxenv.local.conf.get("developer_mode")
			and not nxenv.flags.in_import
			and not nxenv.flags.in_test
		):
			nxenv.throw(nxenv._("Standard Print Style cannot be changed. Please duplicate to edit."))

	def on_update(self):
		self.export_doc()

	def export_doc(self):
		# export
		from nxenv.modules.utils import export_module_json

		export_module_json(self, self.standard == 1, "Printing")
