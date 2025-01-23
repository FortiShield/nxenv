import nxenv


def execute():
	"""
	Deprecate Feedback Trigger and Rating. This feature was not customizable.
	Now can be achieved via custom Web Forms
	"""
	nxenv.delete_doc("DocType", "Feedback Trigger")
	nxenv.delete_doc("DocType", "Feedback Rating")
