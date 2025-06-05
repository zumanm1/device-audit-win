const puppeteer = require('puppeteer');

async function runPuppeteerUITest() {
  console.log('🚀 Starting Comprehensive Web UI Test with Puppeteer');
  console.log('===================================================');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  const baseUrl = 'http://localhost:5010';
  const testResults = {
    passed: 0,
    failed: 0,
    issues: []
  };
  
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      testResults.issues.push(`Console Error: ${msg.text()}`);
    }
  });
  
  try {
    // Test 1: Performance and Loading
    console.log('\n⚡ Test 1: Performance and Loading Speed...');
    const startTime = Date.now();
    await page.goto(baseUrl, { waitUntil: 'networkidle2' });
    const loadTime = Date.now() - startTime;
    
    console.log(`📊 Page load time: ${loadTime}ms`);
    if (loadTime < 5000) {
      console.log('✅ Page loads within acceptable time');
      testResults.passed++;
    } else {
      console.log('⚠️ Page load time is slow');
      testResults.issues.push('Slow page load time');
      testResults.failed++;
    }
    
    await page.screenshot({ path: 'puppeteer_01_performance.png' });
    
    // Test 2: Interactive Elements
    console.log('\n🖱️ Test 2: Testing Interactive Elements...');
    try {
      // Test buttons
      const buttons = await page.$$('button, .btn, input[type="submit"]');
      console.log(`📊 Found ${buttons.length} interactive buttons`);
      
      if (buttons.length > 0) {
        // Test button hover states
        await buttons[0].hover();
        await page.screenshot({ path: 'puppeteer_02_button_hover.png' });
        console.log('✅ Button interaction working');
        testResults.passed++;
      } else {
        console.log('⚠️ No buttons found for interaction testing');
        testResults.issues.push('No interactive buttons found');
        testResults.failed++;
      }
    } catch (error) {
      console.log(`❌ Interactive elements test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Interactive elements error: ${error.message}`);
    }
    
    // Test 3: AJAX/Fetch Requests
    console.log('\n🌐 Test 3: Testing AJAX Requests...');
    const requests = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/') || request.url().includes('/device_status')) {
        requests.push(request.url());
      }
    });
    
    // Trigger some navigation to generate requests
    try {
      await page.click('a[href*="inventory"], text="Inventory"');
      await page.waitForTimeout(2000);
      
      if (requests.length > 0) {
        console.log(`✅ Detected ${requests.length} API requests`);
        requests.forEach(req => console.log(`   - ${req}`));
        testResults.passed++;
      } else {
        console.log('⚠️ No API requests detected');
        testResults.issues.push('No API requests detected');
      }
    } catch (error) {
      console.log(`❌ AJAX test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`AJAX test error: ${error.message}`);
    }
    
    // Test 4: Form Functionality
    console.log('\n📝 Test 4: Testing Form Functionality...');
    try {
      await page.goto(`${baseUrl}/inventory`);
      await page.waitForSelector('body', { timeout: 5000 });
      
      const forms = await page.$$('form');
      const inputs = await page.$$('input, textarea, select');
      
      console.log(`📊 Found ${forms.length} forms and ${inputs.length} input fields`);
      
      if (inputs.length > 0) {
        // Test first input field
        await inputs[0].click();
        await inputs[0].type('test-value');
        console.log('✅ Form input interaction working');
        testResults.passed++;
      } else {
        console.log('⚠️ No form inputs found');
        testResults.issues.push('No form inputs found');
        testResults.failed++;
      }
      
      await page.screenshot({ path: 'puppeteer_04_forms.png' });
    } catch (error) {
      console.log(`❌ Form functionality test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Form functionality error: ${error.message}`);
    }
    
    // Test 5: Real-time Features (WebSocket/SSE)
    console.log('\n🔄 Test 5: Testing Real-time Features...');
    try {
      await page.goto(`${baseUrl}/audit`);
      await page.waitForSelector('body', { timeout: 5000 });
      
      // Look for progress indicators or real-time elements
      const realTimeElements = await page.$$('.progress, #progress, .real-time, .live-update');
      
      if (realTimeElements.length > 0) {
        console.log(`✅ Found ${realTimeElements.length} real-time elements`);
        testResults.passed++;
      } else {
        console.log('⚠️ No real-time elements detected');
        testResults.issues.push('No real-time elements found');
      }
      
      await page.screenshot({ path: 'puppeteer_05_realtime.png' });
    } catch (error) {
      console.log(`❌ Real-time features test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Real-time features error: ${error.message}`);
    }
    
    // Test 6: Download Functionality
    console.log('\n💾 Test 6: Testing Download Functionality...');
    try {
      await page.goto(`${baseUrl}/reports`);
      await page.waitForSelector('body', { timeout: 5000 });
      
      const downloadLinks = await page.$$('a[href*="download"], a[href*=".pdf"], a[href*=".xlsx"], a[href*=".csv"]');
      
      if (downloadLinks.length > 0) {
        console.log(`✅ Found ${downloadLinks.length} download links`);
        testResults.passed++;
      } else {
        console.log('⚠️ No download links found');
        testResults.issues.push('No download links found');
        testResults.failed++;
      }
      
      await page.screenshot({ path: 'puppeteer_06_downloads.png' });
    } catch (error) {
      console.log(`❌ Download functionality test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Download functionality error: ${error.message}`);
    }
    
    // Test 7: Error Handling
    console.log('\n🚨 Test 7: Testing Error Handling...');
    try {
      // Test 404 page
      await page.goto(`${baseUrl}/nonexistent-page`);
      await page.waitForSelector('body', { timeout: 5000 });
      
      const pageContent = await page.content();
      if (pageContent.includes('404') || pageContent.includes('Not Found') || pageContent.includes('Error')) {
        console.log('✅ Error handling working (404 page detected)');
        testResults.passed++;
      } else {
        console.log('⚠️ No proper error handling detected');
        testResults.issues.push('No proper error handling');
        testResults.failed++;
      }
      
      await page.screenshot({ path: 'puppeteer_07_error.png' });
    } catch (error) {
      console.log(`❌ Error handling test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Error handling test error: ${error.message}`);
    }
    
    // Test 8: Search Functionality
    console.log('\n🔍 Test 8: Testing Search Functionality...');
    try {
      await page.goto(baseUrl);
      await page.waitForSelector('body', { timeout: 5000 });
      
      const searchElements = await page.$$('input[type="search"], .search-box, #search, [placeholder*="search" i]');
      
      if (searchElements.length > 0) {
        console.log(`✅ Found ${searchElements.length} search elements`);
        // Test search input
        await searchElements[0].type('router');
        await page.keyboard.press('Enter');
        testResults.passed++;
      } else {
        console.log('⚠️ No search functionality found');
        testResults.issues.push('No search functionality');
      }
      
      await page.screenshot({ path: 'puppeteer_08_search.png' });
    } catch (error) {
      console.log(`❌ Search functionality test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Search functionality error: ${error.message}`);
    }
    
    // Test 9: Device Monitoring
    console.log('\n📡 Test 9: Testing Device Status Monitoring...');
    try {
      const response = await page.goto(`${baseUrl}/device_status`);
      
      if (response.ok()) {
        const content = await page.content();
        if (content.includes('device') || content.includes('status') || content.includes('router')) {
          console.log('✅ Device status monitoring endpoint working');
          testResults.passed++;
        } else {
          console.log('⚠️ Device status endpoint empty or invalid');
          testResults.issues.push('Device status endpoint invalid');
          testResults.failed++;
        }
      } else {
        console.log('⚠️ Device status endpoint not accessible');
        testResults.issues.push('Device status endpoint not accessible');
        testResults.failed++;
      }
      
      await page.screenshot({ path: 'puppeteer_09_device_status.png' });
    } catch (error) {
      console.log(`❌ Device monitoring test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Device monitoring error: ${error.message}`);
    }
    
    // Test 10: Security Headers
    console.log('\n🔒 Test 10: Testing Security Headers...');
    try {
      const response = await page.goto(baseUrl);
      const headers = response.headers();
      
      const securityHeaders = ['x-frame-options', 'x-content-type-options', 'content-security-policy'];
      let securityScore = 0;
      
      securityHeaders.forEach(header => {
        if (headers[header]) {
          console.log(`✅ Security header ${header} present`);
          securityScore++;
        } else {
          console.log(`⚠️ Security header ${header} missing`);
          testResults.issues.push(`Missing security header: ${header}`);
        }
      });
      
      if (securityScore >= 1) {
        testResults.passed++;
      } else {
        testResults.failed++;
      }
    } catch (error) {
      console.log(`❌ Security headers test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Security headers error: ${error.message}`);
    }
    
  } catch (error) {
    console.log(`❌ Critical test failure: ${error.message}`);
    testResults.failed++;
    testResults.issues.push(`Critical error: ${error.message}`);
  } finally {
    await browser.close();
  }
  
  // Test Results Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 PUPPETEER TEST RESULTS SUMMARY');
  console.log('='.repeat(50));
  console.log(`✅ Tests Passed: ${testResults.passed}`);
  console.log(`❌ Tests Failed: ${testResults.failed}`);
  console.log(`📈 Success Rate: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`);
  
  if (testResults.issues.length > 0) {
    console.log('\n🐛 Issues Found:');
    testResults.issues.forEach((issue, index) => {
      console.log(`   ${index + 1}. ${issue}`);
    });
  } else {
    console.log('\n🎉 No issues found! All tests passed.');
  }
  
  return testResults;
}

// Run the test
runPuppeteerUITest().catch(console.error); 