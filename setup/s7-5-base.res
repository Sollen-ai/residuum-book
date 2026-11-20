module Errores

entity Thing
entity Person {
    assets : Set Thing
}

const juan : Person
const pedro : Person
const car : Thing
const tau : PropositionTime

seeded verb sells(subject : Person, object : Thing, recipient : Person)
derived verb owns(owner : Person, object : Thing)
