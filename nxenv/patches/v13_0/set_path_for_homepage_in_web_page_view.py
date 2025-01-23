import nxenv


def execute():
	nxenv.reload_doc("website", "doctype", "web_page_view", force=True)
	nxenv.db.sql("""UPDATE `tabWeb Page View` set path='/' where path=''""")
