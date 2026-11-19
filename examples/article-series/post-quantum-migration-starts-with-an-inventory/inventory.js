// A deliberately small cryptographic inventory pipeline:
//   1. scan source and config for cryptographic calls (discovery),
//   2. join each finding with human annotations (purpose, lifetime, owner),
//   3. rank findings under an explicit, assumed threat timeline.
//
// The scanner only understands Node's crypto API called with literal
// algorithm names, plus one JSON config shape. Everything else is a blind
// spot, and the tests say so.

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, sep } from 'node:path'

const RULES = [
    { re: /createSign\(\s*'([^']+)'/g, kind: 'signature', primitive: m => m[1] },
    { re: /createSign\(\s*[\w.]/g, kind: 'signature', primitive: () => 'unknown (non-literal algorithm)' },
    { re: /createECDH\(\s*'([^']+)'/g, kind: 'key-establishment', primitive: m => `ECDH ${m[1]}` },
    { re: /publicEncrypt\(/g, kind: 'key-transport', primitive: () => 'RSA public-key encryption' },
    { re: /generateKeyPairSync\(\s*'([^']+)'/g, kind: 'key-generation', primitive: m => m[1] },
    { re: /createHmac\(\s*'([^']+)'/g, kind: 'mac', primitive: m => `HMAC-${m[1]}` },
    { re: /createCipheriv\(\s*'([^']+)'/g, kind: 'symmetric-encryption', primitive: m => m[1] },
    { re: /createHash\(\s*'([^']+)'/g, kind: 'hash', primitive: m => m[1] },
]

export function scanSource(text, file) {
    const findings = []
    text.split(/\r?\n/).forEach((line, index) => {
        if (line.trim().startsWith('//')) {
            return
        }
        for (const rule of RULES) {
            for (const match of line.matchAll(rule.re)) {
                findings.push({ file, line: index + 1, kind: rule.kind, primitive: rule.primitive(match) })
            }
        }
    })
    return findings
}

export function scanJsonConfig(text, file) {
    const config = JSON.parse(text)
    if (!Array.isArray(config.groups)) {
        return []
    }
    return [{ file, line: 1, kind: 'key-establishment', primitive: `TLS groups: ${config.groups.join(', ')}` }]
}

export function scanDirectory(root) {
    const files = readdirSync(root, { recursive: true })
        .map(p => String(p))
        .filter(p => statSync(join(root, p)).isFile())
        .sort()
    const findings = []
    for (const relative of files) {
        const file = relative.split(sep).join('/')
        const text = readFileSync(join(root, relative), 'utf8')
        if (file.endsWith('.js')) {
            findings.push(...scanSource(text, file))
        }
        else if (file.endsWith('.json')) {
            findings.push(...scanJsonConfig(text, file))
        }
    }
    return findings
}

export function annotationKey(finding) {
    return `${finding.file}|${finding.primitive}`
}

// Coarse classification. NIST IR 8547 lists RSA, ECDSA, EdDSA and (EC)DH
// as quantum-vulnerable, and treats approved symmetric primitives with at
// least 128 bits of classical security as meeting at least Category 1.
export function quantumExposure(primitive) {
    const p = primitive.toLowerCase()
    if (p.startsWith('unknown')) {
        return 'unknown'
    }
    if (p.startsWith('tls groups:') && /mlkem|ml-kem/.test(p)) {
        // Configuration lists capabilities, not the group a connection negotiated.
        return 'tls-negotiation-unverified'
    }
    if (/mlkem|ml-kem|ml-dsa|slh-dsa/.test(p)) {
        return 'post-quantum-or-hybrid'
    }
    if (/\bmd5\b|\bsha1\b/.test(p)) {
        return 'classically-weak'
    }
    if (/rsa|ecdh|ecdsa|ed25519|ed448|x25519|p-256|prime256v1|secp256k1/.test(p)) {
        return 'shor'
    }
    if (/aes-(?:128|192|256)|hmac-sha(?:256|384|512)|^sha(?:256|384|512)$/.test(p)) {
        return 'symmetric-ok'
    }
    return 'unknown'
}

export const PRIORITY = {
    FIX_NOW: 'Fix now: classically weak',
    P1: 'P1: harvest now, decrypt later',
    P2: 'P2: long-lived signatures',
    REVIEW_UNKNOWN: 'Review: algorithm unknown',
    REVIEW_OWNER: 'Review: no owner annotation',
    REVIEW_TLS: 'Review: verify TLS negotiation and fallback policy',
    REVIEW_INCOMPLETE: 'Review: incomplete purpose, lifetime or retirement policy',
    P3: 'P3: schedule with normal upgrades',
    KEEP: 'Keep: symmetric, 128-bit or stronger',
    KEEP_PQ: 'Keep: post-quantum or hybrid in place',
    DOCUMENT: 'Document: not a security control',
}

const RANK = {
    [PRIORITY.FIX_NOW]: 0,
    [PRIORITY.P1]: 1,
    [PRIORITY.P2]: 2,
    [PRIORITY.REVIEW_UNKNOWN]: 3,
    [PRIORITY.REVIEW_OWNER]: 3,
    [PRIORITY.REVIEW_TLS]: 3,
    [PRIORITY.REVIEW_INCOMPLETE]: 3,
    [PRIORITY.P3]: 4,
    [PRIORITY.KEEP]: 5,
    [PRIORITY.KEEP_PQ]: 5,
    [PRIORITY.DOCUMENT]: 6,
}

// scenarioYears is an assumption supplied by the reader, not a forecast.
// A use is urgent when the protected data (or signature) must stay
// trustworthy for longer than the threat is assumed to take to arrive,
// once the time needed to migrate is added.
export function decide(exposure, note, scenarioYears) {
    if (exposure === 'unknown') {
        return PRIORITY.REVIEW_UNKNOWN
    }
    if (!note || typeof note.owner !== 'string' || !note.owner.trim()) {
        return PRIORITY.REVIEW_OWNER
    }
    if (exposure === 'tls-negotiation-unverified') {
        return PRIORITY.REVIEW_TLS
    }
    if (exposure === 'classically-weak') {
        return note.securityRelevant === false ? PRIORITY.DOCUMENT : PRIORITY.FIX_NOW
    }
    if (exposure === 'symmetric-ok') {
        return PRIORITY.KEEP
    }
    if (exposure === 'post-quantum-or-hybrid') {
        return PRIORITY.KEEP_PQ
    }
    const duration = value => Number.isFinite(value) && value >= 0
    const signs = note.purpose === 'signature' || note.purpose === 'authentication'
    if (!duration(note.migrationYears)
        || (!signs && note.purpose !== 'confidentiality')
        || (note.purpose === 'confidentiality' && !duration(note.confidentialityYears))
        || (signs && (!duration(note.signatureTrustYears) || !duration(note.classicalAcceptanceRetirementYears)))
        || (note.purpose === 'authentication' && !duration(note.issuerKeyLifetimeYears))) {
        return PRIORITY.REVIEW_INCOMPLETE
    }
    const migration = note.migrationYears
    if (note.purpose === 'confidentiality' && note.confidentialityYears + migration > scenarioYears) {
        return PRIORITY.P1
    }
    const signingHorizon = signs ? Math.max(note.signatureTrustYears, note.issuerKeyLifetimeYears ?? 0) : 0
    if (signs && (signingHorizon + migration > scenarioYears || note.classicalAcceptanceRetirementYears > scenarioYears)) {
        return PRIORITY.P2
    }
    return PRIORITY.P3
}

export function prioritize(findings, annotations, { scenarioYears }) {
    if (!Number.isFinite(scenarioYears) || scenarioYears < 0) {
        throw new RangeError('scenarioYears must be a finite non-negative assumption')
    }
    return findings
        .map((finding) => {
            const exposure = quantumExposure(finding.primitive)
            const note = annotations[annotationKey(finding)]
            return {
                ...finding,
                exposure,
                owner: note?.owner ?? null,
                plannedAction: note?.plannedAction ?? null,
                priority: decide(exposure, note, scenarioYears),
            }
        })
        .sort((a, b) => RANK[a.priority] - RANK[b.priority] || a.file.localeCompare(b.file) || a.line - b.line)
}

export function formatPlan(plan) {
    const rows = plan.map(p => `| ${p.priority} | ${p.file}:${p.line} | ${p.primitive} | ${p.owner ?? '(none)'} | ${p.plannedAction ?? 'Assign an owner, purpose and data lifetime.'} |`)
    return ['| Priority | Location | Primitive | Owner | Planned action |', '| --- | --- | --- | --- | --- |', ...rows].join('\n')
}
