const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

// Use an existing Playwright installation, as with validate-balloon.cjs.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const root = path.resolve(__dirname, '..')
const dist = path.join(root, 'dist')
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.png': 'image/png', '.webp': 'image/webp', '.avif': 'image/avif', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' }

function builtPath(urlPath) {
    const file = path.resolve(dist, `.${decodeURIComponent(urlPath)}`)
    assert.ok(file.startsWith(dist + path.sep))
    return fs.existsSync(file) && fs.statSync(file).isDirectory() ? path.join(file, 'index.html') : file
}

async function validate() {
    const browser = await chromium.launch({ channel: 'chrome', headless: true })
    try {
        const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
        const errors = []
        page.on('pageerror', error => errors.push(error.message))
        await page.route('**/*', async (route) => {
            const url = new URL(route.request().url())
            if (url.hostname.toLowerCase() !== 'blog.jamestsetsekas.com') {
                return route.fulfill({ status: 204, body: '' })
            }
            const file = builtPath(url.pathname)
            assert.ok(fs.existsSync(file), `Missing built asset: ${url.pathname}`)
            return route.fulfill({ status: 200, contentType: types[path.extname(file)] || 'application/octet-stream', body: fs.readFileSync(file) })
        })
        const visit = route => page.goto(`https://blog.jamestsetsekas.com${route}`, { waitUntil: 'networkidle' })
        await visit('/categories/')
        const topics = await page.locator('[data-category-card]').evaluateAll(cards => cards.map(card => ({
            slug: card.dataset.categoryCard,
            count: Number(card.textContent.match(/(\d+) posts?/)[1]),
        })))
        assert.ok(topics.length > 0)
        assert.ok(topics.every(topic => topic.count > 0), 'Empty topics should not appear in the directory')
        assert.equal(new Set(topics.map(topic => topic.slug)).size, topics.length)
        assert.deepEqual(topics.slice(0, 6).map(topic => topic.slug), ['software-engineering', 'ai', 'security', 'cryptography', 'bitcoin', 'nostr'])
        assert.doesNotMatch(await page.locator('main').textContent() || '', /update today/i)

        const categories = fs.readdirSync(path.join(dist, 'categories'), { withFileTypes: true }).filter(entry => entry.isDirectory())
        for (const category of categories) {
            await visit(`/categories/${category.name}/`)
            const links = await page.locator('[data-category-posts] > a').evaluateAll(cards => cards.map(card => card.getAttribute('href')))
            assert.equal(links.length, topics.find(topic => topic.slug === category.name)?.count || 0, category.name)
            for (const href of links) {
                assert.ok(fs.existsSync(builtPath(href)), `Broken article link: ${href}`)
            }
            if (links.length === 0) {
                assert.equal(await page.getByRole('heading', { name: 'No posts in this topic yet' }).count(), 1)
            }
            assert.equal(await page.getByRole('link', { name: 'All topics', exact: true }).count(), 1)
        }

        const routes = ['/categories/', '/categories/software-engineering/', '/categories/cryptography/', '/categories/laravel/']
        for (const width of [1440, 390]) {
            await page.setViewportSize({ width, height: 1000 })
            for (const dark of [false, true]) {
                await page.evaluate(value => localStorage.setItem('hs_theme', value ? 'dark' : 'default'), dark)
                for (const route of routes) {
                    await visit(route)
                    assert.equal(await page.evaluate(() => document.documentElement.classList.contains('dark')), dark)
                    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, `${route}, ${width}px, dark=${dark}`)
                    if (route === '/categories/') {
                        await page.locator('[data-category-card]').first().focus()
                        assert.equal(await page.locator('[data-category-card]').first().evaluate(el => el.matches(':focus-visible')), true)
                        if (process.env.CATEGORY_SCREENSHOTS) {
                            await page.screenshot({ path: path.join(process.env.CATEGORY_SCREENSHOTS, `categories-${width}-${dark ? 'dark' : 'light'}.png`), fullPage: true })
                        }
                    }
                }
            }
        }
        assert.deepEqual(errors, [])
        console.log(`Validated ${topics.length} active topics, ${categories.length} category routes, article links, empty states, keyboard focus and 16 responsive/theme layouts.`)
    }
    finally {
        await browser.close()
    }
}

validate().catch((error) => {
    console.error(error)
    process.exit(1)
})
