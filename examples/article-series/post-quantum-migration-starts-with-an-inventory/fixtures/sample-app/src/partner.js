// Fixture: a fictional app. Derives a shared key with a partner system.
// Nobody has annotated this one yet.
import { createECDH } from 'node:crypto'

export function partnerKeyAgreement(partnerPublicKey) {
    const ecdh = createECDH('prime256v1')
    const publicKey = ecdh.generateKeys()
    return { publicKey, sharedSecret: ecdh.computeSecret(partnerPublicKey) }
}
