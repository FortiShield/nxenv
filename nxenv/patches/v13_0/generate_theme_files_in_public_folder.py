# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	nxenv.reload_doc("website", "doctype", "website_theme_ignore_app")
	themes = nxenv.get_all("Website Theme", filters={"theme_url": ("not like", "/files/website_theme/%")})
	for theme in themes:
		doc = nxenv.get_doc("Website Theme", theme.name)
		try:
			doc.save()
		except Exception:
			print("Ignoring....")
			print(nxenv.get_traceback())
