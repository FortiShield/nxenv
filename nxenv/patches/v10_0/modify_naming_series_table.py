"""
Modify the Integer 10 Digits Value to BigInt 20 Digit value
to generate long Naming Series

"""

import nxenv


def execute():
	nxenv.db.sql(""" ALTER TABLE `tabSeries` MODIFY current BIGINT """)
