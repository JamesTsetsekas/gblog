// Fixture: a fictional app. Nightly customer backups, retained for seven years.
// Each backup gets a fresh data key, wrapped for a recovery key holder.
import { Buffer } from 'node:buffer'
import { constants, createCipheriv, publicEncrypt, randomBytes } from 'node:crypto'

export function encryptBackup(plaintext, recoveryPublicKeyPem) {
    const dataKey = randomBytes(32)
    const iv = randomBytes(12)
    const cipher = createCipheriv('aes-256-gcm', dataKey, iv)
    const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()])
    const wrappedKey = publicEncrypt(
        { key: recoveryPublicKeyPem, padding: constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' },
        dataKey,
    )
    return { iv, ciphertext, tag: cipher.getAuthTag(), wrappedKey }
}
