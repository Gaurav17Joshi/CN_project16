// Enhanced dashboard.js for real-time updates and status indication

(function() {
    // Use the same host as the HTTP server, but the WebSocket port
    const wsHost = window.location.hostname; // Get hostname from browser URL
    const wsPort = 8001; // Must match WEBSOCKET_PORT in Python server
    const wsUrl = `ws://${wsHost}:${wsPort}`;

    let socket = null;
    let reconnectInterval = 5000; // Milliseconds to wait before retrying connection
    let maxReconnectInterval = 30000; // Maximum wait time
    let reconnectAttempts = 0;
    let reconnectTimer = null;
    let autoRefreshTimer = null;

    // Add connection status indicator to the page
    function createStatusIndicator() {
        const statusDiv = document.createElement('div');
        statusDiv.id = 'connection-status';
        statusDiv.className = 'status-connecting';
        statusDiv.textContent = 'Connecting...';
        document.body.appendChild(statusDiv);
        return statusDiv;
    }

    const statusIndicator = createStatusIndicator();

    function updateConnectionStatus(status, message) {
        if (statusIndicator) {
            statusIndicator.className = status;
            statusIndicator.textContent = message;
        }
    }

    function setupAutoRefresh() {
        // Clear any existing timer
        if (autoRefreshTimer) {
            clearTimeout(autoRefreshTimer);
        }
        
        // Set a new timer for 15 seconds - fallback refresh
        console.log("Setting up 15s automatic refresh timer");
        autoRefreshTimer = setTimeout(function() {
            console.log("Auto-refresh timer triggered - reloading page");
            window.location.reload();
        }, 15000);
    }

    function connectWebSocket() {
        // Clear any existing reconnect timer
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }

        updateConnectionStatus('status-connecting', 'Connecting...');
        console.log(`Attempting to connect WebSocket to: ${wsUrl}`);
        
        try {
            // Create new WebSocket with error handling
            try {
                socket = new WebSocket(wsUrl);
            } catch (err) {
                console.error("Error creating WebSocket:", err);
                updateConnectionStatus('status-disconnected', 'Connection Failed');
                reconnectTimer = setTimeout(connectWebSocket, reconnectInterval);
                return;
            }

            socket.onopen = function(event) {
                console.log("WebSocket connection established.");
                updateConnectionStatus('status-connected', 'Connected');
                
                // Reset reconnect parameters on successful connection
                reconnectAttempts = 0;
                reconnectInterval = 5000;
                
                // Send a ping to confirm connection is working
                try {
                    socket.send("ping");
                    console.log("Sent ping to confirm connection");
                } catch (err) {
                    console.warn("Could not send ping:", err);
                }
                
                // Setup the auto-refresh fallback
                setupAutoRefresh();
            };

            socket.onmessage = function(event) {
                console.log("Message received from server:", event.data);
                
                // Check if the server sent the refresh signal
                if (event.data === "refresh") {
                    console.log("Refresh signal received - reloading page");
                    
                    // Clear the auto-refresh timer before reloading
                    if (autoRefreshTimer) {
                        clearTimeout(autoRefreshTimer);
                        autoRefreshTimer = null;
                    }
                    
                    // Add a small delay to ensure server has fully processed the event
                    setTimeout(function() {
                        window.location.reload();
                    }, 200);
                }
            };

            socket.onerror = function(event) {
                console.error("WebSocket error observed:", event);
                updateConnectionStatus('status-disconnected', 'Connection Error');
                // Note: onclose will usually be called after onerror
            };

            socket.onclose = function(event) {
                console.log(`WebSocket connection closed. Code: ${event.code}, Reason: ${event.reason}`);
                updateConnectionStatus('status-disconnected', 'Disconnected');
                
                socket = null; // Ensure socket is nullified

                // Exponential backoff for reconnection attempts
                reconnectAttempts++;
                const currentWait = Math.min(reconnectInterval * Math.pow(1.5, reconnectAttempts - 1), maxReconnectInterval);
                console.log(`Waiting ${currentWait / 1000} seconds before next reconnect attempt.`);
                
                // Schedule reconnection
                reconnectTimer = setTimeout(connectWebSocket, currentWait);
            };
        } catch (error) {
            console.error("Error creating WebSocket:", error);
            updateConnectionStatus('status-disconnected', 'Connection Failed');
            
            // Try again after a delay
            reconnectTimer = setTimeout(connectWebSocket, reconnectInterval);
        }
    }

    // Set up page visibility change handling
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            console.log("Page is now visible - checking connection status");
            // Check if WebSocket is disconnected when page becomes visible
            if (!socket || socket.readyState !== WebSocket.OPEN) {
                console.log("WebSocket not connected, attempting reconnection...");
                connectWebSocket();
            } else {
                console.log("WebSocket is already connected");
            }
        }
    });

    // Initial connection attempt
    connectWebSocket();
    
    // Setup initial auto-refresh timer
    setupAutoRefresh();

})(); // Immediately Invoked Function Expression (IIFE) to keep scope clean