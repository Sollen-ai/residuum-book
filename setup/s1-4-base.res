module Biblioteca

entity Person
entity Thing

const ana : Person
const book : Thing
const tau : PropositionTime

seeded verb requests(subject : Person, object : Thing)
seeded verb available(object : Thing)
derived verb lent(subject : Person, object : Thing)

rule lending(person, object, t) =
    requests(person, object) @ t & available(object) @ t <= lent(person, object) @ t
