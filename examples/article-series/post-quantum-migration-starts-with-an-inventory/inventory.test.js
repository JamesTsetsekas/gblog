import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
// eslint-disable-next-line test/no-import-node-test -- examples use Node's built-in runner; the repo has no test framework dependency
import { describe, it } from 'node:test'
import { fileURLToPath } from 'node:url'
import { PRIORITY, prioritize, quantumExposure, scanDirectory, scanSource } from './inventory.js'

const here = dirname(fileURLToPath(import.meta.url))
const findings = scanDirectory(join(here, 'fixtures', 'sample-app'))
const annotations = JSON.parse(readFileSync(join(here, 'annotations.json'), 'utf8'))

function priorityOf(plan, file, primitive) {
    return plan.find(p => p.file === file && p.primitive === primitive).priority
}

describe('discovery', () => {
    it('finds the nine literal cryptographic uses in the fixture app', () => {
        const summary = findings.map(f => `${f.file} ${f.kind} ${f.primitive}`)
        assert.deepEqual(summary, [
            'config/tls.json key-establishment TLS groups: X25519, P-256',
            'src/auth.js signature RSA-SHA256',
            'src/backup.js symmetric-encryption aes-256-gcm',
            'src/backup.js key-transport RSA public-key encryption',
            'src/cache.js hash md5',
            'src/partner.js key-establishment ECDH prime256v1',
            'src/plugins.js signature unknown (non-literal algorithm)',
            'src/release.js key-generation ed25519',
            'src/webhooks.js mac HMAC-sha256',
        ])
    })

    it('reports a runtime-selected algorithm instead of silently skipping it', () => {
        const plugin = findings.find(f => f.file === 'src/plugins.js')
        assert.equal(quantumExposure(plugin.primitive), 'unknown')
    })

    it('has blind spots: a third-party SDK and the one-shot sign() call', () => {
        assert.equal(findings.some(f => f.file === 'src/storage.js'), false)
        const release = findings.filter(f => f.file === 'src/release.js')
        assert.deepEqual(release.map(f => f.line), [5])
    })

    it('ignores comments', () => {
        assert.deepEqual(scanSource('// createHash(\'md5\')', 'x.js'), [])
    })
})

describe('classification', () => {
    it('separates quantum-vulnerable public-key uses from symmetric ones', () => {
        assert.equal(quantumExposure('RSA-SHA256'), 'shor')
        assert.equal(quantumExposure('ECDH prime256v1'), 'shor')
        assert.equal(quantumExposure('ed25519'), 'shor')
        assert.equal(quantumExposure('TLS groups: X25519, P-256'), 'shor')
        assert.equal(quantumExposure('aes-256-gcm'), 'symmetric-ok')
        assert.equal(quantumExposure('HMAC-sha256'), 'symmetric-ok')
        assert.equal(quantumExposure('md5'), 'classically-weak')
        assert.equal(quantumExposure('TLS groups: X25519MLKEM768, X25519'), 'tls-negotiation-unverified')
    })
})

