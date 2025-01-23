from urllib.parse import quote_plus

import nxenv
from nxenv import _
from nxenv.utils import cstr
from nxenv.website.page_renderers.template_page import TemplatePage


class NotPermittedPage(TemplatePage):
	def __init__(self, path=None, http_status_code=None, exception=""):
		nxenv.local.message = cstr(exception)
		super().__init__(path=path, http_status_code=http_status_code)
		self.http_status_code = 403

	def can_render(self):
		return True

	def render(self):
		action = f"/login?redirect-to={quote_plus(nxenv.request.path)}"
		if nxenv.request.path.startswith("/app/") or nxenv.request.path == "/app":
			action = "/login"
		nxenv.local.message_title = _("Not Permitted")
		nxenv.local.response["context"] = dict(
			indicator_color="red", primary_action=action, primary_label=_("Login"), fullpage=True
		)
		self.set_standard_path("message")
		return super().render()
