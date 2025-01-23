import nxenv


def execute():
	nxenv.reload_doctype("Translation")
	nxenv.db.sql(
		"UPDATE `tabTranslation` SET `translated_text`=`target_name`, `source_text`=`source_name`, `contributed`=0"
	)
