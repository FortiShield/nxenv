import nxenv


def execute():
	nxenv.reload_doctype("Comment")

	if nxenv.db.count("Feedback") > 20000:
		nxenv.db.auto_commit_on_many_writes = True

	for feedback in nxenv.get_all("Feedback", fields=["*"]):
		if feedback.like:
			new_comment = nxenv.new_doc("Comment")
			new_comment.comment_type = "Like"
			new_comment.comment_email = feedback.owner
			new_comment.content = "Liked by: " + feedback.owner
			new_comment.reference_doctype = feedback.reference_doctype
			new_comment.reference_name = feedback.reference_name
			new_comment.creation = feedback.creation
			new_comment.modified = feedback.modified
			new_comment.owner = feedback.owner
			new_comment.modified_by = feedback.modified_by
			new_comment.ip_address = feedback.ip_address
			new_comment.db_insert()

	if nxenv.db.auto_commit_on_many_writes:
		nxenv.db.auto_commit_on_many_writes = False

	# clean up
	nxenv.db.delete("Feedback")
	nxenv.db.commit()

	nxenv.delete_doc("DocType", "Feedback")
