# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	nxenv.delete_doc("DocType", "Package Publish Tool", ignore_missing=True)
	nxenv.delete_doc("DocType", "Package Document Type", ignore_missing=True)
	nxenv.delete_doc("DocType", "Package Publish Target", ignore_missing=True)
