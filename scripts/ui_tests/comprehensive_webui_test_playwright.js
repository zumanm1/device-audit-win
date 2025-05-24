const { chromium } = require('playwright');

async function runComprehensiveUITest() {
  console.log('🚀 Starting Comprehensive Web UI Test with Playwright');
  console.log('====================================================');
  
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const baseUrl = 'http://localhost:5010';
  const testResults = {
    passed: 0,
    failed: 0,
    issues: []
  };
  
  try {
    // Test 1: Home Page Loading
    console.log('\n📄 Test 1: Loading Home Page...');
    await page.goto(baseUrl);
    await page.waitForLoadState('networkidle');
    
    const title = await page.title();
    console.log(`✅ Page title: ${title}`);
    
    if (title.includes('Router Audit')) {
      testResults.passed++;
      console.log('✅ Home page loaded successfully');
    } else {
      testResults.failed++;
      testResults.issues.push('Home page title incorrect');
      console.log('❌ Home page title issue');
    }
    
    await page.screenshot({ path: 'test_01_homepage.png' });
    
    // Test 2: Navigation Menu
    console.log('\n🧭 Test 2: Testing Navigation Menu...');
    const navLinks = await page.locator('nav a, .nav a, .navbar a').count();
    console.log(`📊 Found ${navLinks} navigation links`);
    
    // Test main navigation items
    const expectedNavItems = ['Home', 'Audit', 'Inventory', 'Reports', 'Terminal'];
    let navTestsPassed = 0;
    
    for (const item of expectedNavItems) {
      try {
        const navItem = page.locator(`text="${item}"`).first();
        if (await navItem.isVisible()) {
          console.log(`✅ Navigation item "${item}" found`);
          navTestsPassed++;
        } else {
          console.log(`⚠️ Navigation item "${item}" not visible`);
        }
      } catch (error) {
        console.log(`❌ Navigation item "${item}" not found`);
        testResults.issues.push(`Navigation item "${item}" missing`);
      }
    }
    
    if (navTestsPassed >= 3) {
      testResults.passed++;
    } else {
      testResults.failed++;
    }
    
    // Test 3: Inventory Page
    console.log('\n📋 Test 3: Testing Inventory Management...');
    try {
      await page.click('text="Inventory"');
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'test_03_inventory.png' });
      
      // Check for inventory table or form
      const inventoryElements = await page.locator('table, form, .inventory').count();
      if (inventoryElements > 0) {
        console.log('✅ Inventory page loaded with content');
        testResults.passed++;
      } else {
        console.log('⚠️ Inventory page loaded but no content detected');
        testResults.issues.push('Inventory page missing content elements');
        testResults.failed++;
      }
    } catch (error) {
      console.log(`❌ Inventory page test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Inventory page error: ${error.message}`);
    }
    
    // Test 4: Audit Page
    console.log('\n🔍 Test 4: Testing Audit Functionality...');
    try {
      await page.click('text="Audit"');
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'test_04_audit.png' });
      
      // Look for audit controls
      const auditControls = await page.locator('button, input[type="submit"], .btn').count();
      if (auditControls > 0) {
        console.log(`✅ Audit page loaded with ${auditControls} controls`);
        testResults.passed++;
      } else {
        console.log('⚠️ Audit page missing interactive controls');
        testResults.issues.push('Audit page missing controls');
        testResults.failed++;
      }
    } catch (error) {
      console.log(`❌ Audit page test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Audit page error: ${error.message}`);
    }
    
    // Test 5: Reports Page
    console.log('\n📊 Test 5: Testing Reports Page...');
    try {
      await page.click('text="Reports"');
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'test_05_reports.png' });
      
      // Look for reports or download links
      const reportElements = await page.locator('a[href*="download"], .report, table').count();
      if (reportElements > 0) {
        console.log('✅ Reports page loaded with content');
        testResults.passed++;
      } else {
        console.log('⚠️ Reports page missing content');
        testResults.issues.push('Reports page missing content');
        testResults.failed++;
      }
    } catch (error) {
      console.log(`❌ Reports page test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Reports page error: ${error.message}`);
    }
    
    // Test 6: Terminal Page
    console.log('\n💻 Test 6: Testing Terminal Page...');
    try {
      await page.click('text="Terminal"');
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'test_06_terminal.png' });
      
      // Look for terminal interface
      const terminalElements = await page.locator('textarea, input, .terminal, .console').count();
      if (terminalElements > 0) {
        console.log('✅ Terminal page loaded with interface elements');
        testResults.passed++;
      } else {
        console.log('⚠️ Terminal page missing interface elements');
        testResults.issues.push('Terminal page missing interface');
        testResults.failed++;
      }
    } catch (error) {
      console.log(`❌ Terminal page test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Terminal page error: ${error.message}`);
    }
    
    // Test 7: API Endpoints
    console.log('\n🔗 Test 7: Testing API Endpoints...');
    const apiEndpoints = [
      '/device_status',
      '/down_devices',
      '/enhanced_summary',
      '/api/inventory',
      '/api/status'
    ];
    
    for (const endpoint of apiEndpoints) {
      try {
        const response = await page.request.get(`${baseUrl}${endpoint}`);
        if (response.ok()) {
          console.log(`✅ API endpoint ${endpoint} responding`);
        } else {
          console.log(`⚠️ API endpoint ${endpoint} returned ${response.status()}`);
          testResults.issues.push(`API endpoint ${endpoint} status ${response.status()}`);
        }
      } catch (error) {
        console.log(`❌ API endpoint ${endpoint} failed: ${error.message}`);
        testResults.issues.push(`API endpoint ${endpoint} error: ${error.message}`);
      }
    }
    
    // Test 8: JavaScript Console Errors
    console.log('\n🐛 Test 8: Checking for JavaScript Errors...');
    const consoleErrors = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    if (consoleErrors.length === 0) {
      console.log('✅ No JavaScript console errors detected');
      testResults.passed++;
    } else {
      console.log(`❌ Found ${consoleErrors.length} JavaScript errors:`);
      consoleErrors.forEach(error => console.log(`   - ${error}`));
      testResults.failed++;
      testResults.issues.push(`JavaScript errors: ${consoleErrors.join(', ')}`);
    }
    
    // Test 9: Form Validation
    console.log('\n📝 Test 9: Testing Form Validation...');
    try {
      await page.goto(`${baseUrl}/inventory`);
      await page.waitForLoadState('networkidle');
      
      // Look for forms and test basic interaction
      const forms = await page.locator('form').count();
      if (forms > 0) {
        console.log(`✅ Found ${forms} forms on inventory page`);
        testResults.passed++;
      } else {
        console.log('⚠️ No forms found for testing');
        testResults.issues.push('No forms found for validation testing');
      }
    } catch (error) {
      console.log(`❌ Form validation test failed: ${error.message}`);
      testResults.failed++;
      testResults.issues.push(`Form validation error: ${error.message}`);
    }
    
    // Test 10: Mobile Responsiveness
    console.log('\n📱 Test 10: Testing Mobile Responsiveness...');
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size
    await page.goto(baseUrl);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test_10_mobile.png' });
    
    // Check if navigation is mobile-friendly
    const mobileNav = await page.locator('.navbar-toggler, .mobile-menu, .hamburger').count();
    if (mobileNav > 0) {
      console.log('✅ Mobile navigation elements detected');
      testResults.passed++;
    } else {
      console.log('⚠️ No mobile navigation elements found');
      testResults.issues.push('Missing mobile navigation elements');
      testResults.failed++;
    }
    
    // Reset viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
  } catch (error) {
    console.log(`❌ Critical test failure: ${error.message}`);
    testResults.failed++;
    testResults.issues.push(`Critical error: ${error.message}`);
  } finally {
    await browser.close();
  }
  
  // Test Results Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 PLAYWRIGHT TEST RESULTS SUMMARY');
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
runComprehensiveUITest().catch(console.error); 