#!/usr/bin/env python3

import os
import re

def enhance_auto_reload(input_filepath, output_filepath):
    """
    Enhances the auto-reload functionality in the NetAuditPro application.
    
    Improvements:
    1. Optimizes the fetchProgressData function for more efficient updates
    2. Adds visual indicators for data refresh
    3. Implements adaptive polling based on audit status
    4. Enhances the Stop/Reset button functionality
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # Enhancement 1: Improve fetchProgressData function
    original_fetch_progress = """    function fetchProgressData() {
        fetch('/audit_progress_data')
            .then(response => response.json())
            .then(data => {
                // Update standard progress elements
                const progressBar = document.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = data.progress.percentage_complete + '%';
                    progressBar.setAttribute('aria-valuenow', data.progress.percentage_complete);
                    progressBar.textContent = data.progress.percentage_complete + '%';
                }
                
                // Update enhanced progress tracking UI
                updateEnhancedProgressUI(data);
                
                // Update logs
                const logsContainer = document.getElementById('logs-container');
                if (logsContainer) {
                    logsContainer.innerHTML = '';
                    data.ui_logs.forEach(log => {
                        const logLine = document.createElement('div');
                        logLine.innerHTML = log;
                        logsContainer.appendChild(logLine);
                    });
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                }
                
                // Schedule next update if audit is running or paused
                if (data.overall_audit_status === 'Running' || data.audit_paused) {
                    setTimeout(fetchProgressData, 1000); // Update every second
                } else {
                    setTimeout(fetchProgressData, 5000); // Update every 5 seconds when idle
                }
            })
            .catch(error => {
                console.error('Error fetching progress data:', error);
                setTimeout(fetchProgressData, 5000); // Retry after 5 seconds
            });
    }"""

    improved_fetch_progress = """    function fetchProgressData() {
        // Add visual indicator that data is being refreshed
        const refreshIndicator = document.getElementById('refresh-indicator');
        if (refreshIndicator) {
            refreshIndicator.classList.add('refreshing');
        }
        
        fetch('/audit_progress_data')
            .then(response => response.json())
            .then(data => {
                // Update standard progress elements
                const progressBar = document.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = data.progress.percentage_complete + '%';
                    progressBar.setAttribute('aria-valuenow', data.progress.percentage_complete);
                    progressBar.textContent = data.progress.percentage_complete + '%';
                }
                
                // Update enhanced progress tracking UI
                updateEnhancedProgressUI(data);
                
                // Update logs with smart diffing (only append new logs)
                const logsContainer = document.getElementById('logs-container');
                if (logsContainer) {
                    // Store current log count to determine if new logs were added
                    const currentLogCount = logsContainer.childElementCount;
                    const newLogsCount = data.ui_logs.length;
                    
                    // Only clear and rebuild if the structure changed significantly
                    if (Math.abs(currentLogCount - newLogsCount) > 5 || newLogsCount < currentLogCount) {
                        logsContainer.innerHTML = '';
                        data.ui_logs.forEach(log => {
                            const logLine = document.createElement('div');
                            logLine.innerHTML = log;
                            logsContainer.appendChild(logLine);
                        });
                    } else if (newLogsCount > currentLogCount) {
                        // Append only new logs for efficiency
                        for (let i = currentLogCount; i < newLogsCount; i++) {
                            const logLine = document.createElement('div');
                            logLine.innerHTML = data.ui_logs[i];
                            logLine.classList.add('new-log-entry');
                            logsContainer.appendChild(logLine);
                            
                            // Remove highlight after animation
                            setTimeout(() => {
                                logLine.classList.remove('new-log-entry');
                            }, 2000);
                        }
                    }
                    
                    // Always scroll to bottom for new logs
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                }
                
                // Update page title with status for better user awareness
                document.title = `NetAuditPro - ${data.overall_audit_status}`;
                
                // Remove refresh indicator
                if (refreshIndicator) {
                    refreshIndicator.classList.remove('refreshing');
                }
                
                // Adaptive polling rate based on activity
                let refreshRate = 5000; // Default 5 seconds
                
                if (data.overall_audit_status === 'Running') {
                    refreshRate = 1000; // 1 second for active audits
                } else if (data.audit_paused) {
                    refreshRate = 2000; // 2 seconds for paused audits
                } else if (data.last_activity_seconds < 30) {
                    refreshRate = 3000; // 3 seconds if recent activity
                }
                
                // Schedule next update with adaptive rate
                window.nextFetchTimeout = setTimeout(fetchProgressData, refreshRate);
            })
            .catch(error => {
                console.error('Error fetching progress data:', error);
                
                // Remove refresh indicator on error
                if (refreshIndicator) {
                    refreshIndicator.classList.remove('refreshing');
                }
                
                // Exponential backoff for retries (up to 30 seconds)
                const retryDelay = Math.min(30000, (window.lastRetryDelay || 5000) * 1.5);
                window.lastRetryDelay = retryDelay;
                
                console.log(`Retrying in ${retryDelay/1000} seconds...`);
                window.nextFetchTimeout = setTimeout(fetchProgressData, retryDelay);
            });
    }
    
    // Function to cancel current fetch timeout and start a new one
    function restartDataFetch() {
        if (window.nextFetchTimeout) {
            clearTimeout(window.nextFetchTimeout);
        }
        window.lastRetryDelay = 5000; // Reset retry delay
        fetchProgressData();
    }"""

    # Enhancement 2: Add CSS for refresh indicator and improved UI
    css_styles = """
    <style>
        /* Refresh indicator styles */
        #refresh-indicator {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }
        
        #refresh-indicator.refreshing {
            opacity: 1;
        }
        
        .refresh-spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Highlight new log entries */
        .new-log-entry {
            animation: highlightNew 2s ease;
        }
        
        @keyframes highlightNew {
            0% { background-color: rgba(255, 255, 0, 0.3); }
            100% { background-color: transparent; }
        }
        
        /* Notifications container */
        #notifications-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
        }
        
        .notification-toast {
            margin-bottom: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
    </style>
    """

    # Enhancement 3: Add HTML for refresh indicator and notifications container
    html_additions = """
    <!-- Refresh indicator -->
    <div id="refresh-indicator">
        <div class="refresh-spinner"></div>
        <span>Refreshing data...</span>
    </div>
    
    <!-- Notifications container -->
    <div id="notifications-container"></div>
    """

    # Enhancement 4: Add JavaScript for improved Stop/Reset functionality
    stop_reset_js = """
    // Enhanced Stop/Reset functionality
    function stopAuditWithConfirmation() {
        if (confirm("Are you sure you want to stop and reset the current audit? This will terminate all connections.")) {
            // Show loading notification
            showNotification("Stopping audit...", "info");
            
            // Call the stop audit endpoint
            fetch('/stop_audit', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Audit stopped:', data);
                    
                    // Show success notification
                    showNotification('Audit stopped and reset successfully', 'success');
                    
                    // Force immediate data refresh
                    restartDataFetch();
                })
                .catch(error => {
                    console.error('Error stopping audit:', error);
                    // Show error notification
                    showNotification('Error stopping audit: ' + error, 'danger');
                });
        }
    }
    
    // Notification helper
    function showNotification(message, type = 'info') {
        const notificationId = 'notification-' + Date.now();
        const notificationHTML = `
            <div id="${notificationId}" class="alert alert-${type} alert-dismissible fade show notification-toast" role="alert">
                ${message}
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
        `;
        
        // Add notification to container
        const notificationsContainer = document.getElementById('notifications-container');
        if (notificationsContainer) {
            notificationsContainer.innerHTML += notificationHTML;
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                const notification = document.getElementById(notificationId);
                if (notification) {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 500);
                }
            }, 5000);
        }
    }
    """

    # Apply enhancements
    print("Applying auto-reload enhancements...")
    
    # 1. Replace fetchProgressData function
    if original_fetch_progress in content:
        content = content.replace(original_fetch_progress, improved_fetch_progress)
        print("✓ Enhanced fetchProgressData function")
    else:
        print("⚠ Could not find original fetchProgressData function")
    
    # 2. Add CSS styles before </head>
    if "</head>" in content:
        content = content.replace("</head>", f"{css_styles}</head>")
        print("✓ Added CSS styles for enhanced UI")
    else:
        print("⚠ Could not find </head> tag")
    
    # 3. Add HTML elements after <body> tag
    body_pattern = r"<body[^>]*>"
    body_match = re.search(body_pattern, content)
    if body_match:
        content = content.replace(body_match.group(0), f"{body_match.group(0)}\n    {html_additions}")
        print("✓ Added HTML elements for refresh indicator and notifications")
    else:
        print("⚠ Could not find <body> tag")
    
    # 4. Add Stop/Reset JavaScript before the DOMContentLoaded event listener
    dom_content_loaded_pattern = r"document\.addEventListener\('DOMContentLoaded', function\(\) \{"
    dom_content_match = re.search(dom_content_loaded_pattern, content)
    if dom_content_match:
        # Insert the stop audit JS before DOMContentLoaded
        insertion_point = content.rfind("    // ", 0, dom_content_match.start())
        if insertion_point != -1:
            content = content[:insertion_point] + stop_reset_js + "\n\n" + content[insertion_point:]
            print("✓ Added enhanced Stop/Reset JavaScript")
        else:
            print("⚠ Could not find appropriate insertion point for Stop/Reset JavaScript")
    else:
        print("⚠ Could not find DOMContentLoaded event listener")
    
    # 5. Modify the Stop/Reset button to use the new function
    stop_button_pattern = r'<button[^>]*id="stop-audit-btn"[^>]*>'
    stop_button_match = re.search(stop_button_pattern, content)
    if stop_button_match:
        # Add onclick handler to the existing button
        modified_button = stop_button_match.group(0).replace('>', ' onclick="stopAuditWithConfirmation()">')
        content = content.replace(stop_button_match.group(0), modified_button)
        print("✓ Enhanced Stop/Reset button with confirmation")
    else:
        print("⚠ Could not find Stop/Reset button")

    print(f"Writing modified content to: {output_filepath}")
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing to file '{output_filepath}': {e}")
        return False
        
    return True

if __name__ == "__main__":
    input_file = "/root/za-con/rr3-router.py"
    output_file = "/root/za-con/rr3-router.py.enhanced"
    
    if enhance_auto_reload(input_file, output_file):
        print(f"Auto-reload enhancements applied. Modified file saved as: {output_file}")
        print("Please review the changes in the new file.")
        print(f"If satisfied, you can replace the original file by running: mv {output_file} {input_file}")
    else:
        print("Failed to apply auto-reload enhancements.")
