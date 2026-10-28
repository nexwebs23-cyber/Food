# Zaika Worlds: deploy with GitHub and Vercel

The site name is Zaika Worlds and the domain is
`https://zaikaworlds.com/`. This folder is a normal static website. It contains one page
(`index.html`), its photos (`assets/`), and the three Beef Nihari videos
(`videos/`). There is no build step and no framework. Follow the steps
below in order. Words in angle brackets, like
`<YOUR-GITHUB-REPO-NAME>`, are placeholders. Replace them with your own
names. The site name and domain are already chosen: Zaika Worlds and
`https://zaikaworlds.com/`.

## What is in this folder

- `index.html`: the whole site on one page. Recipes open in a pop-up
  (modal) on this page, so there are no separate recipe pages.
- `assets/`: every photo used by the page, as a separate file.
- `videos/`: the three Beef Nihari videos, one per language:
  English, Hindi, and Roman Urdu. Changing the language on the page
  switches the video, and keeps the playback position.
- `vercel.json`: tells Vercel this is a plain static site.
- `robots.txt`: allows search engines to crawl the site. It does not
  mention a sitemap. The sitemap is at
  `https://zaikaworlds.com/sitemap.xml`.
- `sitemap.xml`: lists only the homepage, at
  `https://zaikaworlds.com/`. Recipes are not listed
  in it, because they have no separate URLs. This is a limitation of
  the one-page demo design, not an error in this folder.
- `tools/split_export.py`: the script used to split the single-file
  export into this folder. You will use it again after future edits.
  See step 5.

## Before you start

You need Git installed on your computer, a GitHub account, and a Vercel
account. You do all of the steps below in a terminal (command line) in
this folder, except creating the empty repo and importing it, which you
do in your web browser.

## Step 1. Create an empty GitHub repo

1. Go to github.com and sign in.
2. Click New repository.
3. Choose a repository name. Any name is fine. Write it down. This guide
   calls it `<YOUR-GITHUB-REPO-NAME>`.
4. Leave the repo empty. Do NOT add a README, a .gitignore, or a
   licence in GitHub. This folder already has the files you need.
5. Choose Public or Private, whichever you prefer. A private repo still
   works with Vercel.
6. Click Create repository. GitHub will show you an empty repo page.
   Keep that page open. You need the repo web address (URL) from it,
   which looks like this:
   `https://github.com/<YOUR-GITHUB-USERNAME>/<YOUR-GITHUB-REPO-NAME>.git`

## Step 2. Push these files to GitHub from a terminal

Open a terminal, go into this folder, and run these commands one at a
time. Replace the placeholders with your own values.

```bash
git init
git add .
git commit -m "Zaika Worlds demo, split for GitHub and Vercel"
git branch -M main
git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/<YOUR-GITHUB-REPO-NAME>.git
git push -u origin main
```

What each command does:

- `git init` starts Git tracking in this folder.
- `git add .` stages all the files in this folder.
- `git commit` saves them as one version with a message.
- `git branch -M main` names the main branch `main`.
- `git remote add origin ...` connects this folder to your new empty
  GitHub repo.
- `git push -u origin main` uploads the files to GitHub.

If Git asks for your name and email the first time, set them with:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Then run the `git push` command again.

Do NOT add the original single-file export to this folder or to Git.
It is about 133 MB. GitHub hard-blocks any single file over 100 MB,
and the push will fail. Only the split files in this folder belong
in the repo.

## Step 3. Import the repo in Vercel and deploy

1. Go to vercel.com and sign in.
2. Click Add New, then Project.
3. Find your new GitHub repo in the list and click Import. If it is
   not listed, connect your GitHub account first, or use the
   "Import Git Repository" box with the repo URL from step 1.
4. Vercel will show project settings. Set them exactly like this:
   - Framework Preset: Other
   - Build Command: leave empty (no build command)
   - Output Directory: leave empty (the files are already at the top
     level of the repo)
   - Install Command: leave empty
   - Root Directory: leave as the top level of the repo
   - Environment Variables: none. Do not add any.
