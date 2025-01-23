// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

nxenv.ui.form.save = function (frm, action, callback, btn) {
	$(btn).prop("disabled", true);

	// specified here because there are keyboard shortcuts to save
	const working_label = {
		Save: __("Saving", null, "Freeze message while saving a document"),
		Submit: __("Submitting", null, "Freeze message while submitting a document"),
		Update: __("Updating", null, "Freeze message while updating a document"),
		Amend: __("Amending", null, "Freeze message while amending a document"),
		Cancel: __("Cancelling", null, "Freeze message while cancelling a document"),
	}[toTitle(action)];

	var freeze_message = working_label ? __(working_label) : "";

	var save = function () {
		$(frm.wrapper).addClass("validated-form");
		if ((action !== "Save" || frm.is_dirty()) && check_mandatory()) {
			_call({
				method: "nxenv.desk.form.save.savedocs",
				args: { doc: frm.doc, action: action },
				callback: function (r) {
					$(document).trigger("save", [frm.doc]);
					callback(r);
				},
				error: function (r) {
					callback(r);
				},
				btn: btn,
				freeze_message: freeze_message,
			});
		} else {
			!frm.is_dirty() &&
				nxenv.show_alert({ message: __("No changes in document"), indicator: "orange" });
			$(btn).prop("disabled", false);
		}
	};

	var cancel = function () {
		var args = {
			doctype: frm.doc.doctype,
			name: frm.doc.name,
		};

		// update workflow state value if workflow exists
		var workflow_state_fieldname = nxenv.workflow.get_state_fieldname(frm.doctype);
		if (workflow_state_fieldname) {
			$.extend(args, {
				workflow_state_fieldname: workflow_state_fieldname,
				workflow_state: frm.doc[workflow_state_fieldname],
			});
		}

		_call({
			method: "nxenv.desk.form.save.cancel",
			args: args,
			callback: function (r) {
				$(document).trigger("save", [frm.doc]);
				callback(r);
			},
			btn: btn,
			freeze_message: freeze_message,
		});
	};

	var check_mandatory = function () {
		var has_errors = false;
		frm.scroll_set = false;

		if (frm.doc.docstatus == 2) return true; // don't check for cancel

		$.each(nxenv.model.get_all_docs(frm.doc), function (i, doc) {
			var error_fields = [];
			var folded = false;

			$.each(nxenv.meta.docfield_list[doc.doctype] || [], function (i, docfield) {
				if (docfield.fieldname) {
					const df = nxenv.meta.get_docfield(doc.doctype, docfield.fieldname, doc.name);

					if (df.fieldtype === "Fold") {
						folded = frm.layout.folded;
					}

					if (
						is_docfield_mandatory(doc, df) &&
						!nxenv.model.has_value(doc.doctype, doc.name, df.fieldname)
					) {
						has_errors = true;
						error_fields[error_fields.length] = __(df.label, null, df.parent);
						// scroll to field
						if (!frm.scroll_set) {
							scroll_to(doc.parentfield || df.fieldname);
						}

						if (folded) {
							frm.layout.unfold();
							folded = false;
						}
					}
				}
			});

			if (frm.is_new() && frm.meta.autoname === "Prompt" && !frm.doc.__newname) {
				has_errors = true;
				error_fields = [__("Name"), ...error_fields];
			}

			if (error_fields.length) {
				let meta = nxenv.get_meta(doc.doctype);
				let message;
				if (meta.istable) {
					const table_field = nxenv.meta.docfield_map[doc.parenttype][doc.parentfield];

					const table_label = __(
						table_field.label || nxenv.unscrub(table_field.fieldname)
					).bold();

					message = __("Mandatory fields required in table {0}, Row {1}", [
						table_label,
						doc.idx,
					]);
				} else {
					message = __("Mandatory fields required in {0}", [__(doc.doctype)]);
				}
				message = message + "<br><br><ul><li>" + error_fields.join("</li><li>") + "</ul>";
				nxenv.msgprint({
					message: message,
					indicator: "red",
					title: __("Missing Fields"),
				});
				frm.refresh();
			}
		});

		return !has_errors;
	};

	let is_docfield_mandatory = function (doc, df) {
		if (df.reqd) return true;
		if (!df.mandatory_depends_on || !doc) return;

		let out = null;
		let expression = df.mandatory_depends_on;
		let parent = nxenv.get_meta(df.parent);

		if (typeof expression === "boolean") {
			out = expression;
		} else if (typeof expression === "function") {
			out = expression(doc);
		} else if (expression.substr(0, 5) == "eval:") {
			try {
				out = nxenv.utils.eval(expression.substr(5), { doc, parent });
				if (parent && parent.istable && expression.includes("is_submittable")) {
					out = true;
				}
			} catch (e) {
				nxenv.throw(__('Invalid "mandatory_depends_on" expression'));
			}
		} else {
			var value = doc[expression];
			if ($.isArray(value)) {
				out = !!value.length;
			} else {
				out = !!value;
			}
		}

		return out;
	};

	const scroll_to = (fieldname) => {
		frm.scroll_to_field(fieldname);
		frm.scroll_set = true;
	};

	var _call = function (opts) {
		// opts = {
		// 	method: "some server method",
		// 	args: {args to be passed},
		// 	callback: callback,
		// 	btn: btn
		// }

		if (nxenv.ui.form.is_saving) {
			// this is likely to happen if the user presses the shortcut cmd+s for a longer duration or uses double click
			// no need to show this to user, as they can see "Saving" in freeze message
			console.log("Already saving. Please wait a few moments.");
			throw "saving";
		}

		// ensure we remove new docs routes ONLY
		if (frm.is_new()) {
			nxenv.ui.form.remove_old_form_route();
		}
		nxenv.ui.form.is_saving = true;

		return nxenv.call({
			freeze: true,
			// freeze_message: opts.freeze_message,
			method: opts.method,
			args: opts.args,
			btn: opts.btn,
			callback: function (r) {
				opts.callback && opts.callback(r);
			},
			error: opts.error,
			always: function (r) {
				$(btn).prop("disabled", false);
				nxenv.ui.form.is_saving = false;

				if (r) {
					var doc = r.docs && r.docs[0];
					if (doc) {
						nxenv.ui.form.update_calling_link(doc);
					}
				}
			},
		});
	};

	if (action === "cancel") {
		cancel();
	} else {
		save();
	}
};

