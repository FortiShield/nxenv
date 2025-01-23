"""
Run this after updating country_info.json and or
"""

import nxenv


def execute():
	for col in ("field", "doctype"):
		nxenv.db.sql_ddl(f"alter table `tabSingles` modify column `{col}` varchar(255)")
