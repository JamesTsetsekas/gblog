(() => {
    'use strict'
    const root = document.querySelector('.balloon-lab')
    if (!root) {
        return
    }
    const $ = id => root.querySelector(`#${id}`)
    const TAU = Math.PI * 2
    const CAP = 1400
    const defaults = {
        width: 16,
        length: 23 + 1 / 12,
        low: 9.25,
        high: 18.5,
        tallArea: 120,
        diameter: 12,
        packing: 0.64,
        furniture: 150,
        deskW: 8,
        deskL: 6,
    }
    const numeric = Object.keys(defaults)
    const reduced = matchMedia('(prefers-reduced-motion: reduce)')
    let requestedCount = null
    const furnitureByScope = { whole: 150, desk: 20 }
    let priorScope = 'whole'
    const state = {}
    let model = {}
    let points = []
    let furn = []
    let angle = -0.73
    let tilt = 0.57
    let view = 'iso'
    let running = !reduced.matches
    let progress = reduced.matches ? 1 : 0.16
    let goal = 1
    let drag = null
    let last = 0
    let raf = 0
    let tickRaf = 0
    let visible = false
    let disposed = false
    const canvas = $('scene')
    const ctx = canvas.getContext('2d')
    let cw = 700
    let ch = 440
    let scale = 12
    let originX = 350
    let originY = 220
    const fmt = (v, d = 0) =>
        v.toLocaleString('en-US', {
            maximumFractionDigits: d,
            minimumFractionDigits: d,
        })
    function estimate(s) {
        const area = s.width * s.length
        const tall = s.split ? Math.min(area, Math.max(0, s.tallArea)) : 0
        const high = s.split ? Math.max(s.low, s.high) : s.low
        const dw = Math.min(s.width, s.deskW)
        const dl = Math.min(s.length, s.deskL)
        const desk = s.scope === 'desk'
        const a = desk ? dw * dl : area
        const extra = desk
            ? Math.max(0, Math.min(dl, tall / s.width - (s.length - dl)))
            * dw
            * (high - s.low)
            : tall * (high - s.low)
        const gross = a * s.low + extra
        const available = Math.max(0, gross - s.furniture)
        const sphere = (Math.PI / 6) * (s.diameter / 12) ** 3
        const capacity = (available * s.packing) / sphere
        return {
            area: a,
            tall,
            high,
            dw,
            dl,
            gross,
            extra,
            available,
            sphere,
            capacity,
        }
    }
    function read() {
        for (const id of numeric) {
            const el = $(id)
            let v = Number(el.value)
            if (el.value.trim() === '' || !Number.isFinite(v)) {
                v = state[id] ?? defaults[id]
            }
            v = Math.min(+el.max, Math.max(+el.min, v))
            el.value = v
            state[id] = v
        }
        state.high = Math.max(state.low, state.high)
        $('high').value = state.high
        state.tallArea = Math.min(state.width * state.length, state.tallArea)
        $('tallArea').value = state.tallArea
        state.split = $('split').checked
        state.scope = $('scope').value
        model = estimate(state)
        state.furniture = Math.min(state.furniture, model.gross)
        $('furniture').value = state.furniture
        model = estimate(state)
    }
    function sync(source) {
        read()
        if (source === 'fill') {
            goal = +$('fill').value / 100
            requestedCount = null
        }
        if (source === 'count' && $('count').value.trim() === '') {
            $('count').value = Math.floor(model.capacity * goal + 1e-8)
        }
        if (source === 'count') {
            requestedCount = Math.max(
                0,
                Math.floor(Number($('count').value) || 0),
            )
            if (requestedCount >= model.capacity) {
                requestedCount = null
                goal = 1
            }
        }
        if (['preset', 'scope', 'init'].includes(source)) {
            requestedCount = null
        }
        if (requestedCount !== null) {
            requestedCount = Math.min(
                requestedCount,
                Math.floor(model.capacity),
            )
            goal = model.capacity ? requestedCount / model.capacity : 0
        }
        goal = Math.max(0, Math.min(1, goal))
        $('fill').value = goal * 100
        if (['init', 'fill', 'count'].includes(source) && !running) {
            progress = goal
        }
        else {
            progress = Math.min(progress, goal)
        }
        $('count').max = Math.floor(model.capacity)
        $('count').value
            = requestedCount ?? Math.floor(model.capacity * goal + 1e-8)
        $('fillValue').textContent = `${fmt(goal * 100)}%`
        $('capacity').innerHTML
            = `≈ ${fmt(Math.round(model.capacity / 50) * 50)} <small>balloons</small>`
        $('available').textContent = `${fmt(model.available, 1)} ft³`
        $('sphere').textContent
            = `${fmt(state.diameter, 1)} in diameter · ${fmt(model.sphere, 3)} ft³ each`
        $('smaller').textContent
            = `≈ ${fmt(Math.round(model.capacity / 0.9 ** 3))}`
        $('larger').textContent
            = `≈ ${fmt(Math.round(model.capacity / 1.1 ** 3))}`
        $('deskFields').hidden = state.scope !== 'desk'
        $('scopeCaption').textContent
            = state.scope === 'desk'
                ? 'DESK ZONE · ASSUMED RECTANGLE'
                : state.split
                    ? 'LIVING ROOM + DOUBLE-HEIGHT VOID'
                    : 'LIVING ROOM - SINGLE CEILING'
        $('high').disabled = $('tallArea').disabled = !state.split
        $('math').innerHTML
            = `Floor area = ${state.scope === 'desk' ? `${fmt(model.dw, 2)} × ${fmt(model.dl, 2)}` : `${fmt(state.width, 2)} × ${fmt(state.length, 5)}`} = ${fmt(model.area, 3)} ft²<br>Base volume = ${fmt(model.area, 3)} × ${fmt(state.low, 2)} ft = ${fmt(model.area * state.low, 3)} ft³<br>Extra tall void = ${state.scope === 'whole' ? `${state.split ? fmt(model.tall, 2) : '0'} × (${fmt(model.high, 2)} − ${fmt(state.low, 2)})` : 'overlap area × extra height'} = ${fmt(model.extra, 3)} ft³<br>Available = ${fmt(model.gross, 3)} − ${fmt(state.furniture)} = ${fmt(model.available, 3)} ft³<br>Balloon volume = π/6 × (${fmt(state.diameter, 1)}/12)³ = ${fmt(model.sphere, 6)} ft³<br>Count = ${fmt(model.available, 3)} × ${state.packing} / ${fmt(model.sphere, 6)} = ${fmt(model.capacity, 2)}<br>Current target = ${fmt(goal * 100, 1)}% ≈ ${fmt(Math.floor(model.capacity * goal))} balloons`
        const inputSource = (id, baseline, description) =>
            state[id] === baseline ? description : 'User input - verify measurement'
        $('widthSource').textContent = inputSource(
            'width',
            16,
            'Approximate floor plan',
        )
        $('lengthSource').textContent = inputSource(
            'length',
            23 + 1 / 12,
            'Approximate plan: 23 ft 1 in',
        )
        $('lowSource').textContent = inputSource(
            'low',
            9.25,
            '111 in measured = 9.25 ft',
        )
        $('provenance').textContent
            = state.scope === 'desk'
                ? `Desk rectangle: ${model.dw} x ${model.dl} ft, assumed and editable. Lower ceiling: ${state.low} ft. Furniture allowance: ${state.furniture} cu ft, assumed. Extra tall volume in this boundary: ${fmt(model.extra, 1)} cu ft. Packing: ${state.packing}, assumed.`
                : `Approximate floor plan: baseline 16 ft x 23 ft 1 in. Measured lower ceiling: baseline 111 in. Current dimensions: ${state.width} x ${fmt(state.length, 4)} x ${state.low} ft. Tall ceiling ${state.high} ft and tall footprint ${state.tallArea} sq ft are assumptions${state.split ? '' : ' (currently excluded)'}. Furniture allowance ${state.furniture} cu ft and packing ${state.packing} are assumptions. Edited dimensions need independent verification.`

        if (!['fill', 'count'].includes(source)) {
            buildFurniture()
            buildPoints()
        }
        updateMotionButton()
        requestDraw()
    }
    function box(x, y, z, w, l, h, color) {
        return { x, y, z, w, l, h, color }
    }
    function buildFurniture() {
        const w = state.width
        const l = state.length
        const sx = w / 16
        const sy = l / (23 + 1 / 12)
        furn = []
        const add = (x, y, z, a, b, h, c) =>
            furn.push(box(x * sx, y * sy, z, a * sx, b * sy, h, c))
        // Tables are tops and slender legs; do not exclude their accessible underside.
        add(0.6, 0.9, 0, 6, 2.6, 1.25, '#b7a18a')
        add(0.6, 0.9, 1.25, 6, 0.5, 1.25, '#cbbba3')
        add(0.6, 0.9, 1.25, 0.45, 2.6, 0.8, '#cbbba3')
        add(12.8, 1, 0, 2.6, 6, 1.25, '#9d8974')
        add(15, 1, 1.25, 0.4, 6, 1.3, '#baa28a')
        add(5, 5.3, 1.5, 4, 2.1, 0.18, '#9b633e')
        for (const x of [5.2, 8.6]) {
            for (const y of [5.5, 7]) {
                add(x, y, 0, 0.16, 0.16, 1.5, '#6d4f36')
            }
        }
        add(8.8, 12.2, 2.4, 3.1, 3.1, 0.18, '#eeeae0')
        furn[furn.length - 1].round = true
        add(10.1, 13.5, 0, 0.35, 0.35, 2.4, '#aaa99b')
        for (const [x, y] of [
            [8, 13],
            [12.1, 13],
            [9.8, 11.1],
            [9.8, 15.5],
        ]) {
            add(x, y, 1.3, 1, 1, 0.18, '#568599')
            add(x, y + 0.8, 1.3, 1, 0.15, 1.1, '#568599')
        }
        add(1, 20, 2.4, 7, 2, 0.16, '#b39468')
        for (const x of [1.2, 7.6]) {
            add(x, 20.2, 0, 0.15, 1.6, 2.4, '#68685a')
        }
        for (let i = 0; i < 4; i++) {
            add(1.3 + i * 1.6, 21, 2.65, 1.35, 0.15, 0.9, '#343f40')
        }
        add(4, 18.5, 1.3, 1.5, 1.5, 0.2, '#485c58')
    }
    function blocked(x, y, z, r) {
        return furn.some(
            b =>
                x + r > b.x
                && x - r < b.x + b.w
                && y + r > b.y
                && y - r < b.y + b.l
                && z + r > b.z
                && z - r < b.z + b.h,
        )
    }
    function rand(i) {
        const v = Math.sin(i * 127.1 + 311.7) * 43758.5453
        return v - Math.floor(v)
    }
    function buildPoints() {
        points = []
        const m = model
        const s = state
        const r = s.diameter / 24
        const w = s.width
        const l = s.length
        const wanted = Math.min(CAP, Math.floor(m.capacity))
        if (!wanted) {
            return
        }
        const step = Math.max(
            2 * r,
            Math.cbrt(m.gross / Math.max(1, wanted)) * 0.9,
        )
        const xmin = s.scope === 'desk' ? 0 : 0
        const xmax = s.scope === 'desk' ? m.dw : w
        const ymin = s.scope === 'desk' ? l - m.dl : 0
        let i = 0
        for (let z = r; z < m.high - r + 0.001; z += step * 0.83) {
            for (let y = ymin + r; y < l - r; y += step * 0.91) {
                for (let x = xmin + r; x < xmax - r; x += step) {
                    const xx = Math.min(
                        xmax - r,
                        Math.max(r, x + (rand(++i) - 0.5) * step * 0.22),
                    )
                    const yy = Math.min(
                        l - r,
                        Math.max(
                            ymin + r,
                            y + (rand(i + 3) - 0.5) * step * 0.22,
                        ),
                    )
                    const zz
                        = z + (rand(i + 8) - 0.5) * Math.min(r * 0.3, step * 0.1)
                    const ceiling = s.split && yy < m.tall / w ? m.high : s.low
                    if (
                        zz - r < 0
                        || zz + r > ceiling
                        || blocked(xx, yy, zz, r)
                        || points.some(
                            p =>
                                (p.x - xx) ** 2
                                + (p.y - yy) ** 2
                                + (p.z - zz) ** 2
                                < (2 * r) ** 2,
                        )
                    ) {
                        continue
                    }
                    points.push({ x: xx, y: yy, z: zz, r, seed: i })
                }
            }
        }
        // Deterministic even sample across the entire allowed volume, then fill from bottom upward.
        if (points.length > wanted) {
            points = points
                .filter(
                    (_, i, a) =>
                        Math.floor((i * wanted) / a.length)
                        !== Math.floor(((i - 1) * wanted) / a.length),
                )
                .slice(0, wanted)
        }
        points.sort((a, b) => a.z - b.z || a.seed - b.seed)
    }
    function project(x, y, z) {
        const X = x - state.width / 2
        const Y = y - state.length / 2
        const c = Math.cos(angle)
        const s = Math.sin(angle)
        const u = X * c - Y * s
        const v = X * s + Y * c
        return {
            x: originX + u * scale,
            y:
                originY
                + v * scale * Math.sin(tilt)
                - z * scale * Math.cos(tilt),
            depth: v + z * 0.05,
        }
    }
    function poly(coords, color, stroke) {
        ctx.beginPath()
        coords.forEach((p, i) => {
            const q = project(...p)
            i ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y)
        })
        ctx.closePath()
        ctx.fillStyle = color
        ctx.fill()
        if (stroke) {
            ctx.strokeStyle = stroke
            ctx.lineWidth = 0.7
            ctx.stroke()
        }
    }
    function line(a, b, color = '#639185', dash = []) {
        const p = project(...a)
        const q = project(...b)
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(q.x, q.y)
        ctx.strokeStyle = color
        ctx.lineWidth = 1
        ctx.setLineDash(dash)
        ctx.stroke()
        ctx.setLineDash([])
    }
    function label(text, x, y, z, color = '#56665c') {
        const p = project(x, y, z)
        ctx.font = '10px "Segoe UI",sans-serif'
        const width = ctx.measureText(text).width
        ctx.fillStyle = '#f7f4e9e8'
        ctx.fillRect(p.x - width / 2 - 4, p.y - 11, width + 8, 16)
        ctx.fillStyle = color
        ctx.textAlign = 'center'
        ctx.fillText(text, p.x, p.y)
    }
    function shade(hex, k) {
        const a = hex
            .match(/\w\w/g)
            .map(x => Math.min(255, Math.round(Number.parseInt(x, 16) * k)))
        return `#${a.map(x => x.toString(16).padStart(2, '0')).join('')}`
    }
    function drawBox(b) {
        if (b.round) {
            const top = []
            const bottom = []
            for (let i = 0; i < 32; i++) {
                const a = (i / 32) * TAU
                top.push([
                    b.x + b.w / 2 + (Math.cos(a) * b.w) / 2,
                    b.y + b.l / 2 + (Math.sin(a) * b.l) / 2,
                    b.z + b.h,
                ])
                bottom.push([
                    b.x + b.w / 2 + (Math.cos(a) * b.w) / 2,
                    b.y + b.l / 2 + (Math.sin(a) * b.l) / 2,
                    b.z,
                ])
            }
            poly(bottom, '#b8b5aa')
            poly(top, b.color, '#c3c0b4')
            return
        }
        const { x, y, z, w, l, h, color } = b
        const faces = [
            {
                d: project(x + w / 2, y, z).depth,
                p: [
                    [x, y, z],
                    [x + w, y, z],
                    [x + w, y, z + h],
                    [x, y, z + h],
                ],
                k: 0.88,
            },
            {
                d: project(x + w / 2, y + l, z).depth,
                p: [
                    [x, y + l, z],
                    [x + w, y + l, z],
                    [x + w, y + l, z + h],
                    [x, y + l, z + h],
                ],
                k: 0.85,
            },
            {
                d: project(x, y + l / 2, z).depth,
                p: [
                    [x, y, z],
                    [x, y + l, z],
                    [x, y + l, z + h],
                    [x, y, z + h],
                ],
                k: 0.75,
            },
            {
                d: project(x + w, y + l / 2, z).depth,
                p: [
                    [x + w, y, z],
                    [x + w, y + l, z],
                    [x + w, y + l, z + h],
                    [x + w, y, z + h],
                ],
                k: 0.95,
            },
        ]
        faces.sort((a, b) => a.d - b.d)
        for (const f of faces) {
            poly(f.p, shade(color, f.k))
        }
        poly(
            [
                [x, y, z + h],
                [x + w, y, z + h],
                [x + w, y + l, z + h],
                [x, y + l, z + h],
            ],
            color,
            '#444b4420',
        )
    }
    function draw() {
        const shown = Math.floor(model.capacity * Math.min(progress, goal))
        $('current').textContent = `Estimated balloons at this fill: ${fmt(shown)} (${fmt(progress * 100)}%)`
        raf = 0
        ctx.clearRect(0, 0, cw, ch)
        const s = state
        const w = s.width
        const l = s.length
        const t = model.tall / w
        scale = 1
        originX = originY = 0
        const bounds = []
        for (const x of [0, w]) {
            for (const y of [0, t, l]) {
                for (const z of [0, s.split && y <= t ? model.high : s.low]) {
                    bounds.push(project(x, y, z))
                }
            }
        }
        const minX = Math.min(...bounds.map(p => p.x))
        const maxX = Math.max(...bounds.map(p => p.x))
        const minY = Math.min(...bounds.map(p => p.y))
        const maxY = Math.max(...bounds.map(p => p.y))
        scale = Math.min((cw - 90) / (maxX - minX), (ch - 95) / (maxY - minY))
        originX = cw / 2 - ((minX + maxX) / 2) * scale
        originY = (ch + 26) / 2 - ((minY + maxY) / 2) * scale
        // Floor, plank lines and the tall footprint.
        poly(
            [
                [0, 0, 0],
                [w, 0, 0],
                [w, l, 0],
                [0, l, 0],
            ],
            '#dbccb0',
            '#a79b82',
        )
        for (let y = 0; y < l; y += 1.2) {
            line([0, y, 0], [w, y, 0], '#c2b597')
        }
        if (s.split) {
            poly(
                [
                    [0, 0, 0.015],
                    [w, 0, 0.015],
                    [w, t, 0.015],
                    [0, t, 0.015],
                ],
                '#b5c9c35c',
            )
        }
        poly(
            [
                [(w * 3.5) / 16, (l * 3.7) / (23 + 1 / 12), 0.03],
                [(w * 11) / 16, (l * 3.7) / (23 + 1 / 12), 0.03],
                [(w * 11) / 16, (l * 9) / (23 + 1 / 12), 0.03],
                [(w * 3.5) / 16, (l * 9) / (23 + 1 / 12), 0.03],
            ],
            '#ae6353',
        )
        // Rear cutaway wall and window wall; translucent to keep the room legible at every orbit.
        poly(
            [
                [0, l, 0],
                [w, l, 0],
                [w, l, s.low],
                [0, l, s.low],
            ],
            '#e9e5d670',
            '#c6c0ad',
        )
        poly(
            [
                [0, 0, 0],
                [w, 0, 0],
                [w, 0, model.high],
                [0, 0, model.high],
            ],
            '#dae3da45',
            '#b3c0b2',
        )
        for (let x = 1; x < w; x += w / 4) {
            line([x, 0, 1], [x, 0, model.high - 1], '#8ea89b')
        }
        line([0, 0, model.high * 0.5], [w, 0, model.high * 0.5], '#8ea89b')
        // Loft edge: the upstairs floor itself is outside the fill volume.
        if (s.split) {
            poly(
                [
                    [0, t, s.low],
                    [w, t, s.low],
                    [w, l, s.low],
                    [0, l, s.low],
                ],
                '#b6b9a316',
                '#adb29c',
            )
            line([0, t, s.low], [w, t, s.low], '#6f7c70')
            line([w, t, s.low], [w, l, s.low], '#6f7c70')
        }
        const items = furn.map(b => ({
            d: project(b.x + b.w / 2, b.y + b.l / 2, b.z + b.h / 2).depth,
            draw: () => drawBox(b),
        }))
        const n = Math.floor(points.length * progress)
        for (let i = 0; i < n; i++) {
            const b = points[i]
            const q = project(b.x, b.y, b.z)
            items.push({
                d: q.depth,
                draw: () => {
                    const radius = Math.max(1.4, b.r * scale)
                    const grad = ctx.createRadialGradient(
                        q.x - radius * 0.36,
                        q.y - radius * 0.4,
                        radius * 0.07,
                        q.x,
                        q.y,
                        radius,
                    )
                    grad.addColorStop(0, '#ffc6a8')
                    grad.addColorStop(0.2, '#f46b4b')
                    grad.addColorStop(0.5, '#de3527')
                    grad.addColorStop(1, '#8f201c')
                    ctx.globalAlpha = view === 'top' ? 0.72 : 0.95
                    ctx.fillStyle = grad
                    ctx.beginPath()
                    ctx.ellipse(q.x, q.y, radius * 0.92, radius, 0, 0, TAU)
                    ctx.fill()
                    ctx.globalAlpha = 1
                    ctx.fillStyle = '#9d241d'
                    ctx.beginPath()
                    ctx.moveTo(q.x, q.y + radius * 0.85)
                    ctx.lineTo(q.x - 1.7, q.y + radius * 1.16)
                    ctx.lineTo(q.x + 1.7, q.y + radius * 1.16)
                    ctx.fill()
                },
            })
        }
        items.sort((a, b) => a.d - b.d)
        items.forEach(o => o.draw())
        const x2 = s.scope === 'desk' ? model.dw : w
        const y1 = s.scope === 'desk' ? l - model.dl : 0
        const edge = (a, b) => line(a, b, '#377d6a', [5, 4])
        for (const [a, b] of [
            [
                [0, y1, 0],
                [x2, y1, 0],
            ],
            [
                [x2, y1, 0],
                [x2, l, 0],
            ],
            [
                [x2, l, 0],
                [0, l, 0],
            ],
            [
                [0, l, 0],
                [0, y1, 0],
            ],
        ]) {
            edge(a, b)
        }
        if (view !== 'top') {
            for (const [x, y] of [
                [0, y1],
                [x2, y1],
                [x2, l],
                [0, l],
            ]) {
                const h = s.split && y < t ? model.high : s.low
                edge([x, y, 0], [x, y, h])
            }
            edge([0, l, s.low], [x2, l, s.low])
            edge([x2, t, s.low], [x2, t, model.high])
            if (s.split && s.scope === 'whole') {
                edge([0, 0, model.high], [w, 0, model.high])
                edge([0, t, model.high], [w, t, model.high])
            }
        }
        label(`${fmt(w, 1)} ft`, w / 2, -2, 0)
        label(`${fmt(l, 2)} ft`, w + 2, l / 2, 0)
        $('sample').textContent
            = `Showing ${n} of ~${fmt(Math.floor(model.capacity * progress))} balloons (sample)`
    }
    function requestDraw() {
        if (!disposed && !raf) {
            raf = requestAnimationFrame(draw)
        }
        ensureTick()
    }
    function ensureTick() {
        if (!disposed && visible && !document.hidden && running && progress < goal && !tickRaf) {
            tickRaf = requestAnimationFrame(tick)
        }
    }
    function updateMotionButton() {
        if (goal === 0) {
            running = false
        }
        $('pause').textContent = running ? 'Pause' : 'Play'
    }
    let lastReadout = -1
    function tick(time) {
        tickRaf = 0
        if (disposed || !visible || document.hidden) {
            return
        }
        const dt = Math.min(0.1, (time - last) / 1000)
        last = time
        if (running && progress < goal) {
            progress = Math.min(goal, progress + dt * 0.1)
            if (progress >= goal) {
                running = false
                updateMotionButton()
            }
            requestDraw()
        }
        const shown = Math.floor(model.capacity * Math.min(progress, goal))
        if (shown !== lastReadout) {
            $('current').textContent
                = `≈ ${fmt(shown)} balloons at ${fmt(progress * 100)}% · sample shown`
            lastReadout = shown
        }
        ensureTick()
    }
    function camera(next) {
        view = next
        tilt = next === 'top' ? Math.PI / 2 : 0.57
        angle = next === 'top' ? 0 : -0.73
        $('iso').classList.toggle('active', next === 'iso')
        $('top').classList.toggle('active', next === 'top')
        $('iso').setAttribute('aria-pressed', next === 'iso')
        $('top').setAttribute('aria-pressed', next === 'top')
        requestDraw()
    }
    for (const id of numeric) {
        $(id).addEventListener('change', () => {
            if (['width', 'length', 'low', 'high', 'tallArea'].includes(id)) {
                $('preset').value = 'custom'
                for (const k of ['width', 'length', 'low']) {
                    $(`${k}Source`).textContent
                        = 'Custom input · user assumption'
                }
            }
            sync(id)
        })
    }
    $('count').addEventListener('change', () => sync('count'))
    $('fill').addEventListener('input', () => {
        progress = +$('fill').value / 100
        sync('fill')
    })
    $('split').addEventListener('change', () => sync('split'))
    $('scope').addEventListener('change', () => {
        furnitureByScope[priorScope] = state.furniture
        priorScope = $('scope').value
        $('furniture').value = furnitureByScope[priorScope]
        $('furnitureSource').textContent
            = $('scope').value === 'desk'
                ? 'ESTIMATE · desk zone only'
                : 'ESTIMATE · material / blocked volume'
        sync('scope')
    })
    $('preset').addEventListener('change', () => {
        if ($('preset').value === 'baseline') {
            furnitureByScope.whole = 150
            furnitureByScope.desk = 20
            priorScope = 'whole'
            for (const id of numeric) {
                $(id).value = defaults[id]
            }
            $('scope').value = 'whole'
            $('split').checked = true
            $('widthSource').textContent = 'Supplied dimension'
            $('lengthSource').textContent
                = '23 ft 1 in supplied (= 23.083333…)'
            $('lowSource').textContent = '111 in measured = 9.25 ft'
            $('furnitureSource').textContent
                = 'ESTIMATE · material / blocked volume'
        }
        else {
            for (const k of ['width', 'length', 'low']) {
                $(`${k}Source`).textContent = 'Custom input · user assumption'
            }
        }
        sync('preset')
    })
    $('iso').onclick = () => camera('iso')
    $('top').onclick = () => camera('top')
    $('pause').onclick = () => {
        if (!running && progress >= goal) {
            progress = 0
        }
        running = !running
        updateMotionButton()
        requestDraw()
    }
    $('replay').onclick = () => {
        progress = reduced.matches ? goal : 0
        running = !reduced.matches
        updateMotionButton()
        requestDraw()
    }
    $('full').onclick = () => {
        $('fill').value = 100
        goal = 1
        if (reduced.matches || !running) {
            progress = 1
        }
        sync('fill')
    }
    $('empty').onclick = () => {
        $('fill').value = 0
        progress = 0
        sync('fill')
    }
    canvas.addEventListener('pointerdown', (e) => {
        drag = { x: e.clientX, y: e.clientY }
        canvas.setPointerCapture(e.pointerId)
    })
    canvas.addEventListener('pointermove', (e) => {
        if (!drag) {
            return
        }
        if (view === 'top') {
            camera('iso')
        }
        angle += (e.clientX - drag.x) * 0.009
        tilt = Math.min(
            1.35,
            Math.max(0.15, tilt + (e.clientY - drag.y) * 0.005),
        )
        drag = { x: e.clientX, y: e.clientY }
        requestDraw()
    })
    for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) {
        canvas.addEventListener(type, () => (drag = null))
    }
    canvas.addEventListener('keydown', (e) => {
        if (e.key === 'Home') {
            camera('iso')
            e.preventDefault()
            return
        }
        if (
            !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)
        ) {
            return
        }
        e.preventDefault()
        if (view === 'top') {
            camera('iso')
        }
        angle
            += e.key === 'ArrowLeft' ? -0.12 : e.key === 'ArrowRight' ? 0.12 : 0
        tilt = Math.min(
            1.35,
            Math.max(
                0.15,
                tilt
                + (e.key === 'ArrowUp'
                    ? 0.08
                    : e.key === 'ArrowDown'
                        ? -0.08
                        : 0),
            ),
        )
        requestDraw()
    })
    function onReducedChange() {
        if (reduced.matches) {
            running = false
            progress = goal
            updateMotionButton()
            requestDraw()
        }
    }
    reduced.addEventListener('change', onReducedChange)
    const resizeObserver = new ResizeObserver(() => {
        const r = canvas.getBoundingClientRect()
        cw = r.width
        ch = r.height
        const dpr = Math.min(2, devicePixelRatio || 1)
        canvas.width = cw * dpr
        canvas.height = ch * dpr
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
        requestDraw()
    })
    resizeObserver.observe(canvas)
    const visibilityObserver = new IntersectionObserver((entries) => {
        visible = entries[0].isIntersecting
        if (visible) {
            last = performance.now()
            requestDraw()
        }
        else {
            cancelAnimationFrame(tickRaf)
            tickRaf = 0
        }
    })
    visibilityObserver.observe(canvas)
    function onVisibilityChange() {
        cancelAnimationFrame(tickRaf)
        tickRaf = 0
        last = performance.now()
        ensureTick()
    }
    document.addEventListener('visibilitychange', onVisibilityChange)
    function destroy() {
        disposed = true
        cancelAnimationFrame(raf)
        cancelAnimationFrame(tickRaf)
        resizeObserver.disconnect()
        visibilityObserver.disconnect()
        reduced.removeEventListener('change', onReducedChange)
        document.removeEventListener('visibilitychange', onVisibilityChange)
        window.removeEventListener('pagehide', destroy)
        document.removeEventListener('astro:before-swap', destroy)
    }
    window.addEventListener('pagehide', destroy)
    document.addEventListener('astro:before-swap', destroy)
    root.hidden = false
    sync('init')
    // Pure model and read-only diagnostics for repeatable local validation.
    root.balloonLab = {
        estimate,
        getState: () => ({ ...state }),
        getModel: () => ({ ...model }),
        getDiagnostics: () => ({
            points: points.length,
            blocked: points.filter(p => blocked(p.x, p.y, p.z, p.r)).length,
            progress,
            goal,
            running,
            angle,
            tilt,
            view,
            visible,
            tickActive: Boolean(tickRaf),
        }),
    }
})()
