// Image upload
document.getElementById('imageForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  const filter = document.getElementById('filter').value;
  if (filter) {
    formData.append('filter', filter);
  }

  const response = await fetch('/detect-image', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  document.getElementById('output').innerText = JSON.stringify(result, null, 2);
});

// Video upload
document.getElementById('videoForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const formData = new FormData(this);

  const response = await fetch('/detect-video', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  document.getElementById('output').innerText = JSON.stringify(result, null, 2);
});
