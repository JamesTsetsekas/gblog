import assert from 'node:assert/strict'
// eslint-disable-next-line test/no-import-node-test -- examples use Node's built-in runner; the repo has no test framework dependency
import { describe, it } from 'node:test'
import {
    checkBounded,
    conservation,
    countGuardHits,
    impossibleGuard,
    largestRemainderRule,
    proportional,
    strongSpec,
    vacuousConservation,
    weakSpec,
} from './spec.js'
import {
    assertValidInput,
    mutantCeilAll,
    mutantFloorsOnly,
    mutantLeftoverToFirst,
    mutantLeftoverToFirstFractional,
    splitLargestRemainder,
    splitRounded,
} from './split.js'

// 61 totals x (6 + 36 + 216) weight vectors = 15,738 inputs.
const DOMAIN = { maxTotal: 60, maxLength: 3, maxWeight: 6 }
const DOMAIN_SIZE = 15738

describe('example-based tests', () => {
    const examples = [
        { total: 100, weights: [1, 1], expected: [50, 50] },
        { total: 90, weights: [1, 2], expected: [30, 60] },
        { total: 10, weights: [1, 1, 3], expected: [2, 2, 6] },
    ]

    it('pass for the rounded first draft', () => {
        for (const { total, weights, expected } of examples) {
            assert.deepEqual(splitRounded(total, weights), expected)
        }
    })

    it('pass for the largest-remainder version', () => {
        for (const { total, weights, expected } of examples) {
            assert.deepEqual(splitLargestRemainder(total, weights), expected)
        }
    })
})

describe('bounded exhaustive check against the strong specification', () => {
    it('finds the smallest counterexample to the rounded draft', () => {
        const result = checkBounded(splitRounded, strongSpec, DOMAIN)
        assert.deepEqual(result.counterexample, {
            total: 1,
            weights: [1, 1],
            parts: [1, 1],
            property: 'conservation',
        })
    })

    it('shows the draft can also lose units: 100 split three ways', () => {
        const parts = splitRounded(100, [1, 1, 1])
        assert.deepEqual(parts, [33, 33, 33])
        assert.equal(conservation(100, [1, 1, 1], parts), false)
    })

    it('finds no counterexample to the largest-remainder version in the domain', () => {
        const result = checkBounded(splitLargestRemainder, [...strongSpec, largestRemainderRule], DOMAIN)
        assert.equal(result.cases, DOMAIN_SIZE)
        assert.equal(result.counterexample, null)
    })

    it('stays exact at bitcoin-scale totals outside the bounded domain', () => {
        const total = 2_100_000_000_000_000
        for (const weights of [[1, 1, 1], [3, 7, 11], [1, 999_999]]) {
            const parts = splitLargestRemainder(total, weights)
            assert.ok(conservation(total, weights, parts))
            assert.ok(proportional(total, weights, parts))
        }
    })
})

describe('specification strength', () => {
    it('a weak specification accepts the broken draft on every input', () => {
        const result = checkBounded(splitRounded, [weakSpec], DOMAIN)
        assert.equal(result.cases, DOMAIN_SIZE)
        assert.equal(result.counterexample, null)
    })

    it('the weak specification rejects none of the four mutants', () => {
        for (const mutant of [mutantFloorsOnly, mutantCeilAll, mutantLeftoverToFirst, mutantLeftoverToFirstFractional]) {
            assert.equal(checkBounded(mutant, [weakSpec], DOMAIN).counterexample, null, mutant.name)
        }
    })

    it('the strong specification rejects three of four mutants', () => {
        const floors = checkBounded(mutantFloorsOnly, strongSpec, DOMAIN)
        assert.equal(floors.counterexample.property, 'conservation')

        const ceil = checkBounded(mutantCeilAll, strongSpec, DOMAIN)
        assert.equal(ceil.counterexample.property, 'conservation')

        const first = checkBounded(mutantLeftoverToFirst, strongSpec, DOMAIN)
        assert.deepEqual(first.counterexample, {
            total: 2,
            weights: [2, 1, 1],
            parts: [2, 0, 0],
            property: 'proportional',
        })

        const fractional = checkBounded(mutantLeftoverToFirstFractional, strongSpec, DOMAIN)
        assert.equal(fractional.cases, DOMAIN_SIZE)
        assert.equal(fractional.counterexample, null)
    })

    it('the surviving mutant is only caught by an explicit apportionment rule', () => {
        const result = checkBounded(mutantLeftoverToFirstFractional, [...strongSpec, largestRemainderRule], DOMAIN)
        assert.deepEqual(result.counterexample, {
            total: 1,
            weights: [1, 2],
            parts: [1, 0],
            property: 'largestRemainderRule',
        })
    })
})

describe('vacuity', () => {
    it('a property behind an impossible guard accepts nonsense', () => {
        const nonsense = () => [999]
        const result = checkBounded(nonsense, [vacuousConservation], DOMAIN)
        assert.equal(result.counterexample, null)
    })

    it('a witness count exposes the impossible guard', () => {
        assert.equal(countGuardHits(impossibleGuard, DOMAIN), 0)
    })

    it('the real precondition is satisfiable and rejects invalid input', () => {
        const valid = (total, weights) => {
            try {
                assertValidInput(total, weights)
                return true
            }
            catch {
                return false
            }
        }
        assert.equal(countGuardHits(valid, DOMAIN), DOMAIN_SIZE)
        assert.equal(valid(-1, [1]), false)
        assert.equal(valid(1, []), false)
        assert.equal(valid(1, [0]), false)
        assert.equal(valid(0.5, [1]), false)
    })
})
