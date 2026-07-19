---
name: playwright-record-demo
description: Record a short video demo of a recently implemented application feature — its visible impact in the running app, not the code. Use when the user asks to "record a demo", "capture a video of the feature", or wants a clip to attach to a GitHub issue/PR after implementing a change.
metadata:
  origin: local
  origin-status: local
---

# Playwright Record Demo

Produce a short, watchable screencast showing what a feature change looks like in the running application. Output: a `.webm` file the user can attach to an issue or PR.

## Prerequisites

- Node.js and Playwright: `npm i -D playwright && npx playwright install chromium` (one-time per machine; Playwright bundles its own ffmpeg and browser).
- Web application reachable in a browser (the primary path). Non-browser targets: see "Beyond the browser" in Reference.

## Steps

1. **Write the demo script.** From the issue, diff, or conversation, list the ordered user actions that make the change *visible*: starting URL, clicks/inputs, and the moment the new behaviour appears. 3–8 actions; the script is done when a stranger could follow it and see the feature. Confirm the script with the user only if the feature's visible impact is ambiguous.
2. **Get the app running.** Reuse a live dev server if one exists; otherwise start it with the project's normal command (check `package.json` scripts, `Makefile`, README) as a background/supervised process, and wait for readiness (port accepting connections or ready log line). Done when the starting URL responds.
3. **Write the recording script.** A one-off `demos/record.mjs` using Playwright's `recordVideo` — the video finalizes automatically when the context closes:

   ```js
   import { chromium } from 'playwright';
   import { rename } from 'node:fs/promises';

   const browser = await chromium.launch();
   const context = await browser.newContext({
     viewport: { width: 1280, height: 720 },
     recordVideo: { dir: 'demos/', size: { width: 1280, height: 720 } },
   });
   const page = await context.newPage();

   // Off-camera setup happens BEFORE the first on-script action is possible to
   // avoid: login, seed data, dismiss boilerplate — do it here, fast, no pauses.

   await page.goto('<starting URL>');
   await page.waitForTimeout(800);              // settle frame
   // ...demo script actions, each followed by page.waitForTimeout(800–1500)
   //    so the viewer can see the result...
   await page.waitForTimeout(1200);             // hold final state

   const video = page.video();
   await context.close();                        // finalizes the video
   await browser.close();
   await rename(await video.path(), 'demos/<feature-or-issue-slug>-<YYYYMMDD>.webm');
   ```

   Pace deliberately: a pause after every visible change. A demo with no pauses is unwatchable.
4. **Record.** Run the script (`node demos/record.mjs`). Done when the named `.webm` exists with nonzero size.
5. **Deliver.** Report the absolute path, duration, and size; delete `record.mjs` unless the user wants to keep it. Done when the path is reported.

## Reference

- **Watchability check:** if the recording missed the moment (too fast, wrong element, error on screen), edit the script and re-record — a second take is cheaper than editing video.
- **GitHub upload:** issue/PR comments accept `.webm` by drag-and-drop. If the user needs `.mp4` (Slack, email): `ffmpeg -i demo.webm -c:v libx264 -pix_fmt yuv420p demo.mp4` (ffmpeg required only for this conversion).
- **Cursor visibility:** headless recordings show no mouse cursor. Make actions legible through their *effects* (focus states, typed text appearing, scrolling into view before clicking) and pacing.
- **Beyond the browser:** the Steps assume a web app. Other targets swap only the capture mechanics (steps 3–4); the demo script, pacing, and delivery steps stay the same.
  - *Electron app*: same stack — `await _electron.launch({ args: ['.'], recordVideo: { dir: 'demos/' } })` (from `playwright`); video finalizes on `app.close()`.
  - *Native desktop app*: record the screen natively with `screencapture -V <seconds> demos/<slug>.mov` (macOS, zero dependencies). Agents cannot reliably drive native UI — start the timed recording, tell the user to perform the demo script by hand, then deliver the file.
  - *CLI/TUI*: video is the wrong medium — record with `asciinema rec`, or paste the terminal output into the issue directly.
