// Finite unary addition. Input spines contain no addition table.
// In this experiment only: Z = zeroTime, S(x) = after(x).
module PeanoAfter

entity Natural
entity Cursor
entity Request

const zeroTime : PropositionTime
const nZero : Natural
const nOne : Natural
const nTwo : Natural
const nThree : Natural
const nFour : Natural
const cZero : Cursor
const cOne : Cursor
const cTwo : Cursor
const cThree : Cursor
const cFour : Cursor
const r00 : Request
const r01 : Request
const r02 : Request
const r03 : Request
const r04 : Request
const r10 : Request
const r11 : Request
const r12 : Request
const r13 : Request
const r14 : Request
const r20 : Request
const r21 : Request
const r22 : Request
const r23 : Request
const r24 : Request
const r30 : Request
const r31 : Request
const r32 : Request
const r33 : Request
const r34 : Request
const r40 : Request
const r41 : Request
const r42 : Request
const r43 : Request
const r44 : Request

seeded verb start(number : Natural, cursor : Cursor)
seeded verb successor(number : Natural, cursor : Cursor, next : Cursor)
seeded verb end(number : Natural, cursor : Cursor)
seeded verb add(left : Natural, right : Natural, request : Request) = program Addition

derived verb leftWalk(left : Natural, right : Natural, request : Request, cursor : Cursor) = program LeftWalk
derived verb rightWalk(right : Natural, request : Request, cursor : Cursor) = program RightWalk
derived verb sum(request : Request)
derived verb completed(request : Request)

rule initialize(left, right, request, cursor, t) =
    add(left, right, request) @ t
    & start(left, cursor) @ zeroTime
    <= leftWalk(left, right, request, cursor) @ t

rule leftSuccessor(left, right, request, cursor, next, t) =
    leftWalk(left, right, request, cursor) @ t
    & successor(left, cursor, next) @ zeroTime
    <= leftWalk(left, right, request, next) @ after t

rule changePhase(left, right, request, cursor, first, t) =
    leftWalk(left, right, request, cursor) @ t
    & end(left, cursor) @ zeroTime
    & start(right, first) @ zeroTime
    <= rightWalk(right, request, first) @ t

rule rightSuccessor(right, request, cursor, next, t) =
    rightWalk(right, request, cursor) @ t
    & successor(right, cursor, next) @ zeroTime
    <= rightWalk(right, request, next) @ after t

rule finish(right, request, cursor, t) =
    rightWalk(right, request, cursor) @ t
    & end(right, cursor) @ zeroTime
    <= sum(request) @ t

// Completion observation stays at zeroTime; the numeric result is sum's index.
rule observe(request, t) = sum(request) @ t <= completed(request) @ zeroTime

program Addition(left : Natural, right : Natural, request : Request, t : PropositionTime) {
    use initialize { left = left, right = right, request = request, t = t }
}
program LeftWalk(left : Natural, right : Natural, request : Request, cursor : Cursor, t : PropositionTime) {
    use leftSuccessor { left = left, right = right, request = request, cursor = cursor, t = t }
    use changePhase { left = left, right = right, request = request, cursor = cursor, t = t }
}
program RightWalk(right : Natural, request : Request, cursor : Cursor, t : PropositionTime) {
    use rightSuccessor { right = right, request = request, cursor = cursor, t = t }
    use finish { right = right, request = request, cursor = cursor, t = t }
}

// Actual partial application and temporal beta reduction, using v1 syntax.
program LeftTwo = LeftWalk(nTwo)
program LeftTwoThree = LeftTwo(nThree)
program LeftGround = LeftTwoThree(r23, cZero, zeroTime)
program LeftDirect = LeftWalk(nTwo, nThree, r23, cZero, zeroTime)

