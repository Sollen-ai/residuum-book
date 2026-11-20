module Venta

entity Thing
entity Person {
    assets : Set Thing
}

const alice : Person
const bob : Person
const car : Thing
const tau : PropositionTime

seeded verb agreesPrice(subject : Person, object : Thing, recipient : Person)
seeded verb agreesObject(subject : Person, object : Thing, recipient : Person)
seeded verb donates(subject : Person, object : Thing, recipient : Person)

effect verb give(subject : Person, object : Thing, recipient : Person) =>
    subject.assets -= object
    recipient.assets += object

// Cláusula residual: dado el acuerdo de precio, falta el de objeto.
rule sales(debtor, object, creditor, t) =
    agreesPrice(debtor, object, creditor) @ t
    <= agreesObject(creditor, object, debtor) @ t
    -o give(debtor, object, creditor) @ after t

// Cláusula de Horn: una donación también produce la entrega.
rule gift(donor, object, donee, t) =
    donates(donor, object, donee) @ t <= give(donor, object, donee) @ after t
