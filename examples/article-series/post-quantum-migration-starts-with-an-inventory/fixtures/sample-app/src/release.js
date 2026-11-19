// Fixture: a fictional app. Signs firmware updates that devices verify for years.
import { generateKeyPairSync, sign } from 'node:crypto'

export function createReleaseKey() {
    return generateKeyPairSync('ed25519')
}

export function signRelease(artifact, privateKey) {
    return sign(null, artifact, privateKey)
}
