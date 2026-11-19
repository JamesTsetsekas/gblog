// Fixture: a fictional app. Verifies inbound webhook signatures with a shared secret.
import { Buffer } from 'node:buffer'
import { createHmac, timingSafeEqual } from 'node:crypto'

export function verifyWebhook(body, signatureHex, secret) {
    const expected = createHmac('sha256', secret).update(body).digest()
    const received = Buffer.from(signatureHex, 'hex')
    return received.length === expected.length && timingSafeEqual(received, expected)
}
