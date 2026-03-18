# Setup Guide — Apple Deal Tracker
### For GitHub user: gabex0

This takes about 5 minutes. No terminal needed — everything is done through the GitHub website.

---

## Step 1 — Create the repo (you're already here)

On the "Create a new repository" page:

- **Repository name:** `apple-deals`
- **Description:** *(leave blank or type anything)*
- **Visibility:** ✅ **Private** ← make sure this is selected
- **Initialize this repository with:** leave all boxes **unchecked**

Click **"Create repository"**

---

## Step 2 — Upload the files

After creating the repo, you'll see an empty repo page.

1. Click **"uploading an existing file"** (the link in the middle of the page)
2. Drag all **4 files** into the upload area:
   - `index.html`
   - `scraper.py`
   - `SETUP.md` *(this file — optional to include)*
   - The `.github` **folder** — drag the entire folder in
     > ⚠️ The `.github/workflows/update.yml` file must be at the path `.github/workflows/update.yml` inside the repo. GitHub's drag-and-drop uploader handles nested folders automatically.
3. Scroll down, leave the commit message as-is, click **"Commit changes"**

---

## Step 3 — Enable GitHub Pages

This is what gives you a live URL to visit.

1. In your repo, click **Settings** (top menu bar)
2. Click **Pages** in the left sidebar
3. Under **"Build and deployment"**, set:
   - Source: **Deploy from a branch**
   - Branch: **main** · folder: **/ (root)**
4. Click **Save**

After about 60 seconds, refresh the page. You'll see:

> ✅ Your site is live at **https://gabex0.github.io/apple-deals/**

That's your URL. Bookmark it.

---

## Step 4 — Enable GitHub Actions

1. Click the **Actions** tab in your repo
2. You may see a banner saying "Workflows aren't running" — click **"I understand my workflows, go ahead and enable them"**
3. You should now see **"Daily Price Update"** listed in the left sidebar

To test it immediately:
1. Click **"Daily Price Update"**
2. Click **"Run workflow"** → **"Run workflow"** (green button)
3. Watch it run — takes about 30 seconds

---

## Step 5 — You're done

Your site will:
- ✅ Be live at `https://gabex0.github.io/apple-deals/`
- ✅ Be password protected (password: **gabecool**)
- ✅ Auto-update every day at 9:00 AM UTC (2 AM Pacific)
- ✅ Only be accessible from your private repo

---

## How to manually trigger an update anytime

1. Go to your repo → **Actions** tab
2. Click **"Daily Price Update"**
3. Click **"Run workflow"** → **"Run workflow"**

---

## How to update prices manually (if the scraper gets blocked)

Open `index.html` in GitHub's editor (click the file → pencil icon ✏️).
Prices are in the HTML tables — just find and replace the dollar amounts.
Commit when done — the site updates in about 60 seconds.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Site shows "404" | Wait 2 minutes after enabling Pages, then refresh |
| Actions tab says "disabled" | Go to Settings → Actions → Allow all actions |
| Scraper runs but prices don't change | Amazon/BB may have blocked the request — baseline prices are used as fallback. Site still updates with today's date. |
| Password not working | Make sure you're typing `gabecool` exactly, no spaces |

---

## File structure in your repo

```
apple-deals/
├── index.html              ← the website
├── scraper.py              ← daily price fetcher
├── SETUP.md                ← this guide
└── .github/
    └── workflows/
        └── update.yml      ← GitHub Actions schedule
```
