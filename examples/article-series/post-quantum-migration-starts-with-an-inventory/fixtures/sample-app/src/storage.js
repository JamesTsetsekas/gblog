// Fixture: a fictional app. A third-party SDK encrypts uploads internally.
// A source scanner sees no cryptographic call here.
export async function uploadDocument(sdk, document) {
    return sdk.uploadEncrypted({ bucket: 'customer-documents', body: document })
}
