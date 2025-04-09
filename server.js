import express from 'express';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const port = 8000;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Serve static files from public
app.use(express.static(path.join(__dirname, 'public')));

// Serve JSON directly from root (no extra 'main')
app.get('/unique_functions_combined.json', (req, res) => {
  res.sendFile(path.join(__dirname, 'unique_functions_combined.json'));
});

app.get('/function_calls_combined.json', (req, res) => {
  res.sendFile(path.join(__dirname, 'function_calls_combined.json'));
});

// Python API route
app.get('/api/desc/:id/:task', (req, res) => {
  console.log('Received request for description:', req.params);
  const { id, task } = req.params;
  const py = spawn('python3', ['AIChatter.py', id, task]);

  let result = '';

  py.stdout.on('data', (data) => {
    result += data.toString();
  });

  py.stderr.on('data', (err) => {
    console.error('Python error:', err.toString());
  });

  py.on('close', (code) => {
    res.json({ success: true, output: result.trim(), code });
  });
});

app.listen(port, () => {
  console.log(`✅ Server running at http://localhost:${port}`);
});
