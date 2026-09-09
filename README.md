# James Tsetsekas — Blog

Source for [blog.JamesTsetsekas.com](https://blog.JamesTsetsekas.com), a personal publication about Bitcoin, Nostr, Lightning, security, AI, and product engineering.

The site is a static [Astro](https://astro.build/) application with Markdown and MDX content, category pages, RSS, a sitemap, responsive images, light and dark themes, and optional analytics and comments.

## Development

Requirements: a current Node.js release and npm.

```bash
npm ci
npm run dev
```

The local development server starts with hot reload. Before opening a pull request, run:

```bash
npm run lint
npm run build
```

Use `npm run preview` to inspect the production build locally.

## Content structure

- `src/content/posts/` — Markdown and MDX articles
- `src/content/categories/` — category names and descriptions
- `src/images/banners/` — local article banners
- `src/images/posts/` — inline diagrams and supporting article images
- `src/config.ts` — site metadata, navigation, analytics, comments, and asset configuration

Posts use Astro content collections. A minimal article looks like this:

```yaml
---
title: "Article title"
description: "A concise summary for previews and search results."
pubDate: "2026-09-09 12:00:00"
category: ["bitcoin", "security"]
banner: "@images/banners/example.png"
tags: ["Bitcoin", "Security"]
selected: false
---
```

Use a local 16:9 banner when possible, write descriptive alt text for inline images, and attribute external data or diagrams next to the visual. Add a matching file in `src/content/categories/` before assigning a new category.

## Production and assets

`npm run build` creates a static site. Image optimization can be enabled with `ASTRO_IMAGE_OPTIMIZE`. The optional `S3_*` configuration uploads built assets through `astro-uploader`; without it, assets remain part of the normal static build. Never commit credentials or local environment files.

## Credits

The original theme and much of the site foundation came from [godruoyi/gblog](https://github.com/godruoyi/gblog) and [mearashadowfax/ScrewFast](https://github.com/mearashadowfax/ScrewFast). This repository has since been adapted for James’s publication and content workflow.

## License

Released under the [MIT License](LICENSE).
