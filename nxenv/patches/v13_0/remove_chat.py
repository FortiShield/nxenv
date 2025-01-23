import click

import nxenv


def execute():
	nxenv.delete_doc_if_exists("DocType", "Chat Message")
	nxenv.delete_doc_if_exists("DocType", "Chat Message Attachment")
	nxenv.delete_doc_if_exists("DocType", "Chat Profile")
	nxenv.delete_doc_if_exists("DocType", "Chat Token")
	nxenv.delete_doc_if_exists("DocType", "Chat Room User")
	nxenv.delete_doc_if_exists("DocType", "Chat Room")
	nxenv.delete_doc_if_exists("Module Def", "Chat")

	click.secho(
		"Chat Module is moved to a separate app and is removed from Nxenv in version-13.\n"
		"Please install the app to continue using the chat feature: https://github.com/nxenv/chat",
		fg="yellow",
	)