5. Click Deploy.
6. Wait for the deployment to finish. Vercel will give you a web
   address ending in `.vercel.app`. Open it and check the site:
   the grid loads, a recipe pop-up opens, the language buttons change
   the text, and the Beef Nihari video plays with sound in each
   language.

## Step 4. Add a custom domain and HTTPS in Vercel

You only need this step if you want your own domain name instead of
the `.vercel.app` address. HTTPS is handled by Vercel automatically
once the domain is connected. There is no certificate to install
yourself.

1. Buy the domain zaikaworlds.com from any domain seller, if you do
   not own it yet, or use it if you already own it.
2. In Vercel, open your project, then Settings, then Domains.
3. Type zaikaworlds.com and click Add.
4. Vercel will show you the DNS records to add. Add them at your
   domain seller, exactly as Vercel shows them. This is usually one
   `A` record or one `CNAME` record. Vercel shows the exact values
   for your project, so follow what it shows on the day you do this.
5. Wait for DNS to update. This can take minutes or, rarely, up to
   a day.
6. When Vercel shows the domain as valid, open `https://` followed
   by your domain in a browser. The site should load over HTTPS.
7. The sitemap in this folder already uses
   `https://zaikaworlds.com/`. After the domain is live, check
   `https://zaikaworlds.com/sitemap.xml` in a browser, then submit
   that sitemap in Google Search Console
   under your domain, if you use Search Console.

## Step 5. Redeploy after a future demo edit

When the demo is edited again, do NOT edit `index.html` in this folder
by hand, and do NOT commit a new single-file export. Repeat the split
step instead:

1. Get the new exported single HTML file from the demo. Save it
   somewhere outside this repo, for example your Downloads folder.
   Do not copy it into this repo.
2. In a terminal, run the split script with the exported file as the
   argument, and this folder as the output folder:

```bash
python3 tools/split_export.py /path/to/the-new-export.html .
```

Run this command from inside this folder. The script rebuilds
`index.html`, `assets/`, and `videos/` from the new export. It does
not touch `vercel.json`, `robots.txt`, `sitemap.xml`, or this guide.
If a photo or video was removed in the new export, the script removes
its old extracted file too, because it rebuilds the `assets/` and
`videos/` folders each time.

3. Check that the site still works locally if you can, then commit
   and push:

```bash
git add .
git commit -m "Update demo export"
git push
```

4. Vercel redeploys automatically when it sees the new push. You do
   not need to click Deploy again. Wait a short while, then open
   your site address and check it.

## Size limits that matter

- GitHub: no single file may be over 100 MB. Every file in this folder
  is under that limit. The largest files are the three videos, each
  about 22 MB. Never commit the unsplit export, which is about
  133 MB.
- Vercel: a deployment on the free plan must be under 250 MB in
  total. This folder is about 75.5 MB in total, so it fits. The three
  videos are most of that total (about 67 MB together).
- If a future export makes the total go over 250 MB, or any single
  file go over 100 MB, stop and fix the size before pushing. Do not
  just push and hope. The usual fixes, in this order, are:
  1. Run the split script again and check the sizes. A stale large
     file left in the folder is the most common cause.
  2. Ask for the photos to be made smaller before the next export,
     or for fewer large photos.
  3. For videos, host them somewhere made for video (for example
     YouTube) and link to them, instead of shipping the video files
     in the repo. Do not compress, re-encode, or trim a video
     yourself unless you have checked that the result still looks
     and sounds right.
  4. If none of that is possible, split the site or use a paid plan
     with a higher limit. Do not silently drop a video or a photo
     to get under a limit.

## If something goes wrong

- Push rejected because a file is too large: you probably added the
  unsplit export. Remove it from the folder, run `git rm` on it if
  it was staged, and push again.
- Vercel shows a blank page or missing photos: check that `assets/`
  and `index.html` are both in the repo on GitHub, and that the
  deployment finished. A missing `assets/` folder is the usual cause.
- Video does not play: check that `videos/` is in the repo and that
  you opened the Beef Nihari recipe, which is the only recipe with a
  video. Other recipes show a "coming soon" message on purpose.
- Domain shows an error after step 4: the DNS records are usually
  still updating, or were typed differently from what Vercel showed.
  Re-check them in Vercel under Settings, then Domains.
