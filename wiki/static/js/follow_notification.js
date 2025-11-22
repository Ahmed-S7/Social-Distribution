// Follow Request Notification System
// This script polls for new follow requests and displays notifications at the top of the screen
// Rate-limited to check every 15 minutes to prevent spam

(function() {
  'use strict';
  
  // Configuration
  const POLL_INTERVAL = 15 * 60 * 1000; // Check every 15 minutes (900,000 ms)
  const NOTIFICATION_DURATION = 6000; // Show notification for 6 seconds
  const TRACKING_WINDOW = 15 * 60 * 1000; // Track requests from last 15 minutes
  
  let lastCheckTime = null;
  let pollIntervalId = null;
  let activeNotificationId = null;
  
  // Get CSRF token from cookies
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  
  // Create notification container if it doesn't exist
  function ensureNotificationContainer() {
    let container = document.getElementById('follow-notification-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'follow-notification-container';
      container.className = 'follow-notification-container';
      document.body.appendChild(container);
    }
    return container;
  }
  
  // Get notified request IDs from localStorage
  function getNotifiedRequestIds() {
    try {
      const stored = localStorage.getItem('follow_request_notified_ids');
      if (!stored) return new Set();
      const data = JSON.parse(stored);
      const now = Date.now();
      // Filter out old entries (older than tracking window)
      const recentIds = data.filter(entry => (now - entry.timestamp) < TRACKING_WINDOW);
      // Update storage
      localStorage.setItem('follow_request_notified_ids', JSON.stringify(recentIds));
      return new Set(recentIds.map(entry => entry.id));
    } catch (e) {
      console.error('Error reading notified request IDs:', e);
      return new Set();
    }
  }
  
  // Mark request IDs as notified
  function markAsNotified(requestIds) {
    try {
      const stored = localStorage.getItem('follow_request_notified_ids');
      const existing = stored ? JSON.parse(stored) : [];
      const now = Date.now();
      
      // Add new IDs with current timestamp
      requestIds.forEach(id => {
        // Remove if already exists
        const filtered = existing.filter(entry => entry.id !== id);
        filtered.push({ id: id, timestamp: now });
        existing.length = 0;
        existing.push(...filtered);
      });
      
      // Clean up old entries
      const recent = existing.filter(entry => (now - entry.timestamp) < TRACKING_WINDOW);
      localStorage.setItem('follow_request_notified_ids', JSON.stringify(recent));
    } catch (e) {
      console.error('Error storing notified request IDs:', e);
    }
  }
  
  // Show a summary notification for new follow requests
  function showNotification(count, authorSerial) {
    // Hide existing notification if any
    if (activeNotificationId) {
      const existing = document.getElementById(activeNotificationId);
      if (existing) {
        hideNotification(existing);
      }
    }
    
    const container = ensureNotificationContainer();
    const notificationId = 'follow-notification-' + Date.now();
    activeNotificationId = notificationId;
    
    const notification = document.createElement('div');
    notification.id = notificationId;
    notification.className = 'follow-notification';
    
    const requestText = count === 1 ? 'request' : 'requests';
    
    notification.innerHTML = `
      <div class="follow-notification-content">
        <div class="follow-notification-icon">🔔</div>
        <div class="follow-notification-text">
          You have <strong>${count} new follow ${requestText}</strong>
        </div>
        <a href="/authors/${authorSerial}/follow_requests/" class="follow-notification-link">
          View Follow Requests
        </a>
        <button class="follow-notification-close">&times;</button>
      </div>
    `;
    
    // Add close button functionality
    const closeBtn = notification.querySelector('.follow-notification-close');
    closeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      hideNotification(notification);
    });
    
    // Click anywhere on notification to go to requests page
    notification.querySelector('.follow-notification-content').addEventListener('click', (e) => {
      if (e.target !== closeBtn && !closeBtn.contains(e.target)) {
        window.location.href = `/authors/${authorSerial}/follow_requests/`;
      }
    });
    
    // Add to container
    container.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    // Auto-hide after duration
    setTimeout(() => {
      if (document.getElementById(notificationId)) {
        hideNotification(notification);
      }
    }, NOTIFICATION_DURATION);
    
    return notification;
  }
  
  // Hide a notification
  function hideNotification(notification) {
    if (!notification) return;
    
    notification.classList.remove('show');
    notification.classList.add('hide');
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
      if (activeNotificationId === notification.id) {
        activeNotificationId = null;
      }
    }, 300); // Wait for fade-out animation
  }
  
  // Get current author serial (from page context or API)
  function getAuthorSerial() {
    // Try to get from template constant first (most reliable)
    if (typeof CURRENT_AUTHOR_SERIAL !== 'undefined' && CURRENT_AUTHOR_SERIAL) {
      return CURRENT_AUTHOR_SERIAL;
    }
    
    // Try to get from AUTHOR_ID constant if available
    if (typeof AUTHOR_ID !== 'undefined' && AUTHOR_ID) {
      return AUTHOR_ID.split('/').pop();
    }
    
    // Try to get from URL pattern (for profile pages)
    const urlMatch = window.location.pathname.match(/\/authors\/([^\/]+)/);
    if (urlMatch) {
      return urlMatch[1];
    }
    
    // Try to get from profile link in navigation
    const profileLink = document.querySelector('a[href*="/authors/"]');
    if (profileLink) {
      const match = profileLink.href.match(/\/authors\/([^\/]+)/);
      if (match) {
        return match[1];
      }
    }
    
    return null;
  }
  
  // Check for new follow requests
  async function checkForNewFollowRequests() {
    const authorSerial = getAuthorSerial();
    if (!authorSerial) {
      return; // Can't check without author serial
    }
    
    try {
      const csrftoken = getCookie('csrftoken');
      const url = `/api/authors/${authorSerial}/follow_requests/`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        credentials: 'same-origin'
      });
      
      if (!response.ok) {
        return;
      }
      
      const data = await response.json();
      
      // Filter for new requests (only REQUESTING state)
      const allRequests = Array.isArray(data) 
        ? data.filter(req => req.state === 'requesting')
        : [];
      
      // Get IDs we've already notified about
      const notifiedIds = getNotifiedRequestIds();
      
      // Find new requests (ones we haven't notified about)
      const newRequestIds = [];
      allRequests.forEach(request => {
        // Create unique identifier from actor and object IDs
        // This uniquely identifies each follow request
        let requestId = null;
        if (request.actor && request.actor.id && request.object && request.object.id) {
          const actorId = request.actor.id;
          const objectId = request.object.id;
          // Create unique ID from both actor and object
          requestId = `${actorId}->${objectId}`;
        }
        
        if (requestId && !notifiedIds.has(requestId)) {
          newRequestIds.push(requestId);
        }
      });
      
      // If there are new requests, show notification
      if (newRequestIds.length > 0) {
        markAsNotified(newRequestIds);
        showNotification(newRequestIds.length, authorSerial);
      }
      
      lastCheckTime = new Date();
      
    } catch (error) {
      console.error('Error checking for follow requests:', error);
    }
  }
  
  // Start polling for follow requests
  function startPolling() {
    // Only start if user is authenticated
    if (!document.cookie.includes('sessionid')) {
      return;
    }
    
    // Check immediately on page load (user might have new requests)
    checkForNewFollowRequests();
    
    // Then check periodically (every 15 minutes)
    if (pollIntervalId) {
      clearInterval(pollIntervalId);
    }
    
    pollIntervalId = setInterval(() => {
      checkForNewFollowRequests();
    }, POLL_INTERVAL);
  }
  
  // Stop polling
  function stopPolling() {
    if (pollIntervalId) {
      clearInterval(pollIntervalId);
      pollIntervalId = null;
    }
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startPolling);
  } else {
    startPolling();
  }
  
  // Check when page becomes visible again (user returns to tab)
  document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
      // Check immediately when user returns to the tab
      // (they might have received requests while away)
      checkForNewFollowRequests();
    }
  });
  
  // Export functions for manual control
  window.FollowNotificationSystem = {
    check: checkForNewFollowRequests,
    start: startPolling,
    stop: stopPolling
  };
})();

