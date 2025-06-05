const puppeteer = require('puppeteer');

(async () => {
  console.log('🚀 Starting Puppeteer test on Remote Machine (172.16.39.140)...');
  
  try {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    console.log('📃 Navigating to example.com...');
    await page.goto('https://example.com');
    
    const title = await page.title();
    console.log(`✅ Page title: ${title}`);
    
    await page.screenshot({ path: 'remote_puppeteer_test.png' });
    console.log('📸 Screenshot saved as remote_puppeteer_test.png');
    
    await browser.close();
    console.log('🎉 Puppeteer test completed successfully!');
    
  } catch (error) {
    console.error('❌ Puppeteer test failed:', error.message);
  }
})(); 