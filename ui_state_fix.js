// UI State Fix for NetAuditPro
// Ensures all UI elements show consistent completed audit data

function fixUIState() {
    console.log('🔧 Applying UI State Fix...');
    
    // Force refresh all data from APIs
    Promise.all([
        fetch('/api/progress').then(r => r.json()),
        fetch('/api/timing').then(r => r.json())
    ]).then(([progressData, timingData]) => {
        console.log('📊 Progress Data:', progressData);
        console.log('⏰ Timing Data:', timingData);
        
        // Update Quick Stats
        if (progressData.success) {
            document.getElementById('total-devices-count').textContent = progressData.total_devices || 0;
            document.getElementById('successful-devices-count').textContent = progressData.status_counts?.success || 0;
            document.getElementById('violations-count').textContent = progressData.status_counts?.violations || 0;
            
            // Update progress bar
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = progressData.percent_complete + '%';
                progressBar.textContent = progressData.percent_complete.toFixed(1) + '%';
            }
            
            // Update current device
            const currentDeviceElement = document.getElementById('current-device');
            if (currentDeviceElement) {
                currentDeviceElement.textContent = progressData.current_device || 'None';
            }
        }
        
        // Update timing information
        if (timingData.success && timingData.timing) {
            const timing = timingData.timing;
            
            // Update start time
            if (timing.raw_start_time) {
                const startDate = new Date(timing.raw_start_time * 1000);
                const startTimeElement = document.getElementById('audit-start-time');
                const startDateElement = document.getElementById('audit-start-date');
                
                if (startTimeElement) {
                    startTimeElement.textContent = startDate.toLocaleTimeString();
                }
                if (startDateElement) {
                    startDateElement.textContent = startDate.toLocaleDateString();
                }
            }
            
            // Update elapsed time
            const elapsedTimeElement = document.getElementById('audit-elapsed-time');
            if (elapsedTimeElement) {
                elapsedTimeElement.textContent = timing.formatted_elapsed_time || "00:00:00";
            }
            
            // Update completion time if available
            if (timing.raw_completion_time) {
                const completionDate = new Date(timing.raw_completion_time * 1000);
                const completionTimeElement = document.getElementById('audit-completion-time');
                const completionDateElement = document.getElementById('audit-completion-date');
                
                if (completionTimeElement) {
                    completionTimeElement.textContent = completionDate.toLocaleTimeString();
                }
                if (completionDateElement) {
                    completionDateElement.textContent = completionDate.toLocaleDateString();
                }
            }
        }
        
        console.log('✅ UI State Fix Applied Successfully');
    }).catch(error => {
        console.error('❌ UI State Fix Failed:', error);
    });
}

// Apply fix immediately and set up periodic refresh
fixUIState();
setInterval(fixUIState, 5000); // Refresh every 5 seconds

console.log('🚀 UI State Fix Loaded - Timing display should now be consistent'); 