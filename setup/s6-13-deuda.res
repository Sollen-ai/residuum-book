module Deuda

entity Person
entity Thing

const ana : Person
const bob : Person
const car : Thing
const tau : PropositionTime

seeded verb agrees(seller : Person, object : Thing, buyer : Person)
seeded verb pays(buyer : Person, object : Thing, seller : Person)
derived verb owes(seller : Person, object : Thing, buyer : Person)

// El acuerdo y el pago implican la deuda de entrega en el instante siguiente.
rule sale(seller, object, buyer, t) =
    agrees(seller, object, buyer) @ t & pays(buyer, object, seller) @ t
    <= owes(seller, object, buyer) @ after t
