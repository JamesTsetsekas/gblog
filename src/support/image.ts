import fs from 'node:fs/promises'

export async function blurStyle(image?: string) {
    if (!image) {
        return {}
    }

    const data = await blurImage(image)
    return {
        backgroundSize: 'cover',
        backgroundPosition: '50% 50%',
        backgroundRepeat: 'no-repeat',
        backgroundImage: `url("data:image/svg+xml;charset=utf-8,${data}")`,
    }
}

export async function blurImage(filePath: string): Promise<string> {
    const { default: sharp } = await import('sharp')
    const buffer = await fs.readFile(filePath)

    const img = sharp(buffer)
    const { width, height } = await img.metadata()
    if (width == null || height == null) {
        throw new Error(`Invalid image path: ${filePath}`)
    }
    const aspectRatio = width / height
    const blurWidth = 8
    const blurHeight = Math.round(blurWidth / aspectRatio)
    const blurImage = await img.resize(blurWidth, blurHeight).webp({ quality: 1 }).toBuffer()
    const blurDataURL = `data:image/webp;base64,${blurImage.toString('base64')}`

    const std = 20
    const svgWidth = blurWidth ? blurWidth * 40 : width
    const svgHeight = blurHeight ? blurHeight * 40 : height

    const viewBox = svgWidth && svgHeight ? `viewBox='0 0 ${svgWidth} ${svgHeight}'` : ''

    return `%3Csvg xmlns='http://www.w3.org/2000/svg' ${viewBox}%3E%3Cfilter id='b' color-interpolation-filters='sRGB'%3E%3CfeGaussianBlur stdDeviation='${std}'/%3E%3CfeColorMatrix values='1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 100 -1' result='s'/%3E%3CfeFlood x='0' y='0' width='100%25' height='100%25'/%3E%3CfeComposite operator='out' in='s'/%3E%3CfeComposite in2='SourceGraphic'/%3E%3CfeGaussianBlur stdDeviation='${std}'/%3E%3C/filter%3E%3Cimage width='100%25' height='100%25' x='0' y='0' preserveAspectRatio='xMidYMid slice' style='filter: url(%23b);' href='${blurDataURL}'/%3E%3C/svg%3E`
}
