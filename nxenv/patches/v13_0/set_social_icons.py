import nxenv


def execute():
	providers = nxenv.get_all("Social Login Key")

	for provider in providers:
		doc = nxenv.get_doc("Social Login Key", provider)
		doc.set_icon()
		doc.save()
