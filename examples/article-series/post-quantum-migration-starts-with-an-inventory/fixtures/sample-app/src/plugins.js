// Fixture: a fictional app. The algorithm comes from configuration at runtime.
import { createSign } from 'node:crypto'

export function signPluginManifest(manifest, config, privateKeyPem) {
    const signer = createSign(config.signatureAlgorithm)
    signer.update(manifest)
    return signer.sign(privateKeyPem, 'base64')
}
