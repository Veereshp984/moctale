/// <reference types="cypress" />

describe('Content discovery happy path', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('supports discovery, playlist management, and social sharing', () => {
    cy.findByTestId('discovery-section').within(() => {
      cy.findAllByTestId('media-card').should('have.length.greaterThan', 0)
      cy.findAllByTestId('media-card-add').first().should('not.be.disabled').click()
    })

    cy.findByTestId('metric-item-count').should('contain', '1')
    cy.findByTestId('playlist-items').children().should('have.length', 1)

    cy.contains('button', 'Music').click()
    cy.findByTestId('discovery-section').within(() => {
      cy.findAllByTestId('media-card-add').first().should('not.be.disabled').click()
    })

    cy.findByTestId('metric-item-count').should('contain', '2')
    cy.findByTestId('playlist-items').children().should('have.length', 2)

    cy.findAllByTestId('move-item-down').first().click()

    cy.findByTestId('save-playlist').should('be.enabled').click()
    cy.contains('Saved!').should('be.visible')

    cy.findByTestId('playlist-public-toggle').check({ force: true })
    cy.findByTestId('share-controls').should('exist')

    cy.findByTestId('save-playlist').click()
    cy.contains('Saved!').should('be.visible')

    cy.findByTestId('share-link-input')
      .invoke('val')
      .then((value) => {
        expect(value).to.be.a('string').and.to.contain('/playlist/')
        return cy.visit(value as string)
      })

    cy.findByTestId('public-playlist').within(() => {
      cy.contains('Shared playlist').should('exist')
      cy.contains('Build your playlist').should('exist')
    })
  })
})
