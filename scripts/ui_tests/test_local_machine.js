const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function testPlaywright() {
  console.log('🚀 Testing Playwright on Local Machine (172.16.39.1)...');
  
  const playwrightTest = `
const { chromium } = require('playwright');
(async () => {
  try {
    const browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto('https://example.com');
    const title = await page.title();
    console.log('✅ Playwright - Page title:', title);
    await page.screenshot({ path: 'local_playwright_test.png' });
    console.log('📸 Playwright - Screenshot saved');
    await browser.close();
    console.log('🎉 Playwright test completed successfully!');
  } catch (error) {
    console.error('❌ Playwright test failed:', error.message);
  }
})();
  `;
  
  try {
    await execPromise(`echo '${playwrightTest}' > local_pw_test.js && node local_pw_test.js`);
  } catch (error) {
    console.error('❌ Playwright test error:', error.message);
  }
}

async function testPuppeteer() {
  console.log('🚀 Testing Puppeteer on Local Machine (172.16.39.1)...');
  
  const puppeteerTest = `
const puppeteer = require('puppeteer');
(async () => {
  try {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();
    await page.goto('https://example.com');
    const title = await page.title();
    console.log('✅ Puppeteer - Page title:', title);
    await page.screenshot({ path: 'local_puppeteer_test.png' });
    console.log('📸 Puppeteer - Screenshot saved');
    await browser.close();
    console.log('🎉 Puppeteer test completed successfully!');
  } catch (error) {
    console.error('❌ Puppeteer test failed:', error.message);
  }
})();
  `;
  
  try {
    await execPromise(`echo '${puppeteerTest}' > local_pp_test.js && node local_pp_test.js`);
  } catch (error) {
    console.error('❌ Puppeteer test error:', error.message);
  }
}

async function main() {
  console.log('🔍 Testing Playwright and Puppeteer on Local Machine (172.16.39.1)');
  console.log('===============================================================');
  
  await testPlaywright();
  console.log('');
  await testPuppeteer();
}

main(); 