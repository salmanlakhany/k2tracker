# Nautilus Watch — Chrono24 Tracker

A free, self-updating dashboard of every Patek Philippe Nautilus reference
currently listed on Chrono24. A GitHub Actions job checks Chrono24 once an
hour and updates the page you see at your GitHub Pages URL.

**Cost: $0.** GitHub Actions gives free accounts 2,000 build-minutes/month
(this job takes seconds and runs 24 times/day, so it uses a small fraction
of that), and GitHub Pages hosting is free for public repos.

## Setup (10 minutes, one time)

1. **Create a free GitHub account** at github.com if you don't have one.

2. **Create a new repository**
   - Click the "+" in the top right → "New repository"
   - Name it anything, e.g. `nautilus-tracker`
   - Set it to **Public** (required for free GitHub Pages)
   - Don't initialize with a README (we already have one)

3. **Upload these files**
   - On the new repo's page, click "uploading an existing file"
   - Drag in this entire folder's contents, preserving the structure:
     ```
     scraper.py
     README.md
     .github/workflows/scrape.yml
     docs/index.html
     docs/data.json
     ```
   - Commit the files to the `main` branch.

4. **Turn on GitHub Pages**
   - Go to the repo's **Settings → Pages**
   - Under "Build and deployment", set **Source: Deploy from a branch**
   - Branch: `main`, folder: `/docs` → Save
   - GitHub will give you a URL like
     `https://yourusername.github.io/nautilus-tracker/`
     — that's your dashboard.

5. **Turn on Actions permissions** (needed so the job can commit updated data)
   - Settings → Actions → General → "Workflow permissions"
   - Select **Read and write permissions** → Save

6. **Run it once manually** to check everything works
   - Go to the **Actions** tab → "Scrape Chrono24 Nautilus listings" → "Run workflow"
   - After ~30 seconds, check your Pages URL — you should see listings.

After that, it runs automatically every hour — no further action needed.

## If listings stop showing up

Chrono24 occasionally changes their page layout, which can break the
parser in `scraper.py`. Check the Actions tab for a failed/empty run —
the log will say `WARNING: parsed 0 listings`. The most likely fix is
updating the `sortorder` value or the regex patterns near the top of
`scraper.py` to match Chrono24's current markup.

## Notes

- This scrapes public Chrono24 listing pages (there's no official API).
  The job makes at most 2 requests per hour, which is intentionally light.
- Prices shown are whatever Chrono24 displays (usually USD as listed by
  the dealer); currency/shipping terms aren't normalized.
