module Alquiler

entity Person
entity Flat

const lena : Person
const omar : Person
const attic : Flat
const tau : PropositionTime

seeded verb signs(tenant : Person, flat : Flat, landlord : Person)
seeded verb paysDeposit(tenant : Person, flat : Flat, landlord : Person)
derived verb handsKeys(landlord : Person, flat : Flat, tenant : Person)

rule keys(tenant, flat, landlord, t) =
    signs(tenant, flat, landlord) @ t & paysDeposit(tenant, flat, landlord) @ t
    <= handsKeys(landlord, flat, tenant) @ after t
