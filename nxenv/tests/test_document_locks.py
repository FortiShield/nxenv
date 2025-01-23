# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv.tests import IntegrationTestCase
from nxenv.utils.data import add_to_date, today


class TestDocumentLocks(IntegrationTestCase):
	def test_locking(self):
		todo = nxenv.get_doc(doctype="ToDo", description="test").insert()
		todo_1 = nxenv.get_doc("ToDo", todo.name)

		todo.lock()
		self.assertRaises(nxenv.DocumentLockedError, todo_1.lock)
		todo.unlock()

		todo_1.lock()
		self.assertRaises(nxenv.DocumentLockedError, todo.lock)
		todo_1.unlock()

	def test_operations_on_locked_documents(self):
		todo = nxenv.get_doc(doctype="ToDo", description="testing operations").insert()
		todo.lock()

		with self.assertRaises(nxenv.DocumentLockedError):
			todo.description = "Random"
			todo.save()

		# Checking for persistant locks across all instances.
		doc = nxenv.get_doc("ToDo", todo.name)
		self.assertEqual(doc.is_locked, True)

		with self.assertRaises(nxenv.DocumentLockedError):
			doc.description = "Random"
			doc.save()

		doc.unlock()
		self.assertEqual(doc.is_locked, False)
		self.assertEqual(todo.is_locked, False)

	def test_locks_auto_expiry(self):
		todo = nxenv.get_doc(doctype="ToDo", description=nxenv.generate_hash()).insert()
		todo.lock()

		self.assertRaises(nxenv.DocumentLockedError, todo.lock)

		with self.freeze_time(add_to_date(today(), days=3)):
			todo.lock()
