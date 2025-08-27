function confirmUnsubscribe() {
  // Get the email parameter from the URL if present
  const urlParams = new URLSearchParams(window.location.search);
  const email = urlParams.get('email');
  const token = urlParams.get('token');
  
  if (confirm('Are you absolutely sure you want to unsubscribe from ShellCast emails? This action cannot be undone.')) {
    // Show loading state
    const container = document.querySelector('.unsubscribe-container');
    container.innerHTML = `
      <div class="unsubscribe-header">
        <img src="/static/img/shellcast_logo.png" 
             alt="ShellCast logo" 
             class="unsubscribe-logo">
        <h1 class="h3">Processing...</h1>
      </div>
      
      <div class="unsubscribe-message">
        <p class="mb-0">
          <strong>Please wait while we process your unsubscription request...</strong>
        </p>
      </div>
    `;
    
    // Make API call to unsubscribe
    fetch('/api/unsubscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        token: token
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.message) {
        // Success - show success message
        container.innerHTML = `
          <div class="unsubscribe-header">
            <img src="/static/img/shellcast_logo.png" 
                 alt="ShellCast logo" 
                 class="unsubscribe-logo">
            <h1 class="h3">Unsubscribed Successfully</h1>
          </div>
          
          <div class="unsubscribe-message">
            <p class="mb-3">
              <strong>You have been successfully unsubscribed!</strong>
            </p>
            <p class="mb-0">
              You will no longer receive email notifications from ShellCast. 
              If you change your mind, you can always re-subscribe by visiting 
              your preferences page after signing in to your account.
            </p>
          </div>
          
          <div class="unsubscribe-actions">
            <a href="/" class="btn btn-cancel">
              Return to ShellCast
            </a>
          </div>
          
          <div class="footer-links">
            <a href="/about">About ShellCast</a>
            <a href="/feedback">Contact Us</a>
          </div>
        `;
      } else {
        // Error - show error message
        throw new Error(data.errors ? data.errors.join(', ') : 'Unknown error occurred');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      // Show error message
      container.innerHTML = `
        <div class="unsubscribe-header">
          <img src="/static/img/shellcast_logo.png" 
               alt="ShellCast logo" 
               class="unsubscribe-logo">
          <h1 class="h3">Error Occurred</h1>
        </div>
        
        <div class="unsubscribe-message">
          <p class="mb-3">
            <strong>Sorry, we encountered an error while processing your request.</strong>
          </p>
          <p class="mb-0">
            Please try again later or contact us for assistance.
          </p>
        </div>
        
        <div class="unsubscribe-actions">
          <a href="/" class="btn btn-cancel">
            Return to ShellCast
          </a>
        </div>
        
        <div class="footer-links">
          <a href="/about">About ShellCast</a>
          <a href="/feedback">Contact Us</a>
        </div>
      `;
    });
  }
}

// Check if this is a valid unsubscribe link (you might want to validate the token)
window.onload = function() {
  const urlParams = new URLSearchParams(window.location.search);
  const email = urlParams.get('email');
  const token = urlParams.get('token');
  
  if (!email || !token) {
    // If no email or token, show an error message
    const container = document.querySelector('.unsubscribe-container');
    container.innerHTML = `
      <div class="unsubscribe-header">
        <img src="/static/img/shellcast_logo.png" 
             alt="ShellCast logo" 
             class="unsubscribe-logo">
        <h1 class="h3">Invalid Unsubscribe Link</h1>
      </div>
      
      <div class="unsubscribe-message">
        <p class="mb-3">
          <strong>This unsubscribe link is invalid or has expired.</strong>
        </p>
        <p class="mb-0">
          Please contact us if you need help unsubscribing from our emails, 
          or use the unsubscribe link from a recent email.
        </p>
      </div>
      
      <div class="unsubscribe-actions">
        <a href="/" class="btn btn-cancel">
          Return to ShellCast
        </a>
      </div>
      
      <div class="footer-links">
        <a href="/about">About ShellCast</a>
        <a href="/feedback">Contact Us</a>
      </div>
    `;
  }
};
