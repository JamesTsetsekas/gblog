// Specifications and a bounded exhaustive checker.
//
// A property receives (total, weights, parts) and returns true when the
// output is acceptable. Exact BigInt arithmetic avoids floating-point noise
// in the specification itself.

function sumBig(values) {
    return values.reduce((a, b) => a + BigInt(b), 0n)
}

export function shape(total, weights, parts) {
    return Array.isArray(parts) && parts.length === weights.length
}

export function nonNegativeIntegers(total, weights, parts) {
    return parts.every(p => Number.isSafeInteger(p) && p >= 0)
}

export function conservation(total, weights, parts) {
    return sumBig(parts) === BigInt(total)
}

// Each part is the floor or the ceiling of its exact proportional share:
// |part * sum - total * weight| < sum.
export function proportional(total, weights, parts) {
    const sum = sumBig(weights)
    const t = BigInt(total)
    return weights.every((w, i) => {
        const diff = BigInt(parts[i]) * sum - t * BigInt(w)
        return (diff < 0n ? -diff : diff) < sum
    })
}

// The extra units go to the largest fractional remainders, ties to the lower
// index. This pins down one specific apportionment rule.
export function largestRemainderRule(total, weights, parts) {
    const sum = sumBig(weights)
    const t = BigInt(total)
    const remainders = weights.map(w => (t * BigInt(w)) % sum)
    const roundedUp = weights.map((w, i) => BigInt(parts[i]) * sum > t * BigInt(w))
    for (let i = 0; i < weights.length; i++) {
        for (let j = 0; j < weights.length; j++) {
            if (roundedUp[i] && !roundedUp[j]) {
                const beats = remainders[i] > remainders[j]
                    || (remainders[i] === remainders[j] && i < j)
                if (!beats) {
                    return false
                }
            }
        }
    }
    return true
}

// A weak specification: right length, and no part exceeds the total.
export function weakSpec(total, weights, parts) {
    return shape(total, weights, parts) && parts.every(p => p <= total)
}

export const strongSpec = [shape, nonNegativeIntegers, conservation, proportional]

// A guarded property whose guard can never be true. It "passes" for any
// implementation, which is exactly the problem.
export function impossibleGuard(total, weights) {
    return weights.length > 3 && weights.length < 2
}

export function vacuousConservation(total, weights, parts) {
    if (impossibleGuard(total, weights)) {
        return conservation(total, weights, parts)
    }
    return true
}

// Every (total, weights) pair with 0 <= total <= maxTotal, 1 <= length <=
// maxLength and 1 <= weight <= maxWeight, in a fixed order: total first,
// then length, then weights lexicographically.
export function* boundedDomain({ maxTotal, maxLength, maxWeight }) {
    for (let total = 0; total <= maxTotal; total++) {
        for (let length = 1; length <= maxLength; length++) {
            const weights = Array.from({ length }, () => 1)
            while (true) {
                yield { total, weights: [...weights] }
                let k = length - 1
                while (k >= 0 && weights[k] === maxWeight) {
                    weights[k] = 1
                    k--
                }
                if (k < 0) {
                    break
                }
                weights[k]++
            }
        }
    }
}

// Run every property on every input in the domain. Returns the number of
// cases and the first counterexample in domain order, or null.
export function checkBounded(impl, properties, domain) {
    let cases = 0
    for (const { total, weights } of boundedDomain(domain)) {
        cases++
        const parts = impl(total, weights)
        for (const property of properties) {
            if (!property(total, weights, parts)) {
                return { cases, counterexample: { total, weights, parts, property: property.name } }
            }
        }
    }
    return { cases, counterexample: null }
}

// Count how many inputs in the domain satisfy a guard. Zero means any
// property hidden behind that guard was never exercised.
export function countGuardHits(guard, domain) {
    let hits = 0
    for (const { total, weights } of boundedDomain(domain)) {
        if (guard(total, weights)) {
            hits++
        }
    }
    return hits
}
