const puppeteer = require('puppeteer');

class NetAuditProTimingTester {
    constructor() {
        this.baseUrl = 'http://127.0.0.1:5011';
        this.issues = [];
        this.testResults = [];
    }

    async logTest(testName, status, details = '', issue = '') {
        const result = {
            test: testName,
            status: status,
            details: details,
            timestamp: new Date().toISOString()
        };
        this.testResults.push(result);
        
        if (status === 'FAIL' && issue) {
            this.issues.push({
                test: testName,
                issue: issue,
                details: details
            });
        }
        
        const statusIcon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⚠️';
        console.log(`${statusIcon} ${testName}: ${status}`);
        if (details) console.log(`   Details: ${details}`);
        if (issue) console.log(`   Issue: ${issue}`);
    }

    async testTimingDisplayElements(page) {
        console.log('🧪 Testing Timing Display Elements...');
        
        try {
            // Wait for page to load completely
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check for timing section using text content search
            const timingSections = await page.$$('h5');
            let timingSectionFound = false;
            for (let section of timingSections) {
                const text = await page.evaluate(el => el.textContent, section);
                if (text.includes('Audit Timing Information')) {
                    timingSectionFound = true;
                    break;
                }
            }
            
            if (!timingSectionFound) {
                await this.logTest('Timing Section Exists', 'FAIL', 
                    'Timing section not found', 'Missing Audit Timing Information section');
                return false;
            }

            // Check for start time element (correct ID)
            const startTimeElement = await page.$('#audit-start-time');
            if (!startTimeElement) {
                await this.logTest('Start Time Element', 'FAIL', 
                    'Start time element not found', 'Missing #audit-start-time element');
                return false;
            }

            // Get start time value
            const startTimeText = await page.evaluate(el => el.textContent, startTimeElement);
            console.log(`   📅 Start Time Display: ${startTimeText}`);

            // Check for elapsed time element (correct ID)
            const elapsedTimeElement = await page.$('#audit-elapsed-time');
            if (!elapsedTimeElement) {
                await this.logTest('Elapsed Time Element', 'FAIL', 
                    'Elapsed time element not found', 'Missing #audit-elapsed-time element');
                return false;
            }

            const elapsedTimeText = await page.evaluate(el => el.textContent, elapsedTimeElement);
            console.log(`   ⏱️ Elapsed Time Display: ${elapsedTimeText}`);

            // Check for completion time element (correct ID)
            const completionTimeElement = await page.$('#audit-completion-time');
            if (!completionTimeElement) {
                await this.logTest('Completion Time Element', 'WARN', 
                    'Completion time element not found', 'Missing #audit-completion-time element');
                // Don't return false as this might not exist until audit completes
            } else {
                const completionTimeText = await page.evaluate(el => el.textContent, completionTimeElement);
                console.log(`   🏁 Completion Time Display: ${completionTimeText}`);
            }

            await this.logTest('Timing Display Elements', 'PASS', 
                `Start: ${startTimeText}, Elapsed: ${elapsedTimeText}`);
            return true;

        } catch (error) {
            await this.logTest('Timing Display Elements', 'FAIL', 
                `Exception: ${error.message}`, 'Error accessing timing elements');
            return false;
        }
    }

