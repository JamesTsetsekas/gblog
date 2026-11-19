// Fixture: a fictional app. Signs session tokens that expire after 15 minutes.
import { createSign } from 'node:crypto'

export function signSessionToken(payload, privateKeyPem) {
    const signer = createSign('RSA-SHA256')
    signer.update(JSON.stringify(payload))
    return signer.sign(privateKeyPem, 'base64url')
}
