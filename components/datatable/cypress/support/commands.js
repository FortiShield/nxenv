// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This is will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })

Cypress.Commands.add("getCell", (col, row) => {
	return cy.get(`.dt-cell--${col}-${row}`);
});

Cypress.Commands.add("clickCell", (col, row) => {
	return cy.getCell(col, row).click({ force: true });
});

Cypress.Commands.add("getColumnCell", (col) => {
	return cy.get(`.dt-cell--header-${col}`);
});

Cypress.Commands.add("clickDropdown", (col) => {
	return cy.getColumnCell(col).find(".dt-dropdown__toggle").click();
});

Cypress.Commands.add("clickDropdownItem", (col, item) => {
	return cy.get(`.dt-dropdown__list-item:contains("${item}")`).click({ force: true });
});

Cypress.Commands.add("typeTab", (shiftKey, ctrlKey) => {
	cy.focused().trigger("keydown", {
		keyCode: 9,
		which: 9,
		shiftKey: shiftKey,
		ctrlKey: ctrlKey,
	});
});
