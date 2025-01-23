# Copyright (c) 2019, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import shutil
from pathlib import Path

import nxenv
from nxenv import _
from nxenv.model.document import Document
from nxenv.modules import get_module_path, scrub
from nxenv.modules.export_file import export_to_files

FOLDER_NAME = "dashboard_chart_source"


@nxenv.whitelist()
def get_config(name: str) -> str:
	doc: DashboardChartSource = nxenv.get_doc("Dashboard Chart Source", name)
	return doc.read_config()


class DashboardChartSource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		module: DF.Link
		source_name: DF.Data
		timeseries: DF.Check
	# end: auto-generated types

	def on_update(self):
		if not nxenv.request:
			return

		if not nxenv.conf.developer_mode:
			nxenv.throw(_("Creation of this document is only permitted in developer mode."))

		export_to_files(record_list=[[self.doctype, self.name]], record_module=self.module, create_init=True)

	def on_trash(self):
		if not nxenv.conf.developer_mode and not nxenv.flags.in_migrate:
			nxenv.throw(_("Deletion of this document is only permitted in developer mode."))

		nxenv.db.after_commit.add(self.delete_folder)

	def read_config(self) -> str:
		"""Return the config JS file for this dashboard chart source."""
		config_path = self.get_folder_path() / f"{scrub(self.name)}.js"
		return config_path.read_text() if config_path.exists() else ""

	def delete_folder(self):
		"""Delete the folder for this dashboard chart source."""
		path = self.get_folder_path()
		if path.exists():
			shutil.rmtree(path, ignore_errors=True)

	def get_folder_path(self) -> Path:
		"""Return the path of the folder for this dashboard chart source."""
		return Path(get_module_path(self.module)) / FOLDER_NAME / nxenv.scrub(self.name)
