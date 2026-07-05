import axios from 'axios';

export function notFoundHandler(req, res) {
  res.status(404).json({
    error: 'Not Found',
    message: `Route not found: ${req.method} ${req.originalUrl}`,
  });
}

export function errorHandler(err, _req, res, _next) {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status || 502;
    res.status(status).json({
      error: 'AI Server Error',
      message: err.response?.data?.detail || err.response?.data?.message || err.message,
      details: err.response?.data || null,
    });
    return;
  }

  if (err?.statusCode) {
    res.status(err.statusCode).json({
      error: err.name || 'HttpError',
      message: err.message,
      details: err.details,
    });
    return;
  }

  if (err?.message?.includes('Unsupported CV file type')) {
    res.status(400).json({ error: 'Unsupported File', message: err.message });
    return;
  }

  if (err?.code === 'LIMIT_FILE_SIZE') {
    res.status(413).json({ error: 'File Too Large', message: 'Uploaded CV exceeds the configured size limit.' });
    return;
  }

  console.error(err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err?.message || 'Unexpected server error.',
  });
}
