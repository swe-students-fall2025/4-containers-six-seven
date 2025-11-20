const webcamButton = document.getElementById('webcamButton');
const webcamPreview = document.getElementById('webcamPreview');
const webcamCanvas = document.getElementById('webcamCanvas');

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

document.getElementById('submitButton').addEventListener('click', () => {
  const fileInput = document.getElementById('receiptUpload');
  const file = fileInput.files[0];
  const status = document.getElementById('statusMessage');

  const formData = new FormData();

  if (file) {
    formData.append('receipt', file);
  } else if (webcamPreview.srcObject) {
    const imageData = captureWebcamImage();
    formData.append('receipt_base64', imageData);
  } else {
    status.textContent = "Please upload a file or use the webcam.";
    return;
  }

  status.textContent = "Uploading...";

  fetch('/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    status.textContent = "Receipt processed: " + data.category;
  })
  .catch(error => {
    console.error("Upload error:", error);
    status.textContent = "Upload failed.";
  });
});