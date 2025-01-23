import nxenv


def execute():
	nxenv.reload_doc("website", "doctype", "web_page_view", force=True)
	site_url = nxenv.utils.get_site_url(nxenv.local.site)
	nxenv.db.sql(f"""UPDATE `tabWeb Page View` set is_unique=1 where referrer LIKE '%{site_url}%'""")
