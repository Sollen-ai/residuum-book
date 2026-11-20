module Escalera

const tau : PropositionTime

seeded verb s0()
derived verb s1()
derived verb s2()
derived verb s3()
derived verb s4()
derived verb s5()
derived verb s6()
derived verb s7()
derived verb s8()
derived verb s9()
derived verb s10()
derived verb s11()
derived verb s12()
derived verb s13()
derived verb s14()
derived verb s15()
derived verb s16()

// Una cadena acíclica: cada regla sube un escalón.
rule r1() = s0() @ tau <= s1() @ tau
rule r2() = s1() @ tau <= s2() @ tau
rule r3() = s2() @ tau <= s3() @ tau
rule r4() = s3() @ tau <= s4() @ tau
rule r5() = s4() @ tau <= s5() @ tau
rule r6() = s5() @ tau <= s6() @ tau
rule r7() = s6() @ tau <= s7() @ tau
rule r8() = s7() @ tau <= s8() @ tau
rule r9() = s8() @ tau <= s9() @ tau
rule r10() = s9() @ tau <= s10() @ tau
rule r11() = s10() @ tau <= s11() @ tau
rule r12() = s11() @ tau <= s12() @ tau
rule r13() = s12() @ tau <= s13() @ tau
rule r14() = s13() @ tau <= s14() @ tau
rule r15() = s14() @ tau <= s15() @ tau
rule r16() = s15() @ tau <= s16() @ tau
