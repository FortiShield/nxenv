import nxenv
from nxenv.model.utils.rename_field import rename_field


def execute():
	if not nxenv.db.table_exists("Dashboard Chart"):
		return

	nxenv.reload_doc("desk", "doctype", "dashboard_chart")

	if nxenv.db.has_column("Dashboard Chart", "is_custom"):
		rename_field("Dashboard Chart", "is_custom", "use_report_chart")
