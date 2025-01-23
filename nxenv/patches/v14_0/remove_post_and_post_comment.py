import nxenv


def execute():
	nxenv.delete_doc_if_exists("DocType", "Post")
	nxenv.delete_doc_if_exists("DocType", "Post Comment")
