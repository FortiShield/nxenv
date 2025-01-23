import nxenv


def execute():
	nxenv.delete_doc_if_exists("DocType", "Web View")
	nxenv.delete_doc_if_exists("DocType", "Web View Component")
	nxenv.delete_doc_if_exists("DocType", "CSS Class")