describe('prioritization depends on stated assumptions', () => {
    it('never treats an offered TLS group as evidence of negotiated protection', () => {
        for (const primitive of ['TLS groups: X25519MLKEM768, X25519', 'TLS groups: X25519MLKEM768']) {
            const finding = { file: 'tls.json', line: 1, primitive }
            const notes = { [`tls.json|${primitive}`]: { owner: 'platform', purpose: 'confidentiality', confidentialityYears: 5, migrationYears: 1 } }
            assert.equal(prioritize([finding], notes, { scenarioYears: 10 })[0].priority, PRIORITY.REVIEW_TLS)
        }
    })

    it('routes missing or invalid lifetime records to review instead of defaulting to zero', () => {
        const finding = { file: 'backup.js', line: 1, primitive: 'RSA public-key encryption' }
        const complete = { owner: 'platform', purpose: 'confidentiality', confidentialityYears: 7, migrationYears: 4 }
        for (const field of ['purpose', 'confidentialityYears', 'migrationYears']) {
            const incomplete = { ...complete }
            delete incomplete[field]
            assert.equal(prioritize([finding], { 'backup.js|RSA public-key encryption': incomplete }, { scenarioYears: 10 })[0].priority, PRIORITY.REVIEW_INCOMPLETE)
        }
        for (const value of [-1, Number.NaN, '7']) {
            const invalid = { ...complete, confidentialityYears: value }
            assert.equal(prioritize([finding], { 'backup.js|RSA public-key encryption': invalid }, { scenarioYears: 10 })[0].priority, PRIORITY.REVIEW_INCOMPLETE)
        }
    })

    it('includes issuer key lifetime and verifier retirement in authentication priority', () => {
        const finding = { file: 'src/auth.js', line: 5, primitive: 'RSA-SHA256' }
        const original = annotations['src/auth.js|RSA-SHA256']
        for (const patch of [{ issuerKeyLifetimeYears: 20 }, { classicalAcceptanceRetirementYears: 20 }]) {
            const notes = { 'src/auth.js|RSA-SHA256': { ...original, ...patch } }
            assert.equal(prioritize([finding], notes, { scenarioYears: 10 })[0].priority, PRIORITY.P2)
        }
        const incomplete = { ...original }
        delete incomplete.issuerKeyLifetimeYears
        assert.equal(prioritize([finding], { 'src/auth.js|RSA-SHA256': incomplete }, { scenarioYears: 10 })[0].priority, PRIORITY.REVIEW_INCOMPLETE)
    })

    it('rejects invalid scenario durations', () => {
        for (const scenarioYears of [-1, Number.NaN, Number.POSITIVE_INFINITY, '10']) {
            assert.throws(() => prioritize(findings, annotations, { scenarioYears }), RangeError)
        }
    })

    it('with a 10-year scenario, long-lived backups and firmware signing lead', () => {
        const plan = prioritize(findings, annotations, { scenarioYears: 10 })
        assert.equal(plan[0].file, 'src/backup.js')
        assert.equal(plan[0].priority, PRIORITY.P1)
        assert.equal(plan[1].priority, PRIORITY.P2)
        assert.equal(priorityOf(plan, 'config/tls.json', 'TLS groups: X25519, P-256'), PRIORITY.P3)
        assert.equal(priorityOf(plan, 'src/auth.js', 'RSA-SHA256'), PRIORITY.P3)
        assert.equal(priorityOf(plan, 'src/cache.js', 'md5'), PRIORITY.DOCUMENT)
    })

    it('with a 5-year scenario, TLS traffic becomes a harvest-now risk', () => {
        const plan = prioritize(findings, annotations, { scenarioYears: 5 })
        assert.equal(priorityOf(plan, 'config/tls.json', 'TLS groups: X25519, P-256'), PRIORITY.P1)
        assert.equal(priorityOf(plan, 'src/auth.js', 'RSA-SHA256'), PRIORITY.P3)
    })

    it('with a 15-year scenario, nothing is urgent but unknowns still need review', () => {
        const plan = prioritize(findings, annotations, { scenarioYears: 15 })
        const urgent = plan.filter(p => p.priority === PRIORITY.P1 || p.priority === PRIORITY.P2)
        assert.equal(urgent.length, 0)
        assert.equal(priorityOf(plan, 'src/partner.js', 'ECDH prime256v1'), PRIORITY.REVIEW_OWNER)
        assert.equal(priorityOf(plan, 'src/plugins.js', 'unknown (non-literal algorithm)'), PRIORITY.REVIEW_UNKNOWN)
    })

    it('never ranks an unannotated quantum-vulnerable use as safe', () => {
        for (const scenarioYears of [0, 5, 10, 15, 50]) {
            const plan = prioritize(findings, annotations, { scenarioYears })
            assert.equal(priorityOf(plan, 'src/partner.js', 'ECDH prime256v1'), PRIORITY.REVIEW_OWNER)
        }
    })
})
