# Copyright (c) 2017, Nxenv Technologies and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv.tests import IntegrationTestCase, UnitTestCase


class UnitTestLetterHead(UnitTestCase):
	"""
	Unit tests for LetterHead.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestLetterHead(IntegrationTestCase):
	def test_auto_image(self):
		letter_head = nxenv.get_doc(
			doctype="Letter Head", letter_head_name="Test", source="Image", image="/public/test.png"
		).insert()

		# test if image is automatically set
		self.assertTrue(letter_head.image in letter_head.content)
