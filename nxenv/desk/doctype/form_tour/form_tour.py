# Copyright (c) 2021, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import json

import nxenv
from nxenv import _
from nxenv.model.document import Document
from nxenv.modules.export_file import export_to_files


class FormTour(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.desk.doctype.form_tour_step.form_tour_step import FormTourStep
		from nxenv.types import DF

		dashboard_name: DF.Link | None
		first_document: DF.Check
		include_name_field: DF.Check
		is_standard: DF.Check
		list_name: DF.Literal[
			"List", "Report", "Dashboard", "Kanban", "Gantt", "Calendar", "File", "Image", "Inbox", "Map"
		]
		module: DF.Link | None
		new_document_form: DF.Check
		page_name: DF.Link | None
		page_route: DF.SmallText | None
		reference_doctype: DF.Link | None
		report_name: DF.Link | None
		save_on_complete: DF.Check
		steps: DF.Table[FormTourStep]
		title: DF.Data
		track_steps: DF.Check
		ui_tour: DF.Check
		view_name: DF.Literal["Workspaces", "List", "Form", "Tree", "Page"]
		workspace_name: DF.Link | None
	# end: auto-generated types

	def before_save(self):
		if self.is_standard and not self.module:
			if self.workspace_name:
				self.module = nxenv.db.get_value("Workspace", self.workspace_name, "module")
			elif self.dashboard_name:
				dashboard_doctype = nxenv.db.get_value("Dashboard", self.dashboard_name, "module")
				self.module = nxenv.db.get_value("DocType", dashboard_doctype, "module")
			else:
				self.module = "Desk"
		if not self.ui_tour:
			meta = nxenv.get_meta(self.reference_doctype)
			for step in self.steps:
				if step.is_table_field and step.parent_fieldname:
					parent_field_df = meta.get_field(step.parent_fieldname)
					step.child_doctype = parent_field_df.options
					field_df = nxenv.get_meta(step.child_doctype).get_field(step.fieldname)
					step.label = field_df.label
					step.fieldtype = field_df.fieldtype
				else:
					field_df = meta.get_field(step.fieldname)
					step.label = field_df.label
					step.fieldtype = field_df.fieldtype

	def on_update(self):
		nxenv.cache.delete_key("bootinfo")

		if nxenv.conf.developer_mode and self.is_standard:
			export_to_files([["Form Tour", self.name]], self.module)

	def on_trash(self):
		nxenv.cache.delete_key("bootinfo")


@nxenv.whitelist()
def reset_tour(tour_name):
	for user in nxenv.get_all("User", pluck="name"):
		onboarding_status = nxenv.parse_json(nxenv.db.get_value("User", user, "onboarding_status"))
		onboarding_status.pop(tour_name, None)
		nxenv.db.set_value(
			"User", user, "onboarding_status", nxenv.as_json(onboarding_status), update_modified=False
		)
		nxenv.cache.hdel("bootinfo", user)

	nxenv.msgprint(_("Successfully reset onboarding status for all users."), alert=True)


@nxenv.whitelist()
def update_user_status(value, step):
	from nxenv.utils.telemetry import capture

	step = nxenv.parse_json(step)
	tour = nxenv.parse_json(value)

	capture(
		nxenv.scrub(f"{step.parent}_{step.title}"),
		app="nxenv_ui_tours",
		properties={"is_completed": tour.is_completed},
	)
	nxenv.db.set_value("User", nxenv.session.user, "onboarding_status", value, update_modified=False)

	nxenv.cache.hdel("bootinfo", nxenv.session.user)


def get_onboarding_ui_tours():
	if not nxenv.get_system_settings("enable_onboarding"):
		return []

	ui_tours = nxenv.get_all("Form Tour", filters={"ui_tour": 1}, fields=["page_route", "name"])

	return [[tour.name, json.loads(tour.page_route)] for tour in ui_tours]
