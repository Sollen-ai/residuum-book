module Prestamo

entity Person
entity Thing

const ana : Person
const book : Thing
const tau : PropositionTime

seeded verb requests(subject : Person, object : Thing)
seeded verb available(object : Thing)
derived verb lent(subject : Person, object : Thing)
