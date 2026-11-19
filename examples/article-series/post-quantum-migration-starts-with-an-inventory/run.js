// Usage: node run.js [scenarioYears]
// Prints a ranked migration plan for the fictional fixture app.
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { formatPlan, prioritize, scanDirectory } from './inventory.js'

const here = dirname(fileURLToPath(import.meta.url))
const scenarioYears = Number(process.argv[2] ?? 10)
if (!Number.isFinite(scenarioYears) || scenarioYears < 0) {
    throw new RangeError('scenarioYears must be a non-negative number')
}

const findings = scanDirectory(join(here, 'fixtures', 'sample-app'))
const annotations = JSON.parse(readFileSync(join(here, 'annotations.json'), 'utf8'))
const plan = prioritize(findings, annotations, { scenarioYears })

console.log(`Assumed scenario: a cryptographically relevant quantum computer in ${scenarioYears} years.`)
console.log('This is an input for ranking, not a forecast.\n')
console.log(formatPlan(plan))
