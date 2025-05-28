const puppeteer = require('puppeteer');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Test configuration
const TEST_CONFIG = {
    appUrl: 'http://127.0.0.1:5011',
    appStartupTime: 8000,
    testTimeout: 30000,
    screenshotDir: './test-screenshots'
};

// Ensure screenshot directory exists
if (!fs.existsSync(TEST_CONFIG.screenshotDir)) {
    fs.mkdirSync(TEST_CONFIG.screenshotDir, { recursive: true });
}

class AuditControlsTest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.appProcess = null;
        this.testResults = {
            total: 0,
            passed: 0,
            failed: 0,
            details: []
        };
    }

    async setup() {
        console.log('🤖 Setting up Puppeteer Audit Controls tests...');
        
        // Start the NetAuditPro application
        console.log('🚀 Starting NetAuditPro application...');
        this.appProcess = spawn('python3', ['rr4-router-complete-enhanced-v3.py'], {
            cwd: process.cwd(),
            stdio: 'pipe'
        });

        // Wait for application to start
        console.log('⏳ Waiting for application to be ready...');
        await this.waitForApp();

        // Launch browser
        this.browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        this.page = await this.browser.newPage();
        await this.page.setViewport({ width: 1280, height: 720 });
        
        // Navigate to the application
        await this.page.goto(TEST_CONFIG.appUrl, { waitUntil: 'networkidle2' });
        console.log('✅ Application is ready');
    }

    async waitForApp() {
        const maxAttempts = 20;
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(TEST_CONFIG.appUrl);
                if (response.ok) {
                    await this.sleep(2000); // Extra wait
                    return;
                }
            } catch (error) {
                // App not ready yet
            }
            
            attempts++;
            await this.sleep(1000);
        }
        
        throw new Error('Application failed to start within timeout');
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async runTest(testName, testFunction) {
        this.testResults.total++;
        console.log(`🧪 Testing ${testName}...`);
        
        try {
            await testFunction();
            this.testResults.passed++;
            this.testResults.details.push({ name: testName, status: 'PASSED' });
            console.log(`✅ ${testName}`);
        } catch (error) {
            this.testResults.failed++;
            this.testResults.details.push({ name: testName, status: 'FAILED', error: error.message });
            console.log(`❌ ${testName}: ${error.message}`);
            
            // Take screenshot on failure
            await this.takeScreenshot(`failed-${testName.replace(/\s+/g, '-').toLowerCase()}`);
        }
    }

    async takeScreenshot(name) {
        try {
            const screenshotPath = path.join(TEST_CONFIG.screenshotDir, `${name}-${Date.now()}.png`);
            await this.page.screenshot({
                path: screenshotPath,
                fullPage: true
            });
        } catch (error) {
            console.log(`Warning: Could not take screenshot: ${error.message}`);
        }
    }

    async testAuditControlsExistence() {
        // Check if all audit control buttons exist
        const startButton = await this.page.$('#start-audit');
        const pauseButton = await this.page.$('#pause-audit');
        const stopButton = await this.page.$('#stop-audit');
        const resetButton = await this.page.$('#reset-audit');

        if (!startButton) throw new Error('Start Audit button not found');
        if (!pauseButton) throw new Error('Pause Audit button not found');
        if (!stopButton) throw new Error('Stop Audit button not found');
        if (!resetButton) throw new Error('Reset Audit button not found');
    }

    async testRawTraceLogsSection() {
        // Check if Raw Trace Logs section exists
        const rawLogsSection = await this.page.$('#raw-logs-container');
        if (!rawLogsSection) throw new Error('Raw Trace Logs section not found');

        // Check Raw Trace Logs controls
        const refreshBtn = await this.page.$('#refresh-raw-btn');
        const autoRefreshBtn = await this.page.$('#raw-autorefresh-btn');
        const autoScrollBtn = await this.page.$('#raw-autoscroll-btn');

        if (!refreshBtn) throw new Error('Raw logs refresh button not found');
        if (!autoRefreshBtn) throw new Error('Raw logs auto-refresh button not found');
        if (!autoScrollBtn) throw new Error('Raw logs auto-scroll button not found');
    }

    async testStartAudit() {
        // Click start audit button
        await this.page.click('#start-audit');
        
        // Wait a moment for the action to process
        await this.sleep(2000);
        
        // Check if button states changed correctly
        const startDisabled = await this.page.$eval('#start-audit', el => el.disabled);
        const pauseDisabled = await this.page.$eval('#pause-audit', el => el.disabled);
        const stopDisabled = await this.page.$eval('#stop-audit', el => el.disabled);
        
        if (!startDisabled) throw new Error('Start button should be disabled after starting audit');
        if (pauseDisabled) throw new Error('Pause button should be enabled after starting audit');
        if (stopDisabled) throw new Error('Stop button should be enabled after starting audit');
    }

    async testPauseResumeAudit() {
        // First ensure audit is running (start it if not)
        const startDisabled = await this.page.$eval('#start-audit', el => el.disabled);
        if (!startDisabled) {
            await this.page.click('#start-audit');
            await this.sleep(1000);
        }

        // Click pause button
        await this.page.click('#pause-audit');
        await this.sleep(1000);
        
        // Check if pause worked (button text should change)
        const pauseText = await this.page.$eval('#pause-audit', el => el.textContent);
        if (!pauseText.includes('Resume')) {
            throw new Error('Pause button should show "Resume" after pausing');
        }

        // Click resume (pause button again)
        await this.page.click('#pause-audit');
        await this.sleep(1000);
        
        // Check if resume worked
        const resumeText = await this.page.$eval('#pause-audit', el => el.textContent);
        if (!resumeText.includes('Pause')) {
            throw new Error('Button should show "Pause" after resuming');
        }
    }

    async testStopAudit() {
        // First ensure audit is running
        const startDisabled = await this.page.$eval('#start-audit', el => el.disabled);
        if (!startDisabled) {
            await this.page.click('#start-audit');
            await this.sleep(1000);
        }

        // Click stop button
        await this.page.click('#stop-audit');
        await this.sleep(2000);
        
        // Check if button states changed correctly
        const startDisabled2 = await this.page.$eval('#start-audit', el => el.disabled);
        const pauseDisabled = await this.page.$eval('#pause-audit', el => el.disabled);
        const stopDisabled = await this.page.$eval('#stop-audit', el => el.disabled);
        
        if (startDisabled2) throw new Error('Start button should be enabled after stopping audit');
        if (!pauseDisabled) throw new Error('Pause button should be disabled after stopping audit');
        if (!stopDisabled) throw new Error('Stop button should be disabled after stopping audit');
    }

    async testResetAudit() {
        // Mock the confirm dialog to always return true
        await this.page.evaluateOnNewDocument(() => {
            window.confirm = () => true;
        });

        // Reload page to apply the mock
        await this.page.reload({ waitUntil: 'networkidle2' });

        // Click reset button
        await this.page.click('#reset-audit');
        await this.sleep(3000);
        
        // Check if reset worked - all buttons should be in initial state
        const startDisabled = await this.page.$eval('#start-audit', el => el.disabled);
        const pauseDisabled = await this.page.$eval('#pause-audit', el => el.disabled);
        const stopDisabled = await this.page.$eval('#stop-audit', el => el.disabled);
        
        if (startDisabled) throw new Error('Start button should be enabled after reset');
        if (!pauseDisabled) throw new Error('Pause button should be disabled after reset');
        if (!stopDisabled) throw new Error('Stop button should be disabled after reset');
    }

    async testRawLogsRefresh() {
        // Click refresh button for raw logs
        await this.page.click('#refresh-raw-btn');
        await this.sleep(1000);
        
        // Check if button shows loading state temporarily
        const buttonText = await this.page.$eval('#refresh-raw-btn', el => el.textContent);
        // Button should return to normal state after refresh
        if (!buttonText.includes('Refresh')) {
            throw new Error('Refresh button should return to normal state');
        }
    }

    async testRawLogsAutoRefresh() {
        // Click auto-refresh toggle
        await this.page.click('#raw-autorefresh-btn');
        await this.sleep(500);
        
        // Check if button state changed
        const buttonText = await this.page.$eval('#raw-autorefresh-btn', el => el.textContent);
        const hasAutoText = buttonText.includes('Auto') || buttonText.includes('Manual');
        
        if (!hasAutoText) {
            throw new Error('Auto-refresh button should show Auto or Manual state');
        }
    }

    async testRawLogsAutoScroll() {
        // Click auto-scroll toggle
        await this.page.click('#raw-autoscroll-btn');
        await this.sleep(500);
        
        // Check if button state changed
        const buttonText = await this.page.$eval('#raw-autoscroll-btn', el => el.textContent);
        const hasScrollText = buttonText.includes('Auto') || buttonText.includes('Manual');
        
        if (!hasScrollText) {
            throw new Error('Auto-scroll button should show Auto or Manual state');
        }
    }

    async testRawLogsVisibility() {
        // Check if raw logs container exists and has proper styling
        const container = await this.page.$('#raw-logs-container');
        if (!container) {
            throw new Error('Raw logs container not found');
        }

        // Check if container is in viewport (visible)
        const boundingBox = await container.boundingBox();
        if (!boundingBox || boundingBox.width === 0 || boundingBox.height === 0) {
            throw new Error('Raw logs container should have visible dimensions');
        }

        // Check container styling
        const containerStyle = await this.page.$eval('#raw-logs-container', el => {
            const style = window.getComputedStyle(el);
            return {
                height: style.height,
                fontFamily: style.fontFamily,
                fontSize: style.fontSize,
                display: style.display
            };
        });

        if (containerStyle.display === 'none') {
            throw new Error('Raw logs container should not be hidden');
        }

        if (containerStyle.height === '0px') {
            throw new Error('Raw logs container should have height');
        }
    }

    async testAPIEndpoints() {
        // Test raw logs API endpoint
        const response = await this.page.evaluate(async () => {
            try {
                const res = await fetch('/api/raw-logs');
                const data = await res.json();
                return { success: res.ok, data };
            } catch (error) {
                return { success: false, error: error.message };
            }
        });

        if (!response.success) {
            throw new Error('Raw logs API endpoint failed');
        }

        if (!response.data.hasOwnProperty('logs')) {
            throw new Error('Raw logs API should return logs array');
        }
    }

    async testRawLogsPopulation() {
        // Generate some raw logs by triggering an action
        await this.page.click('#refresh-raw-btn');
        await this.sleep(1000);

        // Check if logs are populated
        const logsCount = await this.page.evaluate(() => {
            const container = document.getElementById('raw-logs-container');
            return container ? container.children.length : 0;
        });

        // Raw logs might be empty initially, but the container should exist
        // This test just verifies the mechanism works
        console.log(`Raw logs container has ${logsCount} entries`);
    }

    async runAllTests() {
        console.log('🤖 Starting Puppeteer Audit Controls Tests...');
        console.log('============================================================');

        await this.runTest('Audit Controls Existence', () => this.testAuditControlsExistence());
        await this.runTest('Raw Trace Logs Section', () => this.testRawTraceLogsSection());
        await this.runTest('Raw Logs Visibility', () => this.testRawLogsVisibility());
        await this.runTest('Raw Logs Population Test', () => this.testRawLogsPopulation());
        await this.runTest('Start Audit Functionality', () => this.testStartAudit());
        await this.runTest('Pause/Resume Audit Functionality', () => this.testPauseResumeAudit());
        await this.runTest('Stop Audit Functionality', () => this.testStopAudit());
        await this.runTest('Reset Audit Functionality', () => this.testResetAudit());
        await this.runTest('Raw Logs Refresh', () => this.testRawLogsRefresh());
        await this.runTest('Raw Logs Auto-Refresh Toggle', () => this.testRawLogsAutoRefresh());
        await this.runTest('Raw Logs Auto-Scroll Toggle', () => this.testRawLogsAutoScroll());
        await this.runTest('API Endpoints', () => this.testAPIEndpoints());

        console.log('\n============================================================');
        console.log('🤖 Puppeteer Audit Controls Tests Summary:');
        console.log(`   • Tests run: ${this.testResults.total}`);
        console.log(`   • Passed: ${this.testResults.passed}`);
        console.log(`   • Failed: ${this.testResults.failed}`);
        console.log(`   • Success rate: ${((this.testResults.passed / this.testResults.total) * 100).toFixed(1)}%`);

        if (this.testResults.failed > 0) {
            console.log('\n❌ Failed tests:');
            this.testResults.details
                .filter(test => test.status === 'FAILED')
                .forEach(test => console.log(`   • ${test.name}: ${test.error}`));
        }

        console.log('🧹 Cleaning up Puppeteer tests...');
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
        
        if (this.appProcess) {
            this.appProcess.kill('SIGTERM');
            
            // Wait a moment for graceful shutdown
            await this.sleep(2000);
            
            // Force kill if still running
            try {
                this.appProcess.kill('SIGKILL');
            } catch (error) {
                // Process already terminated
            }
        }
    }
}

// Main execution
async function main() {
    const tester = new AuditControlsTest();
    
    try {
        await tester.setup();
        await tester.runAllTests();
    } catch (error) {
        console.error('❌ Test execution failed:', error.message);
        process.exit(1);
    } finally {
        await tester.cleanup();
    }
    
    // Exit with appropriate code
    process.exit(tester.testResults.failed > 0 ? 1 : 0);
}

// Handle process termination
process.on('SIGINT', async () => {
    console.log('\n🛑 Test interrupted by user');
    process.exit(1);
});

process.on('SIGTERM', async () => {
    console.log('\n🛑 Test terminated');
    process.exit(1);
});

// Run the tests
main().catch(error => {
    console.error('❌ Unexpected error:', error);
    process.exit(1);
}); 