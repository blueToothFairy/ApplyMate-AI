const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:3001';

function getHeaders() {
  const headers = {};
  const apiKey = import.meta.env.VITE_API_KEY;
  if (apiKey) {
    headers['x-api-key'] = apiKey;
  }
  return headers;
}

async function handleResponse(response) {
  if (!response.ok) {
    let message = 'API request failed';
    try {
      const errData = await response.json();
      message = errData.message || errData.error || message;
    } catch {
      try {
        const text = await response.text();
        if (text) message = text;
      } catch {}
    }
    throw new Error(message);
  }
  return response.json();
}

export async function createApplication(formData) {
  const response = await fetch(`${BASE_URL}/api/applications`, {
    method: 'POST',
    headers: getHeaders(), // Note: Do not set Content-Type header when using FormData; fetch sets it automatically with the boundary boundary.
    body: formData,
  });
  return handleResponse(response);
}

export async function getApplication(id) {
  const response = await fetch(`${BASE_URL}/api/applications/${id}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function generateApplication(id) {
  const response = await fetch(`${BASE_URL}/api/applications/${id}/generate`, {
    method: 'POST',
    headers: {
      ...getHeaders(),
      'Content-Type': 'application/json',
    },
  });
  return handleResponse(response);
}

export async function draftEmail(id, tone = 'professional, concise, internship-friendly') {
  const response = await fetch(`${BASE_URL}/api/applications/${id}/draft-email`, {
    method: 'POST',
    headers: {
      ...getHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tone }),
  });
  return handleResponse(response);
}

export async function approveApplication(id, feedback = '') {
  const response = await fetch(`${BASE_URL}/api/applications/${id}/approve`, {
    method: 'POST',
    headers: {
      ...getHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ feedback }),
  });
  return handleResponse(response);
}

export async function rejectApplication(id, feedback = '') {
  const response = await fetch(`${BASE_URL}/api/applications/${id}/reject`, {
    method: 'POST',
    headers: {
      ...getHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ feedback }),
  });
  return handleResponse(response);
}

export async function sendApplication(id) {
  const response = await fetch(`${BASE_URL}/api/applications/${id}/send`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function exportDocx(id) {
  const response = await fetch(`${BASE_URL}/api/applications/${id}/export/docx`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || 'Failed to export DOCX');
  }
  return response.blob();
}

export async function exportPdf(id) {
  const response = await fetch(`${BASE_URL}/api/applications/${id}/export/pdf`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || 'Failed to export PDF');
  }
  return response.blob();
}

export async function checkBackendHealth() {
  const response = await fetch(`${BASE_URL}/health`, {
    method: 'GET',
  });
  return handleResponse(response);
}
