import express from 'express';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const port = 8000;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/desc/:id/:task', (req, res) => {
  console.log('Received request for description:', req.params);
  const { id, task } = req.params;
  const py = spawn('python3', ['AIChatter.py', id, task]);

  let result = '';

  py.stdout.on('data', (data) => {
    result += data.toString();
  });
  console.log(result);
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
