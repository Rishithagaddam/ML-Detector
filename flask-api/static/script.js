// Enhanced Fire Detection System JavaScript

// Utility functions
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  
  // Add to page
  document.body.appendChild(notification);
  
  // Auto remove after 3 seconds
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function validateFile(file, allowedTypes, maxSize = 50 * 1024 * 1024) { // 50MB default
  if (!allowedTypes.includes(file.type)) {
    throw new Error(`Invalid file type. Allowed: ${allowedTypes.join(', ')}`);
  }
  
  if (file.size > maxSize) {
    throw new Error(`File too large. Maximum size: ${formatBytes(maxSize)}`);
  }
  
  return true;
}

// Enhanced form handlers
async function handleFormSubmission(form, endpoint, allowedTypes) {
  try {
    const formData = new FormData(form);
    const fileInput = form.querySelector('input[type="file"]');
    
    if (fileInput && fileInput.files.length > 0) {
      validateFile(fileInput.files[0], allowedTypes);
      showNotification(`Uploading ${fileInput.files[0].name}...`, 'info');
    }
    
    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    // Show success notification
    if (result.fire_threat_level === "FIRE DETECTED") {
      showNotification('🚨 FIRE DETECTED! Check results below.', 'danger');
    } else if (result.fire_threat_level === "SAFE") {
      showNotification('✅ No fire detected - Area is safe.', 'success');
    } else {
      showNotification('✅ Analysis completed successfully.', 'success');
    }
    
    return result;
  } catch (error) {
    showNotification(`❌ Error: ${error.message}`, 'error');
    throw error;
  }
}

// Image upload handlers
document.getElementById('imageForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  try {
    const result = await handleFormSubmission(
      this, 
      '/detect-image', 
      ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    );
    // Results are handled by the existing showResults function in HTML
  } catch (error) {
    console.error('Image detection error:', error);
  }
});

// Fire image detection
document.getElementById('fireImageForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  try {
    const result = await handleFormSubmission(
      this, 
      '/detect-image', 
      ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    );
  } catch (error) {
    console.error('Fire image detection error:', error);
  }
});

// Video upload handlers
document.getElementById('videoForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  try {
    const result = await handleFormSubmission(
      this, 
      '/detect-video', 
      ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm']
    );
  } catch (error) {
    console.error('Video detection error:', error);
  }
});

// Fire video detection
document.getElementById('fireVideoForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  try {
    const result = await handleFormSubmission(
      this, 
      '/detect-video', 
      ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm']
    );
  } catch (error) {
    console.error('Fire video detection error:', error);
  }
});

// Fire scan
document.getElementById('fireScanForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  
  try {
    const result = await handleFormSubmission(
      this, 
      '/fire-scan', 
      ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
       'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm']
    );
  } catch (error) {
    console.error('Fire scan error:', error);
  }
});

// Update the fall detection form handler
document.getElementById('fallImageForm')?.addEventListener('submit', async function(e) {
  e.preventDefault(); // Prevent default form submission
  
  const formData = new FormData(this);
  const fileInput = this.querySelector('input[type="file"]');
  
  if (!fileInput.files.length) {
    showNotification('❌ Please select an image file', 'error');
    return;
  }
  
  showLoading();
  
  try {
    const response = await fetch('/detect-image', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    // Show results
    hideLoading();
    showResults(result);
    
    // Show notification based on fall detection
    if (result.fall_detected) {
      showNotification('🚨 FALL DETECTED! Check results below.', 'danger');
    } else {
      showNotification('✅ No fall detected - Area is safe.', 'success');
    }
    
  } catch (error) {
    hideLoading();
    showNotification(`❌ Error: ${error.message}`, 'error');
    console.error('Fall detection error:', error);
  }
});

// Add notification styles dynamically
const notificationStyles = `
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 10000;
  animation: slideInRight 0.3s ease;
  max-width: 300px;
  word-wrap: break-word;
}

.notification-info {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.notification-success {
  background: linear-gradient(135deg, #38a169, #2f855a);
}

.notification-error, .notification-danger {
  background: linear-gradient(135deg, #e53e3e, #c53030);
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
`;

// Inject notification styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  console.log('🔥 Fire Detection System Initialized');
  showNotification('Fire Detection System Ready', 'info');
});
