# Copyright (c) 2018, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	nxenv.db.set_value("Currency", "USD", "smallest_currency_fraction_value", "0.01")
