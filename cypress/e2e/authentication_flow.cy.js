describe("Authentication Flow", () => {
  let testUser;

  // Load user fixture before all tests
  before(() => {
    cy.fixture("users.json").then((user) => {
      testUser = user;
    });
  });

  beforeEach(() => {
    cy.visit("/Login");
  });

  it("Unauthorized user visits, redirect to login", () => {
    cy.visit("/");

    cy.url().should("include", "/Login");
  });

  it("cannot login with invalid credentials", () => {
    cy.get('[data-testid="stTab"]').contains("Login").click();

    cy.get('[role="tabpanel"]:visible').within(() => {
      cy.get('input[placeholder="user@example.com"]').type("random@example.com");
      cy.get('input[placeholder="password"]').type("1231231232");

      cy.contains("button", "LOGIN").click();

      cy.contains("Login failed (401)").should("be.visible");
    });
  });

  it("can log in with the registered user from fixture and see dashboard redirect", () => {
    cy.get('[data-testid="stTab"]').contains("Login").click();

    cy.get('[role="tabpanel"]:visible').within(() => {
      cy.get('input[placeholder="user@example.com"]').type(testUser.email);
      cy.get('input[placeholder="password"]').type(testUser.password);

      cy.contains("button", "LOGIN").click();

      cy.url().should("include", "/");
    });
  });
});