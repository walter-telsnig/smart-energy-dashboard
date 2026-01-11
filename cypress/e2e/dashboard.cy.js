describe('Dashboard sanity', () => {
  let testUser;

  // Load user fixture before all tests
  before(() => {
    cy.fixture("users.json").then((user) => {
      testUser = user;
    });
  });


  beforeEach(() => {
    cy.visit("/Login");

    cy.get('[data-testid="stTab"]').contains('Login').click();

    cy.get('[role="tabpanel"]:visible').within(() => {
      cy.get('input[placeholder="user@example.com"]').type(testUser.email);
      cy.get('input[placeholder="password"]').type(testUser.password);

      cy.contains('button', 'LOGIN').click();
    });

    // Ensure dashboard loaded
    cy.url().should('include', '/');
  });

  it('should display dashboard overview header', () => {
    cy.contains('h1', 'Dashboard Overview').should('be.visible');
  } );

  it('should display KPI Cards', () => {
    cy.get('.kpi-card').should('have.length', 4);

    cy.get('.kpi-card').contains('PV (latest)').should('be.visible');
    cy.get('.kpi-card').contains('Consumption (latest)').should('be.visible');
    cy.get('.kpi-card').contains('Price (latest)').should('be.visible');
    cy.get('.kpi-card').contains('Self-sufficiency').should('be.visible');
  } );

  it('should have a sidebar with expected links', () => {
    cy.get('section[data-testid="stSidebar"]').should('be.visible');
    cy.get('section[data-testid="stSidebar"]').within(() => {

      cy.contains('PV').should('be.visible');
      cy.contains('Prices').should('be.visible');
      cy.contains('Consumption').should('be.visible');
      cy.contains('Compare').should('be.visible');
      cy.contains('Recommendations').should('be.visible');


    });
  } );
})


