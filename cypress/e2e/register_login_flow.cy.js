describe("Register to login flow", () => {
  const randomEmail = `user${Date.now()}@example.com`; // unique email for register

  beforeEach(() => {
    cy.visit("http://localhost:8501/Login");
  });

  it("can register a new user and see success message", () => {

    cy.get('[data-testid="stTab"]').contains('Register').click();


    cy.get('[role="tabpanel"]:visible').within(() => {
      cy.get('input[placeholder="Your name"]').type('Test User');
      cy.get('input[placeholder="user@example.com"]').type(randomEmail);
      cy.get('input[placeholder="Create a password"]').type('pass');

   
      cy.contains('button', 'CREATE ACCOUNT').click();

      
      cy.contains("Successfully registered").should('be.visible');
    });
  });

  it("can log in with the registered user and see dashboard redirect", () => {
   
    cy.get('[data-testid="stTab"]').contains('Login').click();


    cy.get('[role="tabpanel"]:visible').within(() => {
      cy.get('input[placeholder="user@example.com"]').type(randomEmail);
      cy.get('input[placeholder="password"]').type('pass');

      cy.contains('button', 'LOGIN').click();

      cy.url().should('eq', 'http://localhost:8501/'); 
    });
  });
});