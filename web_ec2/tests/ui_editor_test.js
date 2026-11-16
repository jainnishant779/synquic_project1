// Browser test of the Ad Studio editor in headless Edge or Chrome: create a free ad, pause on the timeline, typed edit, apply,
// undo, inline edit, split, download. Start the app first (no keys needed): uvicorn main:app --port 8765
// Run: NODE_PATH=<folder with puppeteer> node tests/ui_editor_test.js <screenshot folder> [browser path]
const puppeteer = require("puppeteer");
const out = process.argv[2];
const base = "http://127.0.0.1:8765";
const results = [];
const log = (step, ok, detail) => { results.push({ step, ok, detail }); console.log(`${ok ? "PASS" : "FAIL"} ${step} ${detail || ""}`); };

async function waitStatus(page, test, timeout = 240000) {
  await page.waitForFunction((t) => {
    const s = document.getElementById("status").textContent;
    return new RegExp(t).test(s);
  }, { timeout, polling: 500 }, test);
}

(async () => {
  const browser = await puppeteer.launch({ executablePath: process.argv[3] || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe", headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 1000 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("dialog", async (d) => { console.log("DIALOG", d.type(), d.message().slice(0, 100)); await d.accept(); });
  page.on("request", (r) => { if (/\/(undo|redo|edit|timeline)$/.test(r.url())) console.log("REQUEST", r.method(), r.url().split("/api/")[1]); });
  page.on("response", (r) => { if (/\/(undo|redo|edit|timeline)$/.test(r.url())) console.log("RESPONSE", r.status(), r.url().split("/api/")[1]); });
  try {
    await page.goto(base + "/editor", { waitUntil: "networkidle0" });
    await page.waitForFunction(() => document.getElementById("level").options.length === 3);
    const banner = await page.$eval("#banner", (e) => e.textContent);
    log("config loaded, paid levels locked without a key", /Free level works/.test(banner), banner.slice(0, 90));

    await page.type("#prompt", "BeePure organic honey ka 10 second Instagram ad, kachcha shahad, no sugar, farm se seedha ghar");
    await page.select("#length", "10");
    await page.click("#create");
    await waitStatus(page, "^Ready");
    await page.waitForFunction(() => document.getElementById("player").readyState >= 1, { timeout: 30000 });
    const blocks = await page.$$eval("#scenes .sblock", (b) => b.length);
    const bars = await page.$$eval("#lanes .tbar", (b) => b.length);
    log("ad created from one prompt", blocks >= 3 && bars >= 3, `${blocks} scene blocks, ${bars} text bars`);
    await page.screenshot({ path: out + "\\ui_1_created.png", fullPage: true });

    // Pause at about 30% of the ad by clicking the timeline.
    const scenesEl = await page.$("#scenes");
    const clickAt = async (fraction) => {   // the timeline sits below the fold; scroll it into view before clicking
      await scenesEl.scrollIntoView();
      const b = await scenesEl.boundingBox();
      await page.mouse.click(b.x + b.width * fraction, b.y + b.height / 2);
      await new Promise((r) => setTimeout(r, 700));
    };
    await clickAt(0.3);
    const title = await page.$eval("#momentTitle", (e) => e.textContent);
    const t = await page.$eval("#player", (v) => v.currentTime);
    log("timeline click pauses at that moment", t > 2 && t < 4.5 && /^At 0:0/.test(title), `${title} | currentTime ${t.toFixed(2)}`);

    // Typed edit at this moment: propose, then apply.
    await page.type("#instruction", "'Shuddh shahad' likho, peele rang mein");
    await page.click("#suggest");
    await page.waitForSelector("#proposal .diff", { timeout: 30000 });
    const diff = await page.$eval("#proposal .diff", (e) => e.textContent);
    log("typed request shows the change first", /Shuddh shahad/.test(diff), diff.slice(0, 120));
    const [apply] = await page.$$("xpath/.//button[contains(., 'Apply this change')]");
    await apply.click();
    await page.waitForFunction(() => /Version 2 of 2/.test(document.getElementById("versionInfo").textContent), { timeout: 120000 });
    const texts = await page.$$eval("#lanes .tbar", (b) => b.map((x) => x.textContent));
    log("applied: new version and the new text on the timeline", texts.includes("Shuddh shahad"), texts.join(" | ").slice(0, 120));

    await page.waitForFunction(() => !document.getElementById("undo").disabled, { timeout: 30000 });
    await page.click("#undo");
    await page.waitForFunction(() => /Version 1 of 2/.test(document.getElementById("versionInfo").textContent), { timeout: 120000 });
    const undone = await page.$$eval("#lanes .tbar", (b) => b.map((x) => x.textContent));
    log("undo brings the old text back", !undone.includes("Shuddh shahad"), undone.join(" | ").slice(0, 120));

    // Inline edit of the text on screen, then Apply edits.
    await clickAt(0.05);
    await page.$eval("#layers textarea", (a) => { a.value = "Asli *shahad*"; a.dispatchEvent(new Event("input", { bubbles: true })); });
    const enabled = await page.$eval("#apply", (b) => !b.disabled);
    await page.waitForFunction(() => !document.getElementById("apply").disabled, { timeout: 30000 });
    await page.click("#apply");
    await page.waitForFunction(() => /Version 2 of 2/.test(document.getElementById("versionInfo").textContent), { timeout: 120000 });
    const edited = await page.$$eval("#lanes .tbar", (b) => b.map((x) => x.textContent));
    log("inline edit applies (and drops the old redo branch)", enabled && edited.includes("Asli shahad"), edited.slice(0, 3).join(" | "));

    // Split the scene at the playhead.
    const before = await page.$$eval("#scenes .sblock", (b) => b.length);
    await clickAt(0.1);
    await page.waitForFunction(() => !document.getElementById("split").disabled, { timeout: 30000 });
    await page.click("#split");
    await page.waitForFunction((n) => document.querySelectorAll("#scenes .sblock").length === n + 1, { timeout: 120000 }, before);
    log("split here adds a scene", true, `${before} -> ${before + 1} scenes`);
    await page.screenshot({ path: out + "\\ui_2_edited.png", fullPage: true });
    const href = await page.$eval("#download", (a) => a.href);
    const head = await page.evaluate(async (u) => { const r = await fetch(u); return [r.status, r.headers.get("content-type")]; }, href);
    log("download link serves the MP4", head[0] === 200 && head[1] === "video/mp4", head.join(" "));
  } catch (e) {
    const where = await page.evaluate(() => ({ banner: document.getElementById("banner").textContent, status: document.getElementById("status").textContent,
      version: document.getElementById("versionInfo").textContent, undoDisabled: document.getElementById("undo").disabled }));
    log("run", false, String(e).slice(0, 200) + " | " + JSON.stringify(where));
    await page.screenshot({ path: out + "\\ui_error.png", fullPage: true });
  }
  log("no JavaScript errors on the page", errors.length === 0, errors.slice(0, 3).join(" | "));
  await browser.close();
  process.exit(results.every((r) => r.ok) ? 0 : 1);
})();
