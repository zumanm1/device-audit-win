#!/usr/bin/env node
/**
 * Puppeteer Tests for Quick Stats UI Functionality
 * Tests the visual rendering and behavior of the Quick Stats section
 */

const puppeteer = require('puppeteer');
const { spawn } = require('child_process');
const path = require('path');

class QuickStatsPuppeteerTest {
    constructor() {
        this.browser = null;
        this.page = null;
        this.appProcess = null;
        this.baseUrl = 'http://127.0.0.1:5011';
    }

    async setup() {
        console.log('🤖 Setting up Puppeteer tests...');
        
        // Start the application
        await this.startApplication();
        
        // Launch browser
        this.browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        this.page = await this.browser.newPage();
        await this.page.setViewport({ width: 1280, height: 720 });
        
        // Wait for application to be ready
        await this.waitForApplication();
    }

    async startApplication() {
        console.log('🚀 Starting NetAuditPro application...');
        
        this.appProcess = spawn('python3', ['rr4-router-complete-enhanced-v3.py'], {
            cwd: process.cwd(),
            stdio: 'pipe'
        });
        
        // Give application time to start
        await this.sleep(5000);
    }

    async waitForApplication() {
        console.log('⏳ Waiting for application to be ready...');
        
        const maxAttempts = 30;
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                const response = await this.page.goto(this.baseUrl, { 
                    timeout: 5000,
                    waitUntil: 'networkidle0'
                });
                
                if (response && response.status() === 200) {
                    console.log('✅ Application is ready');
                    return;
                }
            } catch (error) {
                if (attempt < maxAttempts - 1) {
                    await this.sleep(1000);
                } else {
                    throw new Error(`Application failed to start: ${error.message}`);
                }
            }
        }
    }

    async testQuickStatsSectionExists() {
        console.log('🧪 Testing Quick Stats section existence...');
        
        await this.page.goto(this.baseUrl);
        
        // Check if Quick Stats card exists using evaluate
        const quickStatsExists = await this.page.evaluate(() => {
            const elements = Array.from(document.querySelectorAll('h5'));
            return elements.some(el => el.textContent.includes('Quick Stats'));
        });
        
        if (!quickStatsExists) {
            throw new Error('Quick Stats section not found');
        }
        
        console.log('✅ Quick Stats section exists');
    }

    async testQuickStatsThreeColumns() {
        console.log('🧪 Testing Quick Stats three-column layout...');
        
        await this.page.goto(this.baseUrl);
        
        // Find columns with col-4 class in Quick Stats area
        const columns = await this.page.evaluate(() => {
            // Find the Quick Stats card first
            const headings = Array.from(document.querySelectorAll('h5'));
            const quickStatsHeading = headings.find(h => h.textContent.includes('Quick Stats'));
            
            if (!quickStatsHeading) return [];
            
            // Find the parent card
            const card = quickStatsHeading.closest('.card');
            if (!card) return [];
            
            // Find col-4 elements within this card
            return Array.from(card.querySelectorAll('.col-4'));
        });
        
        if (columns.length !== 3) {
            throw new Error(`Expected 3 columns, found ${columns.length}`);
        }
        
        console.log('✅ Quick Stats has three columns');
    }

    async testQuickStatsColumnLabels() {
        console.log('🧪 Testing Quick Stats column labels...');
        
        await this.page.goto(this.baseUrl);
        
        const expectedLabels = ['Total Devices', 'Successful', 'Violations'];
        
        for (const label of expectedLabels) {
            const labelElement = await this.page.evaluate((labelText) => {
                const elements = Array.from(document.querySelectorAll('small'));
                return elements.find(el => el.textContent.includes(labelText));
            }, label);
            
            if (!labelElement) {
                throw new Error(`Label '${label}' not found`);
            }
        }
        
        console.log('✅ All Quick Stats labels are present');
    }

    async testQuickStatsValuesAreNumbers() {
        console.log('🧪 Testing Quick Stats numeric values...');
        
        await this.page.goto(this.baseUrl);
        
        const values = await this.page.evaluate(() => {
            // Find the Quick Stats card
            const headings = Array.from(document.querySelectorAll('h5'));
            const quickStatsHeading = headings.find(h => h.textContent.includes('Quick Stats'));
            
            if (!quickStatsHeading) return [];
            
            const card = quickStatsHeading.closest('.card');
            if (!card) return [];
            
            // Find all h4 elements (the values)
            const h4Elements = Array.from(card.querySelectorAll('h4'));
            return h4Elements.map(el => el.textContent.trim());
        });
        
        if (values.length !== 3) {
            throw new Error(`Expected 3 values, found ${values.length}`);
        }
        
        for (let i = 0; i < values.length; i++) {
            if (!/^\d+$/.test(values[i])) {
                throw new Error(`Value ${i + 1} is not numeric: ${values[i]}`);
            }
        }
        
        console.log('✅ All Quick Stats values are numeric');
    }

    async testQuickStatsColorCoding() {
        console.log('🧪 Testing Quick Stats color coding...');
        
        await this.page.goto(this.baseUrl);
        
        const colorClasses = await this.page.evaluate(() => {
            // Find the Quick Stats card
            const headings = Array.from(document.querySelectorAll('h5'));
            const quickStatsHeading = headings.find(h => h.textContent.includes('Quick Stats'));
            
            if (!quickStatsHeading) return [];
            
            const card = quickStatsHeading.closest('.card');
            if (!card) return [];
            
            // Find all h4 elements and get their classes
            const h4Elements = Array.from(card.querySelectorAll('h4'));
            return h4Elements.map(el => el.className);
        });
        
        const expectedClasses = ['text-primary', 'text-success', 'text-danger'];
        
        for (let i = 0; i < expectedClasses.length; i++) {
            if (!colorClasses[i] || !colorClasses[i].includes(expectedClasses[i])) {
                throw new Error(`Element ${i + 1} missing expected class ${expectedClasses[i]}`);
            }
        }
        
        console.log('✅ Quick Stats have correct color coding');
    }

    async testQuickStatsInitialValues() {
        console.log('🧪 Testing Quick Stats initial values...');
        
        await this.page.goto(this.baseUrl);
        
        const values = await this.page.evaluate(() => {
            // Find the Quick Stats card
            const headings = Array.from(document.querySelectorAll('h5'));
            const quickStatsHeading = headings.find(h => h.textContent.includes('Quick Stats'));
            
            if (!quickStatsHeading) return [];
            
            const card = quickStatsHeading.closest('.card');
            if (!card) return [];
            
            // Find all h4 elements (the values)
            const h4Elements = Array.from(card.querySelectorAll('h4'));
            return h4Elements.map(el => parseInt(el.textContent.trim()));
        });
        
        // Total Devices should be > 0 (from inventory)
        if (values[0] <= 0) {
            throw new Error(`Total Devices should be > 0, got ${values[0]}`);
        }
        
        // Successful should be 0 initially
        if (values[1] !== 0) {
            throw new Error(`Successful should be 0 initially, got ${values[1]}`);
        }
        
        // Violations should be 0 initially
        if (values[2] !== 0) {
            throw new Error(`Violations should be 0 initially, got ${values[2]}`);
        }
        
        console.log(`✅ Initial values: Total=${values[0]}, Successful=${values[1]}, Violations=${values[2]}`);
    }

    async testQuickStatsResponsiveLayout() {
        console.log('🧪 Testing Quick Stats responsive layout...');
        
        await this.page.goto(this.baseUrl);
        
        const viewports = [
            { width: 1920, height: 1080 }, // Desktop
            { width: 768, height: 1024 },  // Tablet
            { width: 375, height: 667 }    // Mobile
        ];
        
        for (const viewport of viewports) {
            await this.page.setViewport(viewport);
            await this.sleep(500); // Allow layout to adjust
            
            const quickStatsVisible = await this.page.evaluate(() => {
                const headings = Array.from(document.querySelectorAll('h5'));
                const quickStatsHeading = headings.find(h => h.textContent.includes('Quick Stats'));
                return quickStatsHeading !== null;
            });
            
            if (!quickStatsVisible) {
                throw new Error(`Quick Stats not visible at ${viewport.width}x${viewport.height}`);
            }
        }
        
        console.log('✅ Quick Stats responsive layout works');
    }

    async testQuickStatsAccessibility() {
        console.log('🧪 Testing Quick Stats accessibility...');
        
        await this.page.goto(this.baseUrl);
        
        // Check for proper heading structure
        const headingExists = await this.page.evaluate(() => {
            const headings = Array.from(document.querySelectorAll('h5'));
            return headings.some(h => h.textContent.includes('Quick Stats'));
        });
        
        if (!headingExists) {
            throw new Error('Quick Stats heading not found');
        }
        
        // Check for icon
        const iconExists = await this.page.evaluate(() => {
            const icons = Array.from(document.querySelectorAll('i.fas.fa-chart-bar'));
            return icons.length > 0;
        });
        
        if (!iconExists) {
            throw new Error('Quick Stats icon not found');
        }
        
        // Check for descriptive labels
        const requiredLabels = ['Total Devices', 'Successful', 'Violations'];
        const labelsFound = await this.page.evaluate((labels) => {
            const smallElements = Array.from(document.querySelectorAll('small'));
            const labelTexts = smallElements.map(el => el.textContent);
            
            return labels.every(label => 
                labelTexts.some(text => text.includes(label))
            );
        }, requiredLabels);
        
        if (!labelsFound) {
            throw new Error('Required accessibility labels not found');
        }
        
        console.log('✅ Quick Stats accessibility features present');
    }

    async cleanup() {
        console.log('🧹 Cleaning up Puppeteer tests...');
        
        if (this.page) {
            await this.page.close();
        }
        
        if (this.browser) {
            await this.browser.close();
        }
        
        // Stop application
        if (this.appProcess) {
            this.appProcess.kill();
        }
    }

    async runAllTests() {
        console.log('🤖 Starting Puppeteer Tests for Quick Stats...');
        console.log('='.repeat(60));
        
        const tests = [
            this.testQuickStatsSectionExists,
            this.testQuickStatsThreeColumns,
            this.testQuickStatsColumnLabels,
            this.testQuickStatsValuesAreNumbers,
            this.testQuickStatsColorCoding,
            this.testQuickStatsInitialValues,
            this.testQuickStatsResponsiveLayout,
            this.testQuickStatsAccessibility
        ];
        
        let passed = 0;
        let failed = 0;
        
        for (const test of tests) {
            try {
                await test.call(this);
                passed++;
            } catch (error) {
                console.log(`❌ ${test.name} failed: ${error.message}`);
                failed++;
            }
        }
        
        console.log('\n' + '='.repeat(60));
        console.log(`🤖 Puppeteer Tests Summary:`);
        console.log(`   • Tests run: ${tests.length}`);
        console.log(`   • Passed: ${passed}`);
        console.log(`   • Failed: ${failed}`);
        console.log(`   • Success rate: ${(passed / tests.length * 100).toFixed(1)}%`);
        
        return failed === 0;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

async function runPuppeteerTests() {
    const testRunner = new QuickStatsPuppeteerTest();
    
    try {
        await testRunner.setup();
        const success = await testRunner.runAllTests();
        return success;
    } catch (error) {
        console.log(`🚨 Puppeteer test setup failed: ${error.message}`);
        return false;
    } finally {
        await testRunner.cleanup();
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    runPuppeteerTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Test execution failed:', error);
            process.exit(1);
        });
}

module.exports = { QuickStatsPuppeteerTest, runPuppeteerTests }; 