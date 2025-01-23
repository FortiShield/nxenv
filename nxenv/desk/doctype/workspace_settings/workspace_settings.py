# Copyright (c) 2024, Nxenv Technologies and contributors
# For license information, please see license.txt

import json

import nxenv
from nxenv.model.document import Document


class WorkspaceSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		workspace_setup_completed: DF.Check
		workspace_visibility_json: DF.JSON
	# end: auto-generated types

	pass

	def on_update(self):
		nxenv.clear_cache()


@nxenv.whitelist()
def set_sequence(sidebar_items):
	if not WorkspaceSettings("Workspace Settings").has_permission():
		nxenv.throw_permission_error()

	cnt = 1
	for item in json.loads(sidebar_items):
		nxenv.db.set_value("Workspace", item.get("name"), "sequence_id", cnt)
		nxenv.db.set_value("Workspace", item.get("name"), "parent_page", item.get("parent") or "")
		cnt += 1

	nxenv.clear_cache()
	nxenv.toast(nxenv._("Updated"))
