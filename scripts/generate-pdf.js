const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();
  await page.goto('https://andreacacioppo.github.io/', { waitUntil: 'networkidle2' });
  await page.evaluate(() => document.querySelector('.download-pdf')?.remove());
  await page.pdf({
    path: 'curriculum/download.pdf',
    format: 'A4',
    printBackground: true
  });
  await browser.close();
})();
