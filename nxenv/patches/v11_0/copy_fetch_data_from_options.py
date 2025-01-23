import nxenv


def execute():
	nxenv.reload_doc("core", "doctype", "docfield", force=True)
	nxenv.reload_doc("custom", "doctype", "custom_field", force=True)
	nxenv.reload_doc("custom", "doctype", "customize_form_field", force=True)
	nxenv.reload_doc("custom", "doctype", "property_setter", force=True)

	nxenv.db.sql(
		"""
		update `tabDocField`
		set fetch_from = options, options=''
		where options like '%.%' and (fetch_from is NULL OR fetch_from='')
 		and fieldtype in ('Data', 'Read Only', 'Text', 'Small Text', 'Text Editor', 'Code', 'Link', 'Check')
 		and fieldname!='naming_series'
	"""
	)

	nxenv.db.sql(
		"""
		update `tabCustom Field`
		set fetch_from = options, options=''
		where options like '%.%' and (fetch_from is NULL OR fetch_from='')
 		and fieldtype in ('Data', 'Read Only', 'Text', 'Small Text', 'Text Editor', 'Code', 'Link', 'Check')
 		and fieldname!='naming_series'
	"""
	)

	nxenv.db.sql(
		"""
		update `tabProperty Setter`
		set property="fetch_from", name=concat(doc_type, '-', field_name, '-', property)
		where property="options" and value like '%.%'
		and property_type in ('Data', 'Read Only', 'Text', 'Small Text', 'Text Editor', 'Code', 'Link', 'Check')
		and field_name!='naming_series'
	"""
	)
