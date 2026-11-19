// Fixture: a fictional app. Builds cache keys. Not a security control.
import { createHash } from 'node:crypto'

export function cacheKey(url) {
    return createHash('md5').update(url).digest('hex')
}
