#!/usr/bin/env python3

import os
import re

def enhance_auto_reload(input_filepath, output_filepath):
    """
    Enhances the auto-reload functionality in the NetAuditPro application.
    
    Improvements:
    1. Optimizes the fetchProgressData function for more efficient updates
    2. Improves Socket.IO event handling for real-time updates
    3. Enhances the Stop/Reset button functionality
    4. Adds visual indicators for data refresh
    """
    print(f"Reading from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{input_filepath}': {e}")
        return False

    # Enhancement 1: Improve fetchProgressData function
    original_fetch_progress = """    // Function to fetch progress data and update UI
    function fetchProgressData() {
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

    improved_fetch_progress = """    // Function to fetch progress data and update UI with optimized refresh
    function fetchProgressData() {
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

    # Enhancement 2: Add refresh indicator HTML
    html_body_pattern = r'<body[^>]*>(.*?)<div class="container-fluid">'
    refresh_indicator_html = """<body>
    <!-- Refresh status indicator -->
    <div id="refresh-indicator" class="refresh-status">
        <div class="refresh-spinner"></div>
        <span>Refreshing data...</span>
    </div>
    
    <div class="container-fluid">"""

    # Enhancement 3: Improve Stop/Reset button functionality
    stop_button_pattern = r'<button[^>]*id="stop-audit-btn"[^>]*>Stop/Reset Audit</button>'
    improved_stop_button = """<button id="stop-audit-btn" class="btn btn-danger" onclick="stopAuditWithConfirmation()">Stop/Reset Audit</button>"""

    # Enhancement 4: Add CSS for refresh indicator and improved UI feedback
    css_additions = """
    <style>
        /* Refresh indicator styles */
        .refresh-status {
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
        
        .refresh-status.refreshing {
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
        
        /* Improve Stop/Reset button visibility */
        #stop-audit-btn {
            position: relative;
            overflow: hidden;
        }
        
        #stop-audit-btn:after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 0;
            height: 100%;
            background-color: rgba(255,255,255,0.2);
            transition: width 0.3s;
        }
        
        #stop-audit-btn:hover:after {
            width: 100%;
        }
        
        /* Improve audit status visibility */
        .audit-status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }
        
        .status-running { background-color: #28a745; }
        .status-paused { background-color: #ffc107; }
        .status-completed { background-color: #17a2b8; }
        .status-error { background-color: #dc3545; }
    </style>
    """

    # Enhancement 5: Add JavaScript for improved Stop/Reset functionality
    stop_audit_js = """
    // Enhanced Stop/Reset Audit functionality
    function stopAuditWithConfirmation() {
        // Create confirmation modal if it doesn't exist
        if (!document.getElementById('stop-audit-modal')) {
            const modalHTML = `
                <div class="modal fade" id="stop-audit-modal" tabindex="-1" role="dialog" aria-labelledby="stopAuditModalLabel" aria-hidden="true">
                    <div class="modal-dialog" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="stopAuditModalLabel">Confirm Stop/Reset</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                Are you sure you want to stop and reset the current audit?
                                <div class="mt-2 text-warning">
                                    <small>This will terminate all connections and reset the audit state.</small>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-danger" id="confirm-stop-btn">Stop & Reset</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHTML;
            document.body.appendChild(modalContainer.firstChild);
            
            // Add event listener to confirmation button
            document.getElementById('confirm-stop-btn').addEventListener('click', function() {
                // Show loading state
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Stopping...';
                this.disabled = true;
                
                // Call the stop audit endpoint
                fetch('/stop_audit', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Audit stopped:', data);
                        $('#stop-audit-modal').modal('hide');
                        
                        // Show success notification
                        showNotification('Audit stopped and reset successfully', 'success');
                        
                        // Force immediate data refresh
                        restartDataFetch();
                    })
                    .catch(error => {
                        console.error('Error stopping audit:', error);
                        // Show error notification
                        showNotification('Error stopping audit: ' + error, 'danger');
                        
                        // Reset button state
                        document.getElementById('confirm-stop-btn').innerHTML = 'Stop & Reset';
                        document.getElementById('confirm-stop-btn').disabled = false;
                    });
            });
        }
        
        // Show the modal
        $('#stop-audit-modal').modal('show');
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
        
        // Create notifications container if it doesn't exist
        let notificationsContainer = document.getElementById('notifications-container');
        if (!notificationsContainer) {
            notificationsContainer = document.createElement('div');
            notificationsContainer.id = 'notifications-container';
            notificationsContainer.style.position = 'fixed';
            notificationsContainer.style.top = '20px';
            notificationsContainer.style.right = '20px';
            notificationsContainer.style.zIndex = '9999';
            notificationsContainer.style.maxWidth = '350px';
            document.body.appendChild(notificationsContainer);
        }
        
        // Add notification to container
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
    """

    # Apply all enhancements
    print("Applying auto-reload enhancements...")
    
    # 1. Replace fetchProgressData function
    if original_fetch_progress in content:
        content = content.replace(original_fetch_progress, improved_fetch_progress)
        print("✓ Enhanced fetchProgressData function")
    else:
        print("⚠ Could not find original fetchProgressData function")
    
    # 2. Add refresh indicator to HTML body
    body_match = re.search(html_body_pattern, content, re.DOTALL)
    if body_match:
        content = content.replace(body_match.group(0), refresh_indicator_html)
        print("✓ Added refresh indicator to HTML")
    else:
        print("⚠ Could not find HTML body tag")
    
    # 3. Enhance Stop/Reset button
    stop_btn_match = re.search(stop_button_pattern, content)
    if stop_btn_match:
        content = content.replace(stop_btn_match.group(0), improved_stop_button)
        print("✓ Enhanced Stop/Reset button")
    else:
        print("⚠ Could not find Stop/Reset button")
    
    # 4. Add CSS styles before </head>
    if "</head>" in content:
        content = content.replace("</head>", f"{css_additions}</head>")
        print("✓ Added CSS styles for enhanced UI")
    else:
        print("⚠ Could not find </head> tag")
    
    # 5. Add enhanced Stop/Reset JavaScript before </script> of the main script block
    socket_io_init_pattern = r"// Initialize Socket\.IO"
    if socket_io_init_pattern in content:
        # Insert the stop audit JS before Socket.IO initialization
        content = re.sub(
            socket_io_init_pattern,
            f"{stop_audit_js}\n\n    // Initialize Socket.IO",
            content
        )
        print("✓ Added enhanced Stop/Reset JavaScript")
    else:
        print("⚠ Could not find Socket.IO initialization point")

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
