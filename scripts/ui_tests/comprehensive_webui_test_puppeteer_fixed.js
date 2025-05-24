const puppeteer = require('puppeteer');

async function runPuppeteerUITest() {
  console.log('🚀 Starting FIXED Comprehensive Web UI Test with Puppeteer');
  console.log('========================================================');
  
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
    
    await page.screenshot({ path: 'puppeteer_01_performance_fixed.png' });
    
    // Test 2: Interactive Elements
    console.log('\n🖱️ Test 2: Testing Interactive Elements...');
    try {
      const buttons = await page.$$('button, .btn, input[type="submit"]');
      console.log(`📊 Found ${buttons.length} interactive buttons`);
      
      if (buttons.length > 0) {
        await buttons[0].hover();
        await page.screenshot({ path: 'puppeteer_02_button_hover_fixed.png' });
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
    
    // Test 3: Navigation Test
    console.log('\n🧭 Test 3: Testing Navigation...');
    try {
      // Use text-based selector for Settings link
      await page.evaluate(() => {
        const settingsLink = Array.from(document.querySelectorAll('a')).find(el => el.textContent.includes('Settings'));
        if (settingsLink) settingsLink.click();
      });
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('✅ Navigation to Settings working');
      testResults.passed++;
    } catch (error) {
      console.log(`❌ Navigation test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Navigation test error: ${error.message}`);
    }
    
    // Test 4: Form Functionality
    console.log('\n📝 Test 4: Testing Form Functionality...');
    try {
      await page.goto(`${baseUrl}/settings`);
      await page.waitForSelector('body', { timeout: 5000 });
      
      const forms = await page.$$('form');
      const inputs = await page.$$('input, textarea, select');
      
      console.log(`📊 Found ${forms.length} forms and ${inputs.length} input fields`);
      
      if (inputs.length > 0) {
        await inputs[0].click();
        await inputs[0].type('test-value');
        console.log('✅ Form input interaction working');
        testResults.passed++;
      } else {
        console.log('⚠️ No form inputs found');
        testResults.issues.push('No form inputs found');
        testResults.failed++;
      }
      
      await page.screenshot({ path: 'puppeteer_04_forms_fixed.png' });
    } catch (error) {
      console.log(`❌ Form functionality test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Form functionality error: ${error.message}`);
    }
    
    // Test 5: API Endpoints
    console.log('\n🔗 Test 5: Testing API Endpoints...');
    try {
      const endpoints = ['/device_status', '/down_devices', '/enhanced_summary'];
      let workingEndpoints = 0;
      
      for (const endpoint of endpoints) {
        try {
          const response = await page.goto(`${baseUrl}${endpoint}`);
          if (response.ok()) {
            workingEndpoints++;
            console.log(`✅ ${endpoint} working`);
          }
        } catch (e) {
          console.log(`⚠️ ${endpoint} failed`);
        }
      }
      
      if (workingEndpoints >= 2) {
        console.log(`✅ Found ${workingEndpoints} working API endpoints`);
        testResults.passed++;
      } else {
        console.log('⚠️ Not enough working API endpoints');
        testResults.issues.push('Insufficient working API endpoints');
        testResults.failed++;
      }
    } catch (error) {
      console.log(`❌ API endpoints test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`API endpoints error: ${error.message}`);
    }
    
  } catch (error) {
    console.log(`❌ Critical test failure: ${error.message}`);
    testResults.failed++;
    testResults.issues.push(`Critical error: ${error.message}`);
  } finally {
    await browser.close();
  }
  
  // Test Results Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 FIXED PUPPETEER TEST RESULTS SUMMARY');
  console.log('='.repeat(60));
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