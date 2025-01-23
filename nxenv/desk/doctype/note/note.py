# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document

UNSEEN_NOTES_KEY = "unseen_notes::"


class Note(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.desk.doctype.note_seen_by.note_seen_by import NoteSeenBy
		from nxenv.types import DF

		content: DF.TextEditor | None
		expire_notification_on: DF.Date | None
		notify_on_every_login: DF.Check
		notify_on_login: DF.Check
		public: DF.Check
		seen_by: DF.Table[NoteSeenBy]
		title: DF.Data
	# end: auto-generated types

	def validate(self):
		if self.notify_on_login and not self.expire_notification_on:
			# expire this notification in a week (default)
			self.expire_notification_on = nxenv.utils.add_days(self.creation, 7)

		if not self.public and self.notify_on_login:
			self.notify_on_login = 0

		if not self.content:
			self.content = "<span></span>"

	def before_print(self, settings=None):
		self.print_heading = self.name
		self.sub_heading = ""

	def clear_cache(self):
		nxenv.cache.delete_keys(UNSEEN_NOTES_KEY)
		return super().clear_cache()

	def mark_seen_by(self, user: str) -> None:
		if user in [d.user for d in self.seen_by]:
			return

		self.append("seen_by", {"user": user})


@nxenv.whitelist()
def mark_as_seen(note: str):
	note: Note = nxenv.get_doc("Note", note)
	note.mark_seen_by(nxenv.session.user)
	note.save(ignore_permissions=True, ignore_version=True)


def get_permission_query_conditions(user):
	if not user:
		user = nxenv.session.user

	return f"(`tabNote`.owner = {nxenv.db.escape(user)} or `tabNote`.public = 1)"


def has_permission(doc, user):
	return bool(doc.public or doc.owner == user)


def get_unseen_notes():
	from nxenv.query_builder.terms import ParameterizedValueWrapper, SubQuery

	def _get_unseen_notes():
		note = nxenv.qb.DocType("Note")
		nsb = nxenv.qb.DocType("Note Seen By").as_("nsb")

		return (
			nxenv.qb.from_(note)
			.select(note.name, note.title, note.content, note.notify_on_every_login)
			.where(
				(note.notify_on_login == 1)
				& (note.expire_notification_on > nxenv.utils.now())
				& (
					ParameterizedValueWrapper(nxenv.session.user).notin(
						SubQuery(nxenv.qb.from_(nsb).select(nsb.user).where(nsb.parent == note.name))
					)
				)
			)
		).run(as_dict=1)

	return (
		nxenv.cache.get_value(
			f"{UNSEEN_NOTES_KEY}{nxenv.session.user}",
			generator=_get_unseen_notes,
		)
		or []
	)
