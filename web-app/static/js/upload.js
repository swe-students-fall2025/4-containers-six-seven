const webcamButton = document.getElementById('webcamButton');
const webcamPreview = document.getElementById('webcamPreview');
const webcamCanvas = document.getElementById('webcamCanvas');

// Check authentication on page load
document.addEventListener('DOMContentLoaded', async () => {
  const user = await checkAuthStatus();
  if (!user) {
    redirectToLogin('/upload');
  }
});

webcamButton.addEventListener('click', () => {
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      webcamPreview.srcObject = stream;
      webcamPreview.style.display = 'block';
    })
    .catch(err => {
      console.error("Webcam error:", err);
      document.getElementById('statusMessage').textContent = "Webcam access denied.";
    });
});

// Capture frame from video when submitting
function captureWebcamImage() {
  const context = webcamCanvas.getContext('2d');
  context.drawImage(webcamPreview, 0, 0, webcamCanvas.width, webcamCanvas.height);
  return webcamCanvas.toDataURL('image/png'); // base64 image
}

// Convert base64 data URL to Blob
function dataURLtoBlob(dataurl) {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)[1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new Blob([u8arr], { type: mime });
}

// Poll for receipt status
function pollReceiptStatus(receiptId, statusElement) {
  const maxAttempts = 60; // 60 attempts * 3 seconds = 3 minutes max
  let attempts = 0;

  const poll = () => {
    attempts++;
    if (attempts > maxAttempts) {
      statusElement.textContent = "Processing timeout. Please check receipt history.";
      return;
    }

    fetch(`/api/receipts/${receiptId}/status`, {
      credentials: 'include'
    })
      .then(response => {
        if (response.status === 401) {
          handleUnauthorized('/upload');
          return null;
        }
        return response.json();
      })
      .then(data => {
        if (!data) return; // Handled by redirect
        if (data.status === 'completed') {
          const merchant = data.merchant || 'Unknown';
          const category = data.category || 'Uncategorized';
          const total = data.total ? `$${data.total.toFixed(2)}` : 'N/A';
          statusElement.textContent = `Receipt processed! Merchant: ${merchant}, Category: ${category}, Total: ${total}`;
        } else if (data.status === 'failed') {
          statusElement.textContent = "Receipt processing failed. Please try again.";
        } else {
          // Still pending, poll again
          statusElement.textContent = `Processing... (attempt ${attempts})`;
          setTimeout(poll, 3000); // Poll every 3 seconds
        }
      })
      .catch(error => {
        console.error("Status poll error:", error);
        statusElement.textContent = "Error checking status. Please check receipt history.";
      });
  };

  poll();
}

document.getElementById('submitButton').addEventListener('click', () => {
  const fileInput = document.getElementById('receiptUpload');
  const file = fileInput.files[0];
  const status = document.getElementById('statusMessage');

  const formData = new FormData();

  if (file) {
    formData.append('file', file);
  } else if (webcamPreview.srcObject) {
    const imageData = captureWebcamImage();
    const blob = dataURLtoBlob(imageData);
    formData.append('file', blob, 'webcam-capture.png');
  } else {
    status.textContent = "Please upload a file or use the webcam.";
    return;
  }

  status.textContent = "Uploading...";

  fetch('/api/receipts/upload', {
    method: 'POST',
    body: formData,
    credentials: 'include'
  })
  .then(response => {
    if (response.status === 401) {
      handleUnauthorized('/upload');
      return null;
    }
    return response.json();
  })
  .then(data => {
    if (!data) return; // Handled by redirect
    
    if (data.receipt_id) {
      status.textContent = "Upload successful! Processing receipt...";
      // Start polling for status
      pollReceiptStatus(data.receipt_id, status);
    } else {
      status.textContent = "Upload failed: " + (data.error || "Unknown error");
    }
  })
  .catch(error => {
    console.error("Upload error:", error);
    status.textContent = "Upload failed. Please try again.";
  });
});