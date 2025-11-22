/**
 * Dark Mode Toggle Functionality
 * Handles theme switching and localStorage persistence
 */

(function() {
  'use strict';

  // Get theme from localStorage or default to 'light'
  function getTheme() {
    return localStorage.getItem('theme') || 'light';
  }

  // Set theme in localStorage and on document
  function setTheme(theme) {
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    updateToggleButton(theme);
  }

  // Initialize theme on page load
  function initTheme() {
    const theme = getTheme();
    setTheme(theme);
  }

  // Toggle between light and dark mode
  function toggleTheme() {
    const currentTheme = getTheme();
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  }

  // Update toggle button icon based on theme
  function updateToggleButton(theme) {
    const toggleButton = document.getElementById('dark-mode-toggle');
    if (toggleButton) {
      toggleButton.textContent = theme === 'dark' ? '🌙' : '☀️';
      toggleButton.setAttribute('aria-label', 
        theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
      );
      toggleButton.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    }
  }

  // Create and insert toggle button into the page
  function createToggleButton() {
    // Check if button already exists
    if (document.getElementById('dark-mode-toggle')) {
      return;
    }

    const toggleButton = document.createElement('button');
    toggleButton.id = 'dark-mode-toggle';
    toggleButton.className = 'dark-mode-toggle';
    toggleButton.setAttribute('aria-label', 'Toggle dark mode');
    toggleButton.setAttribute('type', 'button');
    toggleButton.title = 'Toggle dark mode';
    toggleButton.setAttribute('tabindex', '0'); // Make keyboard accessible
    
    // Add click event listener
    toggleButton.addEventListener('click', toggleTheme);
    
    // Add keyboard support (Enter and Space)
    toggleButton.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleTheme();
      }
    });
    
    // Check if there's a bottom navigation bar and adjust position
    // Wait a bit for DOM to fully load
    setTimeout(function() {
      const hasBottomBar = document.querySelector('.profile_buttons') || 
                          document.querySelector('.nav_buttons') ||
                          document.querySelector('[class*="profile_buttons"]') ||
                          document.querySelector('[class*="nav_buttons"]');
      if (hasBottomBar) {
        toggleButton.style.bottom = '6rem';
        
        // Additional check for mobile
        if (window.innerWidth <= 768) {
          toggleButton.style.bottom = '7rem';
        }
      }
    }, 100);
    
    // Insert button into the page
    document.body.appendChild(toggleButton);
    
    // Update icon based on current theme
    updateToggleButton(getTheme());
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initTheme();
      createToggleButton();
    });
  } else {
    // DOM already loaded
    initTheme();
    createToggleButton();
  }

  // Expose toggle function globally in case needed
  window.toggleDarkMode = toggleTheme;
  window.setDarkMode = function(theme) {
    if (theme === 'dark' || theme === 'light') {
      setTheme(theme);
    }
  };
  window.getDarkMode = getTheme;

})();

