const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

function loadPlaywright() {
    if (process.env.PLAYWRIGHT_MODULE) {
        return require(process.env.PLAYWRIGHT_MODULE)
    }
    try {
        return require('playwright')
    }
    catch {}
    const links = path.join(
        process.env.LOCALAPPDATA || '',
        'ms-playwright',
        '.links',
    )
    if (fs.existsSync(links)) {
        for (const file of fs.readdirSync(links)) {
            try {
                return require(
                    fs.readFileSync(path.join(links, file), 'utf8').trim(),
                )
            }
            catch {}
        }
    }
    throw new Error('Set PLAYWRIGHT_MODULE to a local Playwright installation.')
}
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-7, `${a} != ${b}`);
(async () => {
    const root = path.resolve(__dirname, '..')
    const dist = path.join(root, 'dist')
    const source = [
        'src/components/balloon/controller.js',
        'src/components/balloon/room.html',
        'src/content/posts/how-many-red-balloons.mdx',
    ]
        .map(f => fs.readFileSync(path.join(root, f), 'utf8'))
        .join('\n')
    assert.doesNotMatch(
        source,
        /Say it naturally|Copy explanation|copyStatus|explanationEdited|resetText|supervised/i,
    )
    const { chromium } = loadPlaywright()
    const browser = await chromium.launch({ headless: true })
    try {
        const page = await browser.newPage({
            viewport: { width: 1280, height: 900 },
            reducedMotion: 'reduce',
        })
        const errors = []
        const missing = []
        page.on('pageerror', e => errors.push(e.message))
        await page.route('**/*', async (route) => {
            const url = new URL(route.request().url())
            if (url.hostname !== 'balloon.test') {
                return route.abort()
            }
            let file = path.join(dist, decodeURIComponent(url.pathname))
            if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
                file = path.join(file, 'index.html')
            }
            if (!fs.existsSync(file)) {
                missing.push(url.pathname)
                return route.fulfill({ status: 404, body: 'missing' })
            }
            const types = {
                '.html': 'text/html',
                '.js': 'text/javascript',
                '.css': 'text/css',
                '.png': 'image/png',
                '.svg': 'image/svg+xml',
                '.avif': 'image/avif',
                '.webp': 'image/webp',
            }
            return route.fulfill({
                body: fs.readFileSync(file),
                contentType:
                    types[path.extname(file)] || 'application/octet-stream',
            })
        })
        await page.goto('http://balloon.test/posts/how-many-red-balloons/')
        await page.waitForFunction(
            () => document.querySelector('.balloon-lab')?.balloonLab,
        )
        const data = () =>
            page.evaluate(() => {
                const b = document.querySelector('.balloon-lab').balloonLab
                return {
                    s: b.getState(),
                    m: b.getModel(),
                    d: b.getDiagnostics(),
                }
            })
        const input = async (id, v) => {
            await page.locator(`#${id}`).fill(String(v))
            await page.locator(`#${id}`).dispatchEvent('change')
        }
        const v = await data()
        near(v.m.capacity, 5349.235834504944)
        near(v.m.available, 4376 + 1 / 3)
        assert.equal(v.d.blocked, 0)
        assert.equal(v.d.progress, 1)
        assert.match(await page.locator('#capacity').textContent(), /5,350/)
        await page.locator('.inputs > summary').click()
        await input('diameter', 24)
        near((await data()).m.capacity, v.m.capacity / 8)
        await input('diameter', 12)
        await input('packing', 0.52)
        near((await data()).m.capacity, (v.m.capacity * 0.52) / 0.64)
        await input('packing', 0.64)
        await page.locator('#split').uncheck()
        near((await data()).m.available, 3266 + 1 / 3)
        await page.locator('#split').check()
        await input('tallArea', 160)
        near((await data()).m.available, 4746 + 1 / 3)
        await page.locator('#preset').selectOption('baseline')
        near((await data()).m.capacity, v.m.capacity)
        await page.locator('#preset').selectOption('baseline')
        await input('furniture', 9999)
        near((await data()).m.capacity, 0)
        await page.locator('#preset').selectOption('baseline')
        await page.locator('#empty').click()
        assert.equal((await data()).d.goal, 0)
        await page.locator('#full').click()
        assert.equal((await data()).d.goal, 1)
        await page.locator('#top').click()
        assert.equal((await data()).d.view, 'top')
        await page.locator('#scene').press('Home')
        assert.equal((await data()).d.view, 'iso')
        await page.locator('.inputs > summary').click()
        for (const width of [1280, 390]) {
            for (const dark of [false, true]) {
                await page.setViewportSize({ width, height: 900 })
                await page.evaluate(
                    d => document.documentElement.classList.toggle('dark', d),
                    dark,
                )
                await page.locator('.balloon-lab').scrollIntoViewIfNeeded()
                assert.ok(
                    await page.evaluate(
                        () =>
                            document.documentElement.scrollWidth
                            <= innerWidth + 1,
                    ),
                    'horizontal overflow',
                )
                assert.ok(
                    (await page.locator('article img').count())
                    || (await page.locator('img').count()),
                )
                if (process.env.BALLOON_SCREENSHOTS) {
                    await page.screenshot({
                        path: path.join(
                            process.env.BALLOON_SCREENSHOTS,
                            `balloon-${width}-${dark ? 'dark' : 'light'}.png`,
                        ),
                    })
                }
            }
        }
        const og = await page
            .locator('meta[property="og:image"]')
            .getAttribute('content')
        assert.match(og, /red-balloons-living-room/)
        assert.deepEqual(missing, [])
        assert.deepEqual(errors, [])
        await page.emulateMedia({ reducedMotion: 'no-preference' })
        await page.reload()
        await page.evaluate(() => window.scrollTo(0, 0))
        await page.waitForTimeout(200)
        const beforeVisible = (await data()).d.progress
        await page.waitForTimeout(200)
        near((await data()).d.progress, beforeVisible)
        await page.locator('#scene').scrollIntoViewIfNeeded()
        await page.waitForTimeout(250)
        assert.ok((await data()).d.progress > beforeVisible, 'animation starts when visible')
        await page.evaluate(() => window.scrollTo(0, 0))
        await page.waitForTimeout(100)
        const pausedOffscreen = (await data()).d.progress
        await page.waitForTimeout(150)
        near((await data()).d.progress, pausedOffscreen)
        assert.equal((await data()).d.tickActive, false)
        console.log('PASS visible-only animation and offscreen idle scheduling')
        console.log(
            'PASS built article, local assets/OG, exact baseline, input sensitivity/reset/clamps, scope/fill/camera, reduced motion, mobile/desktop light/dark; no removed copy or browser errors.',
        )
    }
    finally {
        await browser.close()
    }
})().catch((e) => {
    console.error(e)
    process.exitCode = 1
})
