# Copyright (c) 2021, Nxenv Technologies and contributors
# For license information, please see license.txt

import nxenv
from nxenv import _
from nxenv.model.document import Document


class PrintFormatFieldTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		document_type: DF.Link
		field: DF.Data | None
		module: DF.Link | None
		standard: DF.Check
		template: DF.Code | None
		template_file: DF.Data | None
	# end: auto-generated types

	def validate(self):
		if self.standard and not nxenv.conf.developer_mode and not nxenv.flags.in_patch:
			nxenv.throw(_("Enable developer mode to create a standard Print Template"))

	def before_insert(self):
		self.validate_duplicate()

	def on_update(self):
		self.validate_duplicate()
		self.export_doc()

	def validate_duplicate(self):
		if not self.standard:
			return
		if not self.field:
			return

		filters = {"document_type": self.document_type, "field": self.field}
		if not self.is_new():
			filters.update({"name": ("!=", self.name)})
		result = nxenv.get_all("Print Format Field Template", filters=filters, limit=1)
		if result:
			nxenv.throw(
				_("A template already exists for field {0} of {1}").format(
					nxenv.bold(self.field), nxenv.bold(self.document_type)
				),
				nxenv.DuplicateEntryError,
				title=_("Duplicate Entry"),
			)

	def export_doc(self):
		from nxenv.modules.utils import export_module_json

		export_module_json(self, self.standard, self.module)