    async testQuickStatsValues(page) {
        console.log('🧪 Testing Quick Stats Values...');
        
        try {
            // Wait for data to load and refresh the page data
            await new Promise(resolve => setTimeout(resolve, 1000));
            await page.reload({ waitUntil: 'networkidle2' });
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Get Quick Stats values using correct method
            const totalDevicesElement = await page.$('#total-devices-count');
            const successfulDevicesElement = await page.$('#successful-devices-count');
            const violationsElement = await page.$('#violations-count');

            if (!totalDevicesElement || !successfulDevicesElement || !violationsElement) {
                await this.logTest('Quick Stats Elements', 'FAIL', 
                    'Missing Quick Stats elements', 'Quick Stats elements not found');
                return false;
            }

            const totalDevices = await page.evaluate(el => el.textContent, totalDevicesElement);
            const successfulDevices = await page.evaluate(el => el.textContent, successfulDevicesElement);
            const violations = await page.evaluate(el => el.textContent, violationsElement);

            console.log(`   📊 Quick Stats: Total=${totalDevices}, Successful=${successfulDevices}, Violations=${violations}`);

            // Validate expected values based on the API data we confirmed
            if (totalDevices !== '6') {
                await this.logTest('Total Devices Count', 'FAIL', 
                    `Expected 6, got ${totalDevices}`, 'Incorrect total devices count');
                return false;
            }

            if (successfulDevices !== '2') {
                await this.logTest('Successful Devices Count', 'FAIL', 
                    `Expected 2, got ${successfulDevices}`, 'Incorrect successful devices count');
                return false;
            }

            if (violations !== '0') {
                await this.logTest('Violations Count', 'FAIL', 
                    `Expected 0, got ${violations}`, 'Incorrect violations count');
                return false;
            }

            await this.logTest('Quick Stats Values', 'PASS', 
                `All values correct: Total=6, Successful=2, Violations=0`);
            return true;

        } catch (error) {
            await this.logTest('Quick Stats Values', 'FAIL', 
                `Exception: ${error.message}`, 'Error accessing Quick Stats values');
            return false;
        }
    }

    async testAuditStatusDisplay(page) {
        console.log('🧪 Testing Audit Status Display...');
        
        try {
            // Wait for page to load completely
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Check current device (this should exist)
            const currentDeviceElement = await page.$('#current-device');
            if (!currentDeviceElement) {
                await this.logTest('Current Device Element', 'FAIL', 
                    'Current device element not found', 'Missing #current-device element');
                return false;
            }

            const currentDeviceText = await page.evaluate(el => el.textContent, currentDeviceElement);
            console.log(`   🖥️ Current Device: ${currentDeviceText}`);

            // Check for progress percentage in progress bar
            const progressBar = await page.$('.progress-bar');
            if (!progressBar) {
                await this.logTest('Progress Bar Element', 'FAIL', 
                    'Progress bar element not found', 'Missing .progress-bar element');
                return false;
            }

            const progressText = await page.evaluate(el => el.textContent, progressBar);
            console.log(`   📈 Progress: ${progressText}`);

            // Validate expected values based on API data
            if (currentDeviceText.trim() !== 'Audit Complete') {
                await this.logTest('Current Device Status', 'FAIL', 
                    `Expected 'Audit Complete', got '${currentDeviceText}'`, 'Incorrect current device status');
                return false;
            }

            if (!progressText.includes('100.0%')) {
                await this.logTest('Progress Percentage', 'FAIL', 
                    `Expected '100.0%', got '${progressText}'`, 'Incorrect progress percentage');
                return false;
            }

            await this.logTest('Audit Status Display', 'PASS', 
                `Progress: ${progressText}, Device: ${currentDeviceText}`);
            return true;

        } catch (error) {
            await this.logTest('Audit Status Display', 'FAIL', 
                `Exception: ${error.message}`, 'Error accessing audit status elements');
            return false;
        }
    }

    async testTimingConsistency(page) {
        console.log('🧪 Testing Timing Consistency...');
        
        try {
            // Get timing values from UI using correct selectors
            const startTimeElement = await page.$('#audit-start-time');
            const elapsedTimeElement = await page.$('#audit-elapsed-time');

            const startTimeText = await page.evaluate(el => el.textContent, startTimeElement);
            const elapsedTimeText = await page.evaluate(el => el.textContent, elapsedTimeElement);

            console.log(`   🕐 UI Start Time: ${startTimeText}`);
            console.log(`   ⏱️ UI Elapsed Time: ${elapsedTimeText}`);

            // Check for timing API endpoint
            const response = await page.evaluate(async () => {
                try {
                    const res = await fetch('/api/timing');
                    return await res.json();
                } catch (error) {
                    return { error: error.message };
                }
            });

            if (response.error) {
                await this.logTest('Timing API Access', 'FAIL', 
                    `API error: ${response.error}`, 'Cannot access timing API');
                return false;
            }

            console.log(`   🔍 API Response:`, JSON.stringify(response, null, 2));

            // Check for timing discrepancies
            const issues = [];
            
            // Check if start time shows "Not Started" when it should show actual time
            if (startTimeText.trim() === 'Not Started' && response.timing && response.timing.start_time) {
                issues.push(`Start time shows 'Not Started' but API has start_time: ${response.timing.start_time}`);
            }

            // Check elapsed time format (assuming format like "00:01:21")
            const uiElapsedTime = elapsedTimeText.trim();
            if (!uiElapsedTime.match(/\d{2}:\d{2}:\d{2}/)) {
                issues.push(`Invalid elapsed time format: ${uiElapsedTime}`);
            }

            if (issues.length > 0) {
                await this.logTest('Timing Format Validation', 'WARN', 
                    issues.join(', '), 'Timing display issues detected');
            } else {
                await this.logTest('Timing Consistency', 'PASS', 
                    'Timing formats are valid');
            }
            return true;

        } catch (error) {
            await this.logTest('Timing Consistency', 'FAIL', 
                `Exception: ${error.message}`, 'Error checking timing consistency');
            return false;
        }
    }

