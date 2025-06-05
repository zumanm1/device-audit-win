const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Test configuration
const TEST_CONFIG = {
    appUrl: 'http://127.0.0.1:5011',
    testTimeout: 120000, // 2 minutes for full audit
    screenshotDir: './audit-monitoring-screenshots',
    logFile: './audit-monitoring-log.txt'
};

// Ensure directories exist
if (!fs.existsSync(TEST_CONFIG.screenshotDir)) {
    fs.mkdirSync(TEST_CONFIG.screenshotDir, { recursive: true });
}

class AuditMonitor {
    constructor() {
        this.browser = null;
        this.page = null;
        this.auditData = {
            startTime: null,
            endTime: null,
            devicesProcessed: 0,
            devicesSuccessful: 0,
            devicesFailed: 0,
            violations: 0,
            rawLogs: [],
            auditStages: [],
            errors: []
        };
        this.logStream = fs.createWriteStream(TEST_CONFIG.logFile, { flags: 'w' });
    }

    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] ${message}`;
        console.log(logMessage);
        this.logStream.write(logMessage + '\n');
    }

    async setup() {
        this.log('🤖 Setting up Audit Monitoring...');
        
        this.browser = await puppeteer.launch({
            headless: false, // Run in visible mode to see what's happening
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security'],
            defaultViewport: { width: 1920, height: 1080 }
        });

        this.page = await this.browser.newPage();
        
        // Enable console logging from the page
        this.page.on('console', msg => {
            this.log(`PAGE CONSOLE: ${msg.text()}`);
        });

        // Enable network monitoring
        await this.page.setRequestInterception(true);
        this.page.on('request', request => {
            if (request.url().includes('/api/')) {
                this.log(`API REQUEST: ${request.method()} ${request.url()}`);
            }
            request.continue();
        });

        this.page.on('response', response => {
            if (response.url().includes('/api/')) {
                this.log(`API RESPONSE: ${response.status()} ${response.url()}`);
            }
        });

        await this.page.goto(TEST_CONFIG.appUrl, { waitUntil: 'networkidle2' });
        this.log('✅ Connected to NetAuditPro application');
        
        // Take initial screenshot
        await this.takeScreenshot('01-initial-state');
    }

    async takeScreenshot(name) {
        try {
            const screenshotPath = path.join(TEST_CONFIG.screenshotDir, `${name}-${Date.now()}.png`);
            await this.page.screenshot({
                path: screenshotPath,
                fullPage: true
            });
            this.log(`📸 Screenshot saved: ${screenshotPath}`);
        } catch (error) {
            this.log(`❌ Screenshot failed: ${error.message}`);
        }
    }

    async waitForElement(selector, timeout = 10000) {
        try {
            await this.page.waitForSelector(selector, { timeout });
            return true;
        } catch (error) {
            this.log(`❌ Element not found: ${selector}`);
            return false;
        }
    }

    async getQuickStats() {
        try {
            const stats = await this.page.evaluate(() => {
                const totalDevices = document.querySelector('#total-devices')?.textContent || '0';
                const successful = document.querySelector('#successful-devices')?.textContent || '0';
                const violations = document.querySelector('#violations-count')?.textContent || '0';
                
                return {
                    total: parseInt(totalDevices),
                    successful: parseInt(successful),
                    violations: parseInt(violations)
                };
            });
            
            this.log(`📊 Quick Stats - Total: ${stats.total}, Successful: ${stats.successful}, Violations: ${stats.violations}`);
            return stats;
        } catch (error) {
            this.log(`❌ Failed to get quick stats: ${error.message}`);
            return { total: 0, successful: 0, violations: 0 };
        }
    }

    async getRawLogs() {
        try {
            const logs = await this.page.evaluate(() => {
                const container = document.getElementById('raw-logs-container');
                if (!container) return [];
                
                const logEntries = Array.from(container.children).map(entry => entry.textContent);
                return logEntries;
            });
            
            this.log(`📝 Retrieved ${logs.length} raw log entries`);
            return logs;
        } catch (error) {
            this.log(`❌ Failed to get raw logs: ${error.message}`);
            return [];
        }
    }

    async getAuditProgress() {
        try {
            const progress = await this.page.evaluate(() => {
                const progressBar = document.querySelector('.progress-bar');
                const progressText = document.querySelector('#audit-progress-text');
                
                return {
                    percentage: progressBar ? progressBar.style.width : '0%',
                    text: progressText ? progressText.textContent : 'No progress info'
                };
            });
            
            this.log(`📈 Audit Progress: ${progress.percentage} - ${progress.text}`);
            return progress;
        } catch (error) {
            this.log(`❌ Failed to get audit progress: ${error.message}`);
            return { percentage: '0%', text: 'Unknown' };
        }
    }

    async startAudit() {
        this.log('🚀 Starting audit...');
        this.auditData.startTime = new Date();
        
        // Click start audit button
        await this.page.click('#start-audit');
        await this.takeScreenshot('02-audit-started');
        
        // Wait for audit to begin
        await this.page.waitForTimeout(2000);
        
        this.log('✅ Audit started successfully');
    }

    async monitorAuditProgress() {
        this.log('👀 Monitoring audit progress...');
        
        let previousStats = { total: 0, successful: 0, violations: 0 };
        let stableCount = 0;
        const maxStableChecks = 10; // If stats don't change for 10 checks, consider audit complete
        
        while (stableCount < maxStableChecks) {
            // Get current stats
            const currentStats = await this.getQuickStats();
            const progress = await this.getAuditProgress();
            const rawLogs = await this.getRawLogs();
            
            // Update audit data
            this.auditData.devicesProcessed = currentStats.total;
            this.auditData.devicesSuccessful = currentStats.successful;
            this.auditData.violations = currentStats.violations;
            this.auditData.rawLogs = rawLogs;
            
            // Check if stats changed
            if (JSON.stringify(currentStats) === JSON.stringify(previousStats)) {
                stableCount++;
                this.log(`⏳ Stats stable for ${stableCount}/${maxStableChecks} checks`);
            } else {
                stableCount = 0;
                this.log(`🔄 Stats changed - resetting stability counter`);
                await this.takeScreenshot(`03-progress-${Date.now()}`);
            }
            
            previousStats = currentStats;
            
            // Wait before next check
            await this.page.waitForTimeout(3000);
            
            // Check if audit completed by looking for completion indicators
            const isCompleted = await this.page.evaluate(() => {
                const startBtn = document.getElementById('start-audit');
                return startBtn && !startBtn.disabled;
            });
            
            if (isCompleted && currentStats.total > 0) {
                this.log('🎉 Audit appears to be completed');
                break;
            }
        }
        
        this.auditData.endTime = new Date();
        await this.takeScreenshot('04-audit-completed');
    }

    async analyzeResults() {
        this.log('🔍 Analyzing audit results...');
        
        const duration = this.auditData.endTime - this.auditData.startTime;
        const durationSeconds = Math.round(duration / 1000);
        
        this.log('============================================================');
        this.log('📊 AUDIT MONITORING RESULTS');
        this.log('============================================================');
        this.log(`⏱️  Duration: ${durationSeconds} seconds`);
        this.log(`📱 Total Devices: ${this.auditData.devicesProcessed}`);
        this.log(`✅ Successful: ${this.auditData.devicesSuccessful}`);
        this.log(`❌ Failed: ${this.auditData.devicesProcessed - this.auditData.devicesSuccessful}`);
        this.log(`🚨 Violations: ${this.auditData.violations}`);
        this.log(`📝 Raw Log Entries: ${this.auditData.rawLogs.length}`);
        
        // Check if all 6 devices were processed
        if (this.auditData.devicesProcessed !== 6) {
            this.log(`❌ ISSUE: Expected 6 devices, but only ${this.auditData.devicesProcessed} were processed`);
            this.auditData.errors.push(`Device count mismatch: expected 6, got ${this.auditData.devicesProcessed}`);
        } else {
            this.log(`✅ All 6 devices were processed as expected`);
        }
        
        // Analyze raw logs for issues
        const errorLogs = this.auditData.rawLogs.filter(log => 
            log.includes('ERROR') || log.includes('FAILED') || log.includes('❌')
        );
        
        if (errorLogs.length > 0) {
            this.log(`⚠️  Found ${errorLogs.length} error entries in raw logs:`);
            errorLogs.forEach((error, index) => {
                this.log(`   ${index + 1}. ${error}`);
            });
        }
        
        // Check for specific issues
        await this.checkForSpecificIssues();
        
        return this.auditData;
    }

    async checkForSpecificIssues() {
        this.log('🔍 Checking for specific issues...');
        
        // Check if Raw Trace Logs are visible and populated
        const rawLogsVisible = await this.page.evaluate(() => {
            const container = document.getElementById('raw-logs-container');
            if (!container) return false;
            
            const style = window.getComputedStyle(container);
            return style.display !== 'none' && style.visibility !== 'hidden';
        });
        
        if (!rawLogsVisible) {
            this.log('❌ ISSUE: Raw Trace Logs container is not visible');
            this.auditData.errors.push('Raw Trace Logs not visible');
        } else {
            this.log('✅ Raw Trace Logs container is visible');
        }
        
        // Check audit controls functionality
        const controlsWorking = await this.page.evaluate(() => {
            const startBtn = document.getElementById('start-audit');
            const pauseBtn = document.getElementById('pause-audit');
            const stopBtn = document.getElementById('stop-audit');
            const resetBtn = document.getElementById('reset-audit');
            
            return {
                startExists: !!startBtn,
                pauseExists: !!pauseBtn,
                stopExists: !!stopBtn,
                resetExists: !!resetBtn
            };
        });
        
        Object.entries(controlsWorking).forEach(([control, exists]) => {
            if (!exists) {
                this.log(`❌ ISSUE: ${control} button not found`);
                this.auditData.errors.push(`Missing ${control} button`);
            } else {
                this.log(`✅ ${control} button found`);
            }
        });
    }

    async generateReport() {
        const reportData = {
            timestamp: new Date().toISOString(),
            testDuration: this.auditData.endTime - this.auditData.startTime,
            auditData: this.auditData,
            recommendations: []
        };
        
        // Generate recommendations based on findings
        if (this.auditData.errors.length > 0) {
            reportData.recommendations.push('Fix identified errors in the audit process');
        }
        
        if (this.auditData.devicesProcessed !== 6) {
            reportData.recommendations.push('Investigate why not all 6 devices were processed');
        }
        
        if (this.auditData.devicesSuccessful === 0) {
            reportData.recommendations.push('Check network connectivity and device credentials');
        }
        
        // Save report
        const reportPath = './audit-monitoring-report.json';
        fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
        this.log(`📄 Report saved to: ${reportPath}`);
        
        return reportData;
    }

    async cleanup() {
        this.log('🧹 Cleaning up...');
        
        if (this.browser) {
            await this.browser.close();
        }
        
        if (this.logStream) {
            this.logStream.end();
        }
        
        this.log('✅ Cleanup completed');
    }
}

// Main execution
async function main() {
    const monitor = new AuditMonitor();
    
    try {
        await monitor.setup();
        await monitor.startAudit();
        await monitor.monitorAuditProgress();
        const results = await monitor.analyzeResults();
        const report = await monitor.generateReport();
        
        console.log('\n🎉 Monitoring completed successfully!');
        console.log(`📄 Check the report at: audit-monitoring-report.json`);
        console.log(`📝 Check the logs at: ${TEST_CONFIG.logFile}`);
        console.log(`📸 Check screenshots at: ${TEST_CONFIG.screenshotDir}/`);
        
        // Exit with error code if issues were found
        process.exit(results.errors.length > 0 ? 1 : 0);
        
    } catch (error) {
        console.error('❌ Monitoring failed:', error.message);
        await monitor.takeScreenshot('error-state');
        process.exit(1);
    } finally {
        await monitor.cleanup();
    }
}

// Handle process termination
process.on('SIGINT', async () => {
    console.log('\n🛑 Monitoring interrupted by user');
    process.exit(1);
});

// Run the monitoring
main().catch(error => {
    console.error('❌ Unexpected error:', error);
    process.exit(1);
}); 