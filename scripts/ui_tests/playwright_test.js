const { chromium } = require('playwright');

(async () => {
  console.log('🚀 Starting Playwright test on Remote Machine (172.16.39.140)...');
  
  try {
    const browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    console.log('📃 Navigating to example.com...');
    await page.goto('https://example.com');
    
    const title = await page.title();
    console.log(`✅ Page title: ${title}`);
    
    await page.screenshot({ path: 'remote_playwright_test.png' });
    console.log('📸 Screenshot saved as remote_playwright_test.png');
    
    await browser.close();
    console.log('🎉 Playwright test completed successfully!');
    
  } catch (error) {
    console.error('❌ Playwright test failed:', error.message);
  }
})(); 