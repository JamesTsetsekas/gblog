import * as React from 'react'
import Giscus, { type Repo } from '@giscus/react'
import { Settings } from '@/config.ts'

const id = 'inject-comments'
const commentSetting = Settings.Comment.giscus

function getCurrentTheme(): string {
    if (window.localStorage.getItem('hs_theme')) {
        return window.localStorage.getItem('hs_theme') ?? 'default'
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default'
}

function convertThemToGiscusThem(them: string | undefined): string {
    if (!them) {
        return commentSetting.lightThem
    }

    return them === 'dark' ? commentSetting.darkThem : commentSetting.lightThem
}

function BlogComments() {
    const [mounted, setMounted] = React.useState(false)
    const [theme, setTheme] = React.useState(commentSetting.lightThem)

    React.useEffect(() => {
        const handleThemeChange = (event: Event) => {
            setTheme(convertThemToGiscusThem((event as CustomEvent<string>).detail))
        }
        const theme = convertThemToGiscusThem(getCurrentTheme())
        setTheme(theme)

        window.addEventListener('on-hs-appearance-change', handleThemeChange)

        return () => {
            window.removeEventListener('on-hs-appearance-change', handleThemeChange)
        }
    }, [])

    React.useEffect(() => {
        setMounted(true)
    }, [])

    return (
        <section aria-labelledby="discussion-heading" className="w-full">
            <h2 id="discussion-heading" className="mb-2 text-2xl font-bold text-neutral-800 dark:text-neutral-300">Discussion</h2>
            <p className="mb-5 text-sm text-neutral-600 dark:text-neutral-400">Share a thought or question. Sign in with GitHub to comment or react.</p>
            {mounted
                ? (
                        <Giscus
                            id={id}
                            repo={commentSetting.repo as Repo}
                            repoId={commentSetting.repoId}
                            category={commentSetting.category}
                            categoryId={commentSetting.categoryId}
                            mapping="pathname"
                            strict="1"
                            reactionsEnabled="1"
                            emitMetadata="0"
                            inputPosition="top"
                            lang="en"
                            loading="lazy"
                            theme={theme}
                        />
                    )
                : null}
        </section>
    )
}

export default BlogComments
