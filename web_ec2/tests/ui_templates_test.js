// Drive the template gallery in headless Edge: pick a template, make a free ad, save it as a template, find it in the gallery, delete it.
// Start the app on port 8765 first, then: node tests/ui_templates_test.js <screenshot folder>
let puppeteer;
try { puppeteer = require("puppeteer"); } catch (e) { puppeteer = require("puppeteer-core"); }   // either works: Edge is launched by path
const out = process.argv[2] || ".";
const base = process.env.STUDIO_URL || "http://127.0.0.1:8765";
const results = [];
const log = (step, ok, detail) => { results.push({ step, ok }); console.log(`${ok ? "PASS" : "FAIL"} ${step} ${detail || ""}`); };

(async () => {
  const browser = await puppeteer.launch({ executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe", headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 1000 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("dialog", async (d) => { await d.accept(); });
  try {
    await page.goto(base + "/editor", { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => document.querySelectorAll("#tpls .tpl").length >= 11, { timeout: 30000 });
    const count = await page.$$eval("#tpls .tpl", (c) => c.length);
    log("gallery shows AI decides plus the library", count >= 11, `${count} cards`);
    await page.waitForFunction(() => [...document.querySelectorAll("#tpls .tpl img")].slice(0, 3).every((i) => i.complete && i.naturalWidth > 0), { timeout: 120000 });
    log("previews load", true);
    await page.screenshot({ path: out + "\\tpl_1_gallery.png" });

    const [card] = await page.$$("xpath/.//div[contains(concat(' ',@class,' '),' tpl ')][.//b[text()='3 reasons']]");
    await card.click();
    const info = await page.$eval("#tplInfo", (e) => e.textContent);
    const length = await page.$eval("#length", (e) => e.value);
    log("picking a template selects it and sets its length", /3 reasons/.test(info) && length === "15", `${info.slice(0, 60)} | length ${length}`);

    await page.type("#prompt", "BeePure organic honey ka ad, kachcha shahad, no sugar, farm se seedha ghar");
    await page.click("#create");
    await page.waitForFunction(() => /^Ready/.test(document.getElementById("status").textContent), { timeout: 240000, polling: 500 });
    const status = await page.$eval("#status", (e) => e.textContent);
    log("ad made from the template", /template: 3 reasons/.test(status), status);
    const look = await page.$eval("#sCard", (e) => e.value);
    log("settings show the template's look", look === "bold", look);

    await page.click("#saveTpl");
    await page.$eval("#tplName", (e) => { e.value = "Honey reasons"; });
    await page.click("#tplBrand");
    await page.click("#tplSave");
    await page.waitForFunction(() => [...document.querySelectorAll("#tpls .tpl b")].some((b) => /Honey reasons \(saved\)/.test(b.textContent)), { timeout: 60000 });
    const selected = await page.$eval("#tpls .tpl.sel b", (e) => e.textContent);
    log("saved template appears in the gallery, selected", /Honey reasons/.test(selected), selected);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: out + "\\tpl_2_saved.png" });

    const [del] = await page.$$("xpath/.//div[contains(concat(' ',@class,' '),' tpl ')][.//b[contains(.,'Honey reasons')]]//button");
    await del.click();
    await page.waitForFunction(() => ![...document.querySelectorAll("#tpls .tpl b")].some((b) => /Honey reasons/.test(b.textContent)), { timeout: 30000 });
    log("saved template can be deleted", true);
  } catch (e) {
    log("run", false, String(e).slice(0, 300));
    await page.screenshot({ path: out + "\\tpl_error.png", fullPage: true });
  }
  log("no JavaScript errors on the page", errors.length === 0, errors.slice(0, 3).join(" | "));
  await browser.close();
  process.exit(results.every((r) => r.ok) ? 0 : 1);
})();
