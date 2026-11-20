module FourScoped

entity Person

const alice : Person
const bob : Person
const tau : PropositionTime

derived verb Notified(person : Person)
derived verb Served(person : Person)

// Ser atendido implica haber sido notificado.
rule service(person, t) =
    Served(person) @ t <= Notified(person) @ t
