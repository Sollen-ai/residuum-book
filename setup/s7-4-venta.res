module VentaEjecutada

entity Thing
entity Person {
    assets : Set Thing
}

const juan : Person
const pedro : Person
const charlie : Person
const car : Thing
const tau : PropositionTime

seeded verb sells(subject : Person, object : Thing, recipient : Person)

effect verb give(subject : Person, object : Thing, recipient : Person) =>
    subject.assets -= object
    recipient.assets += object

// Una venta en t produce la entrega en el instante siguiente.
rule delivery(seller, object, buyer, t) =
    sells(seller, object, buyer) @ t
    <= give(seller, object, buyer) @ after t
