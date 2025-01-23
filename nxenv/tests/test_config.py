# Copyright (c) 2022, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import nxenv
from nxenv.tests import IntegrationTestCase
from nxenv.utils.modules import get_modules_from_all_apps_for_user


class TestConfig(IntegrationTestCase):
	def test_get_modules(self):
		nxenv_modules = nxenv.get_all("Module Def", filters={"app_name": "nxenv"}, pluck="name")
		all_modules_data = get_modules_from_all_apps_for_user()
		all_modules = [x["module_name"] for x in all_modules_data]
		self.assertIsInstance(all_modules_data, list)
		self.assertFalse([x for x in nxenv_modules if x not in all_modules])