    async testLogTimestamps(page) {
        console.log('🧪 Testing Log Timestamps...');
        
        try {
            // Get live logs from API since the element might not be visible
            const response = await page.evaluate(async () => {
                try {
                    const res = await fetch('/api/live-logs');
                    return await res.json();
                } catch (error) {
                    return { error: error.message };
                }
            });

            if (response.error) {
                await this.logTest('Live Logs API', 'FAIL', 
                    `API error: ${response.error}`, 'Cannot access live logs API');
                return false;
            }

            const liveLogsText = response.logs ? response.logs.join('\n') : '';
            console.log(`   📝 Live Logs Sample: ${liveLogsText.substring(0, 200)}...`);

            // Extract timestamps from logs
            const timestampRegex = /\[(\d{2}:\d{2}:\d{2})\]/g;
            const timestamps = [];
            let match;
            while ((match = timestampRegex.exec(liveLogsText)) !== null) {
                timestamps.push(match[1]);
            }

            if (timestamps.length === 0) {
                await this.logTest('Log Timestamps', 'FAIL', 
                    'No timestamps found in logs', 'Missing timestamps in log entries');
                return false;
            }

            console.log(`   🕐 Found ${timestamps.length} timestamps in logs`);
            console.log(`   🕐 First timestamp: ${timestamps[0]}`);
            console.log(`   🕐 Last timestamp: ${timestamps[timestamps.length - 1]}`);

            // Get UI start time to compare
            const uiResponse = await page.evaluate(async () => {
                try {
                    const res = await fetch('/api/timing');
                    return await res.json();
                } catch (error) {
                    return { error: error.message };
                }
            });

            if (uiResponse.timing && uiResponse.timing.start_time) {
                const uiStartTime = uiResponse.timing.start_time;
                const logStartHour = parseInt(timestamps[0].split(':')[0]);
                const uiStartHour = parseInt(uiStartTime.split(':')[0]);
                
                console.log(`   🕐 UI Start Time: ${uiStartTime} (hour: ${uiStartHour})`);
                console.log(`   🕐 Log Start Time: ${timestamps[0]} (hour: ${logStartHour})`);
                
                if (Math.abs(logStartHour - uiStartHour) > 1) {
                    await this.logTest('Timing Discrepancy Detection', 'WARN', 
                        `UI shows hour ${uiStartHour} but logs show hour ${logStartHour}`, 
                        'Potential timezone or timing display issue');
                } else {
                    await this.logTest('Log Timestamps', 'PASS', 
                        `Found ${timestamps.length} valid timestamps, timing consistent`);
                }
            } else {
                await this.logTest('Log Timestamps', 'PASS', 
                    `Found ${timestamps.length} valid timestamps`);
            }

            return true;

        } catch (error) {
            await this.logTest('Log Timestamps', 'FAIL', 
                `Exception: ${error.message}`, 'Error checking log timestamps');
            return false;
        }
    }