nxenv.ui.form.remove_old_form_route = () => {
	let current_route = nxenv.get_route().join("/");
	nxenv.route_history = nxenv.route_history.filter((route) => route.join("/") !== current_route);
};

nxenv.ui.form.update_calling_link = (newdoc) => {
	if (!nxenv._from_link) return;
	var doc = nxenv.get_doc(nxenv._from_link.doctype, nxenv._from_link.docname);

	let is_valid_doctype = () => {
		if (nxenv._from_link.df.fieldtype === "Link") {
			return newdoc.doctype === nxenv._from_link.df.options;
		} else {
			// dynamic link, type is dynamic
			return newdoc.doctype === doc[nxenv._from_link.df.options];
		}
	};

	if (is_valid_doctype()) {
		nxenv.model.with_doctype(newdoc.doctype, () => {
			let meta = nxenv.get_meta(newdoc.doctype);
			// set value
			if (doc && doc.parentfield) {
				//update values for child table
				$.each(
					nxenv._from_link.frm.fields_dict[doc.parentfield].grid.grid_rows,
					function (index, field) {
						if (field.doc && field.doc.name === nxenv._from_link.docname) {
							if (meta.title_field && meta.show_title_field_in_link) {
								nxenv.utils.add_link_title(
									newdoc.doctype,
									newdoc.name,
									newdoc[meta.title_field]
								);
							}
							nxenv._from_link.set_value(newdoc.name);
						}
					}
				);
			} else {
				if (meta.title_field && meta.show_title_field_in_link) {
					nxenv.utils.add_link_title(
						newdoc.doctype,
						newdoc.name,
						newdoc[meta.title_field]
					);
				}
				nxenv._from_link.set_value(newdoc.name);
			}

			// refresh field
			nxenv._from_link.refresh();

			// if from form, switch
			if (nxenv._from_link.frm) {
				nxenv
					.set_route("Form", nxenv._from_link.frm.doctype, nxenv._from_link.frm.docname)
					.then(() => {
						nxenv.utils.scroll_to(nxenv._from_link_scrollY);
					});
			}

			nxenv._from_link = null;
		});
	}
};
