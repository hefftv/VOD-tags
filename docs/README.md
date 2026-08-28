# VOD Tags Documentation

This folder contains the full documentation for **VOD Tags** (Twitch Stream Highlights Detection). Pages under [`wiki/`](wiki/) are formatted for the [GitHub Wiki](https://github.com/hefftv/VOD-tags/wiki).

## Wiki pages

| Page | Description |
|------|-------------|
| [Home](wiki/Home.md) | Overview, purpose, and quick links |
| [Architecture](wiki/Architecture.md) | System components and data flow |
| [Process Flow](wiki/Process-Flow.md) | End-to-end highlight detection sequence |
| [ML Pipeline](wiki/ML-Pipeline.md) | Feature extractors and metamodel |
| [Deployment](wiki/Deployment.md) | GCP, local containers, and cloud-generic |
| [Configuration](wiki/Configuration.md) | Environment variables and config mapping |

## Publish to GitHub Wiki

GitHub wikis are a separate git repository. After authenticating with GitHub (`gh auth login`):

```bash
# One-time: clone the wiki repo (created when you push the first page)
git clone https://github.com/hefftv/VOD-tags.wiki.git /tmp/vod-tags-wiki

# Copy pages
cp docs/wiki/*.md /tmp/vod-tags-wiki/

# Commit and push
cd /tmp/vod-tags-wiki
git add .
git commit -m "Add architecture and deployment documentation"
git push origin master
```

Alternatively, enable the wiki in **Repository Settings → Features → Wikis**, then create pages manually and paste content from `docs/wiki/`.

## Diagrams

Process and architecture diagrams use [Mermaid](https://mermaid.js.org/). GitHub Wiki and GitHub-flavored Markdown render Mermaid in most views.

## Screenshots

UI screenshots live in [`../images/`](../images/) and are referenced from wiki pages via raw GitHub URLs.