    async testAPIEndpoints(page) {
        console.log('🧪 Testing API Endpoints...');
        
        try {
            const endpoints = [
                '/api/progress',
                '/api/timing',
                '/api/live-logs',
                '/api/raw-logs'
            ];

            for (const endpoint of endpoints) {
                const response = await page.evaluate(async (url) => {
                    try {
                        const res = await fetch(url);
                        const data = await res.json();
                        return { status: res.status, data: data };
                    } catch (error) {
                        return { error: error.message };
                    }
                }, endpoint);

                if (response.error) {
                    await this.logTest(`API ${endpoint}`, 'FAIL', 
                        `Error: ${response.error}`, `API endpoint ${endpoint} failed`);
                } else if (response.status !== 200) {
                    await this.logTest(`API ${endpoint}`, 'FAIL', 
                        `Status: ${response.status}`, `API endpoint ${endpoint} returned non-200 status`);
                } else {
                    await this.logTest(`API ${endpoint}`, 'PASS', 
                        `Status: ${response.status}`);
                    
                    // Log specific data for timing endpoint
                    if (endpoint === '/api/timing') {
                        console.log(`   🔍 Timing API Data:`, JSON.stringify(response.data, null, 2));
                    }
                }
            }

            return true;

        } catch (error) {
            await this.logTest('API Endpoints', 'FAIL', 
                `Exception: ${error.message}`, 'Error testing API endpoints');
            return false;
        }
    }

    async runComprehensiveTest() {
        console.log('🎭 Starting Comprehensive NetAuditPro Timing Test...');
        console.log('='.repeat(60));

        const browser = await puppeteer.launch({ 
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        try {
            const page = await browser.newPage();
            await page.goto(this.baseUrl, { waitUntil: 'networkidle2' });

            // Run all tests
            await this.testTimingDisplayElements(page);
            await this.testQuickStatsValues(page);
            await this.testAuditStatusDisplay(page);
            await this.testTimingConsistency(page);
            await this.testLogTimestamps(page);
            await this.testAPIEndpoints(page);

            // Generate summary
            this.generateSummary();

        } catch (error) {
            console.error('❌ Test execution failed:', error);
            await this.logTest('Test Execution', 'FAIL', 
                `Exception: ${error.message}`, 'Test execution failed');
        } finally {
            await browser.close();
        }

        return this.issues.length === 0;
    }

    generateSummary() {
        console.log('\n' + '='.repeat(60));
        console.log('🎭 PUPPETEER TIMING TEST SUMMARY');
        console.log('='.repeat(60));

        const total = this.testResults.length;
        const passed = this.testResults.filter(r => r.status === 'PASS').length;
        const failed = this.testResults.filter(r => r.status === 'FAIL').length;
        const warnings = this.testResults.filter(r => r.status === 'WARN').length;

        console.log(`📊 Test Results:`);
        console.log(`   • Total Tests: ${total}`);
        console.log(`   • Passed: ${passed} ✅`);
        console.log(`   • Failed: ${failed} ❌`);
        console.log(`   • Warnings: ${warnings} ⚠️`);
        console.log(`   • Success Rate: ${((passed/total)*100).toFixed(1)}%`);

        if (this.issues.length > 0) {
            console.log(`\n🔧 Issues Found (${this.issues.length}):`);
            this.issues.forEach((issue, i) => {
                console.log(`   ${i+1}. ${issue.test}: ${issue.issue}`);
                if (issue.details) {
                    console.log(`      Details: ${issue.details}`);
                }
            });
        } else {
            console.log('\n🎉 No critical issues found!');
        }

        // Save results
        const fs = require('fs');
        fs.writeFileSync('puppeteer_timing_test_results.json', JSON.stringify({
            summary: {
                total_tests: total,
                passed: passed,
                failed: failed,
                warnings: warnings,
                success_rate: (passed/total)*100
            },
            test_results: this.testResults,
            issues_found: this.issues
        }, null, 2));

        console.log(`\n📄 Detailed results saved to: puppeteer_timing_test_results.json`);
    }
}

// Main execution
async function main() {
    const tester = new NetAuditProTimingTester();
    const success = await tester.runComprehensiveTest();
    
    if (success) {
        console.log('\n🎉 All timing tests passed successfully!');
        process.exit(0);
    } else {
        console.log(`\n⚠️ Found ${tester.issues.length} timing issues that need attention`);
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = NetAuditProTimingTester; 