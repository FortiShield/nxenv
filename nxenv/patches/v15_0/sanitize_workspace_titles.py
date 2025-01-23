import nxenv
from nxenv.desk.doctype.workspace.workspace import update_page
from nxenv.utils import strip_html
from nxenv.utils.html_utils import unescape_html


def execute():
	workspaces_to_update = nxenv.get_all(
		"Workspace",
		filters={"module": ("is", "not set")},
		fields=["name", "title", "icon", "indicator_color", "parent_page as parent", "public"],
	)
	for workspace in workspaces_to_update:
		new_title = strip_html(unescape_html(workspace.title))

		if new_title == workspace.title:
			continue

		workspace.title = new_title
		try:
			update_page(**workspace)
			nxenv.db.commit()

		except Exception:
			nxenv.db.rollback()
