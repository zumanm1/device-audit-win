import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('audit-monitoring-playwright.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlaywrightAuditMonitor:
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        self.audit_data = {
            'start_time': None,
            'end_time': None,
            'devices_processed': 0,
            'devices_successful': 0,
            'devices_failed': 0,
            'violations': 0,
            'raw_logs': [],
            'audit_stages': [],
            'errors': [],
            'screenshots': []
        }
        self.app_url = 'http://127.0.0.1:5011'
        self.screenshot_dir = Path('./audit-monitoring-playwright-screenshots')
        self.screenshot_dir.mkdir(exist_ok=True)

    async def setup(self):
        logger.info("🤖 Setting up Playwright Audit Monitoring...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Run in visible mode
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await self.context.new_page()
        
        # Enable console logging
        self.page.on('console', lambda msg: logger.info(f"PAGE CONSOLE: {msg.text}"))
        
        # Enable network monitoring
        self.page.on('request', self._log_request)
        self.page.on('response', self._log_response)
        
        await self.page.goto(self.app_url, wait_until='networkidle')
        logger.info("✅ Connected to NetAuditPro application")
        
        await self.take_screenshot('01-initial-state')

    def _log_request(self, request):
        if '/api/' in request.url:
            logger.info(f"API REQUEST: {request.method} {request.url}")

    def _log_response(self, response):
        if '/api/' in response.url:
            logger.info(f"API RESPONSE: {response.status} {response.url}")

    async def take_screenshot(self, name):
        try:
            timestamp = int(time.time())
            screenshot_path = self.screenshot_dir / f"{name}-{timestamp}.png"
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            self.audit_data['screenshots'].append(str(screenshot_path))
        except Exception as error:
            logger.error(f"❌ Screenshot failed: {error}")

    async def get_quick_stats(self):
        try:
            stats = await self.page.evaluate("""
                () => {
                    const totalDevices = document.querySelector('#total-devices')?.textContent || '0';
                    const successful = document.querySelector('#successful-devices')?.textContent || '0';
                    const violations = document.querySelector('#violations-count')?.textContent || '0';
                    
                    return {
                        total: parseInt(totalDevices),
                        successful: parseInt(successful),
                        violations: parseInt(violations)
                    };
                }
            """)
            
            logger.info(f"📊 Quick Stats - Total: {stats['total']}, Successful: {stats['successful']}, Violations: {stats['violations']}")
            return stats
        except Exception as error:
            logger.error(f"❌ Failed to get quick stats: {error}")
            return {'total': 0, 'successful': 0, 'violations': 0}

    async def get_raw_logs(self):
        try:
            logs = await self.page.evaluate("""
                () => {
                    const container = document.getElementById('raw-logs-container');
                    if (!container) return [];
                    
                    const logEntries = Array.from(container.children).map(entry => entry.textContent);
                    return logEntries;
                }
            """)
            
            logger.info(f"📝 Retrieved {len(logs)} raw log entries")
            return logs
        except Exception as error:
            logger.error(f"❌ Failed to get raw logs: {error}")
            return []

    async def get_audit_progress(self):
        try:
            progress = await self.page.evaluate("""
                () => {
                    const progressBar = document.querySelector('.progress-bar');
                    const progressText = document.querySelector('#audit-progress-text');
                    
                    return {
                        percentage: progressBar ? progressBar.style.width : '0%',
                        text: progressText ? progressText.textContent : 'No progress info'
                    };
                }
            """)
            
            logger.info(f"📈 Audit Progress: {progress['percentage']} - {progress['text']}")
            return progress
        except Exception as error:
            logger.error(f"❌ Failed to get audit progress: {error}")
            return {'percentage': '0%', 'text': 'Unknown'}

    async def start_audit(self):
        logger.info("🚀 Starting audit...")
        self.audit_data['start_time'] = datetime.now()
        
        # Click start audit button
        await self.page.click('#start-audit')
        await self.take_screenshot('02-audit-started')
        
        # Wait for audit to begin
        await asyncio.sleep(2)
        
        logger.info("✅ Audit started successfully")

    async def monitor_audit_progress(self):
        logger.info("👀 Monitoring audit progress...")
        
        previous_stats = {'total': 0, 'successful': 0, 'violations': 0}
        stable_count = 0
        max_stable_checks = 15  # Increased for longer audit processes
        
        while stable_count < max_stable_checks:
            # Get current stats
            current_stats = await self.get_quick_stats()
            progress = await self.get_audit_progress()
            raw_logs = await self.get_raw_logs()
            
            # Update audit data
            self.audit_data['devices_processed'] = current_stats['total']
            self.audit_data['devices_successful'] = current_stats['successful']
            self.audit_data['violations'] = current_stats['violations']
            self.audit_data['raw_logs'] = raw_logs
            
            # Check if stats changed
            if current_stats == previous_stats:
                stable_count += 1
                logger.info(f"⏳ Stats stable for {stable_count}/{max_stable_checks} checks")
            else:
                stable_count = 0
                logger.info("🔄 Stats changed - resetting stability counter")
                await self.take_screenshot(f'03-progress-{int(time.time())}')
            
            previous_stats = current_stats
            
            # Wait before next check
            await asyncio.sleep(3)
            
            # Check if audit completed
            is_completed = await self.page.evaluate("""
                () => {
                    const startBtn = document.getElementById('start-audit');
                    return startBtn && !startBtn.disabled;
                }
            """)
            
            if is_completed and current_stats['total'] > 0:
                logger.info("🎉 Audit appears to be completed")
                break
        
        self.audit_data['end_time'] = datetime.now()
        await self.take_screenshot('04-audit-completed')

    async def analyze_results(self):
        logger.info("🔍 Analyzing audit results...")
        
        duration = self.audit_data['end_time'] - self.audit_data['start_time']
        duration_seconds = int(duration.total_seconds())
        
        logger.info("============================================================")
        logger.info("📊 PLAYWRIGHT AUDIT MONITORING RESULTS")
        logger.info("============================================================")
        logger.info(f"⏱️  Duration: {duration_seconds} seconds")
        logger.info(f"📱 Total Devices: {self.audit_data['devices_processed']}")
        logger.info(f"✅ Successful: {self.audit_data['devices_successful']}")
        logger.info(f"❌ Failed: {self.audit_data['devices_processed'] - self.audit_data['devices_successful']}")
        logger.info(f"🚨 Violations: {self.audit_data['violations']}")
        logger.info(f"📝 Raw Log Entries: {len(self.audit_data['raw_logs'])}")
        
        # Check if all 6 devices were processed
        if self.audit_data['devices_processed'] != 6:
            error_msg = f"Device count mismatch: expected 6, got {self.audit_data['devices_processed']}"
            logger.error(f"❌ ISSUE: {error_msg}")
            self.audit_data['errors'].append(error_msg)
        else:
            logger.info("✅ All 6 devices were processed as expected")
        
        # Analyze raw logs for issues
        error_logs = [log for log in self.audit_data['raw_logs'] 
                     if any(keyword in log for keyword in ['ERROR', 'FAILED', '❌'])]
        
        if error_logs:
            logger.warning(f"⚠️  Found {len(error_logs)} error entries in raw logs:")
            for i, error in enumerate(error_logs, 1):
                logger.warning(f"   {i}. {error}")
        
        # Check for specific issues
        await self.check_for_specific_issues()
        
        return self.audit_data

    async def check_for_specific_issues(self):
        logger.info("🔍 Checking for specific issues...")
        
        # Check if Raw Trace Logs are visible
        raw_logs_visible = await self.page.evaluate("""
            () => {
                const container = document.getElementById('raw-logs-container');
                if (!container) return false;
                
                const style = window.getComputedStyle(container);
                return style.display !== 'none' && style.visibility !== 'hidden';
            }
        """)
        
        if not raw_logs_visible:
            error_msg = "Raw Trace Logs not visible"
            logger.error(f"❌ ISSUE: {error_msg}")
            self.audit_data['errors'].append(error_msg)
        else:
            logger.info("✅ Raw Trace Logs container is visible")
        
        # Check audit controls
        controls_status = await self.page.evaluate("""
            () => {
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
            }
        """)
        
        for control, exists in controls_status.items():
            if not exists:
                error_msg = f"Missing {control} button"
                logger.error(f"❌ ISSUE: {error_msg}")
                self.audit_data['errors'].append(error_msg)
            else:
                logger.info(f"✅ {control} button found")

    async def generate_report(self):
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'test_duration_seconds': int((self.audit_data['end_time'] - self.audit_data['start_time']).total_seconds()),
            'audit_data': {
                'start_time': self.audit_data['start_time'].isoformat(),
                'end_time': self.audit_data['end_time'].isoformat(),
                'devices_processed': self.audit_data['devices_processed'],
                'devices_successful': self.audit_data['devices_successful'],
                'devices_failed': self.audit_data['devices_processed'] - self.audit_data['devices_successful'],
                'violations': self.audit_data['violations'],
                'raw_logs_count': len(self.audit_data['raw_logs']),
                'errors': self.audit_data['errors'],
                'screenshots': self.audit_data['screenshots']
            },
            'recommendations': []
        }
        
        # Generate recommendations
        if self.audit_data['errors']:
            report_data['recommendations'].append('Fix identified errors in the audit process')
        
        if self.audit_data['devices_processed'] != 6:
            report_data['recommendations'].append('Investigate why not all 6 devices were processed')
        
        if self.audit_data['devices_successful'] == 0:
            report_data['recommendations'].append('Check network connectivity and device credentials')
        
        # Save report
        report_path = Path('./audit-monitoring-playwright-report.json')
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Report saved to: {report_path}")
        return report_data

    async def cleanup(self):
        logger.info("🧹 Cleaning up...")
        
        if self.browser:
            await self.browser.close()
        
        logger.info("✅ Cleanup completed")

async def main():
    monitor = PlaywrightAuditMonitor()
    
    try:
        await monitor.setup()
        await monitor.start_audit()
        await monitor.monitor_audit_progress()
        results = await monitor.analyze_results()
        report = await monitor.generate_report()
        
        print("\n🎉 Playwright monitoring completed successfully!")
        print("📄 Check the report at: audit-monitoring-playwright-report.json")
        print("📝 Check the logs at: audit-monitoring-playwright.log")
        print(f"📸 Check screenshots at: {monitor.screenshot_dir}/")
        
        # Return exit code based on results
        return 1 if results['errors'] else 0
        
    except Exception as error:
        logger.error(f"❌ Monitoring failed: {error}")
        await monitor.take_screenshot('error-state')
        return 1
    finally:
        await monitor.cleanup()

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 