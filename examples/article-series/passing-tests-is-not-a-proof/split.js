// Toy code for "Passing Tests Is Not a Proof".
//
// Split an integer amount (think satoshis) across recipients in proportion
// to positive integer weights. Two implementations and three deliberately
// broken "mutants" live here so the tests can compare them against a
// specification.

export function assertValidInput(total, weights) {
    if (!Number.isSafeInteger(total) || total < 0) {
        throw new RangeError('total must be a non-negative safe integer')
    }
    if (!Array.isArray(weights) || weights.length === 0) {
        throw new RangeError('weights must be a non-empty array')
    }
    for (const w of weights) {
        if (!Number.isSafeInteger(w) || w <= 0) {
            throw new RangeError('every weight must be a positive safe integer')
        }
    }
}

// The plausible first draft: scale and round each share independently.
export function splitRounded(total, weights) {
    assertValidInput(total, weights)
    const sum = weights.reduce((a, b) => a + b, 0)
    return weights.map(w => Math.round(total * w / sum))
}

// Exact integer arithmetic. Give everyone the floor of their exact share,
// then hand the leftover units to the largest remainders (ties go to the
// lower index).
function largestRemainderParts(total, weights, { distributeLeftover = true, leftoverToFirst = false, fractionalOnly = false } = {}) {
    assertValidInput(total, weights)
    const t = BigInt(total)
    const ws = weights.map(w => BigInt(w))
    const sum = ws.reduce((a, b) => a + b, 0n)
    const parts = ws.map(w => (t * w) / sum)
    const remainders = ws.map(w => (t * w) % sum)
    let leftover = t - parts.reduce((a, b) => a + b, 0n)

    let order = ws.map((_, i) => i)
    if (fractionalOnly) {
        order = order.filter(i => remainders[i] > 0n)
    }
    if (!leftoverToFirst) {
        order.sort((i, j) => {
            if (remainders[i] === remainders[j]) {
                return i - j
            }
            return remainders[j] > remainders[i] ? 1 : -1
        })
    }

    if (distributeLeftover) {
        for (const i of order) {
            if (leftover === 0n) {
                break
            }
            parts[i] += 1n
            leftover -= 1n
        }
    }
    return parts.map(p => Number(p))
}

export function splitLargestRemainder(total, weights) {
    return largestRemainderParts(total, weights)
}

// Mutant 1: forgets to distribute the leftover units.
export function mutantFloorsOnly(total, weights) {
    return largestRemainderParts(total, weights, { distributeLeftover: false })
}

// Mutant 2: rounds every share up.
export function mutantCeilAll(total, weights) {
    assertValidInput(total, weights)
    const sum = weights.reduce((a, b) => a + b, 0)
    return weights.map(w => Math.ceil(total * w / sum))
}

// Mutant 3: hands leftover units to the first recipients instead of the
// largest remainders, even to a recipient whose share was already exact.
export function mutantLeftoverToFirst(total, weights) {
    return largestRemainderParts(total, weights, { leftoverToFirst: true })
}

// Mutant 4: hands leftover units to the first recipients that have a
// fractional share. Every part is still a floor or a ceiling of its exact
// share, so whether this is a bug depends on the requirement.
export function mutantLeftoverToFirstFractional(total, weights) {
    return largestRemainderParts(total, weights, { leftoverToFirst: true, fractionalOnly: true })
}
