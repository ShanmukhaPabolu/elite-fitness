// Global Sync utility with Page Routing
(function() {
    if (typeof localStorage === 'undefined') return;
    
    // Determine current page context safely
    let path = window.location.pathname.split('/').pop().replace('.html', '') || 'index';
    // Remove query params if any
    path = path.split('?')[0];

    const originalSetItem = localStorage.setItem;
    const ignoreKeys = ['loglevel']; 
    
    // Buffer strictly for the items changed on this page
    let changedDataBuffer = {};
    
    localStorage.setItem = function(key, value) {
        originalSetItem.apply(this, arguments);
        
        if (ignoreKeys.includes(key)) return;
        
        // Add to buffer
        changedDataBuffer[key] = value;
        debounceSync();
    };
    
    let syncTimeout = null;
    function debounceSync() {
        if (syncTimeout) clearTimeout(syncTimeout);
        syncTimeout = setTimeout(() => {
            // Only sync if there is something in the buffer
            if (Object.keys(changedDataBuffer).length === 0) return;

            // Take a snapshot and clear the active buffer so new edits aren't missed
            const payloadToSync = { ...changedDataBuffer };
            changedDataBuffer = {};
            
            fetch('http://127.0.0.1:5000/api/sync-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    pageContext: path,
                    payload: payloadToSync
                })
            }).catch(e => {
                // Return to buffer if network fails
                changedDataBuffer = { ...changedDataBuffer, ...payloadToSync };
            });
        }, 3000); // 3 second batch timer
    }
})();
