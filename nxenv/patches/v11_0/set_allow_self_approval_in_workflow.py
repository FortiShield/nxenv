import nxenv


def execute():
	nxenv.reload_doc("workflow", "doctype", "workflow_transition")
	nxenv.db.sql("update `tabWorkflow Transition` set allow_self_approval=1")
