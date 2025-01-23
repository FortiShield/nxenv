# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

"""docfield utililtes"""

import nxenv


def supports_translation(fieldtype):
	return fieldtype in ["Data", "Select", "Text", "Small Text", "Text Editor"]
