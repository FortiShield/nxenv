# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import os

no_cache = 1

import json
import re
from urllib.parse import urlencode

import nxenv
import nxenv.sessions
from nxenv import _
from nxenv.utils.jinja_globals import is_rtl

SCRIPT_TAG_PATTERN = re.compile(r"\<script[^<]*\</script\>")
CLOSING_SCRIPT_TAG_PATTERN = re.compile(r"</script\>")


def get_context(context):
	if nxenv.session.user == "Guest":
		nxenv.response["status_code"] = 403
		nxenv.msgprint(_("Log in to access this page."))
		nxenv.redirect(f"/login?{urlencode({'redirect-to': nxenv.request.path})}")

	elif nxenv.session.data.user_type == "Website User":
		nxenv.throw(_("You are not permitted to access this page."), nxenv.PermissionError)

	try:
		boot = nxenv.sessions.get()
	except Exception as e:
		raise nxenv.SessionBootFailed from e

	# this needs commit
	csrf_token = nxenv.sessions.get_csrf_token()

	nxenv.db.commit()

	hooks = nxenv.get_hooks()
	app_include_js = hooks.get("app_include_js", []) + nxenv.conf.get("app_include_js", [])
	app_include_css = hooks.get("app_include_css", []) + nxenv.conf.get("app_include_css", [])
	app_include_icons = hooks.get("app_include_icons", [])

	if nxenv.get_system_settings("enable_telemetry") and os.getenv("NXENV_SENTRY_DSN"):
		app_include_js.append("sentry.bundle.js")

	context.update(
		{
			"no_cache": 1,
			"build_version": nxenv.utils.get_build_version(),
			"app_include_js": app_include_js,
			"app_include_css": app_include_css,
			"app_include_icons": app_include_icons,
			"layout_direction": "rtl" if is_rtl() else "ltr",
			"lang": nxenv.local.lang,
			"sounds": hooks["sounds"],
			"boot": boot,
			"desk_theme": boot.get("desk_theme") or "Light",
			"csrf_token": csrf_token,
			"google_analytics_id": nxenv.conf.get("google_analytics_id"),
			"google_analytics_anonymize_ip": nxenv.conf.get("google_analytics_anonymize_ip"),
			"app_name": (
				nxenv.get_website_settings("app_name") or nxenv.get_system_settings("app_name") or "Nxenv"
			),
		}
	)

	return context
