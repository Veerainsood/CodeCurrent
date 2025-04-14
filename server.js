import express from 'express';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const app = express();
const port = 8000;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Middleware to parse JSON if needed
app.use(express.json());

// Serve static files from public
app.use(express.static(path.join(__dirname, 'public')));


// Python API route to call AIChatter.py
app.get('/api/desc/:id/:task', async (req, res) => {
  console.log('📨 Received /api/desc request:', req.params);
  const { id, task } = req.params;

  try {
    const result = await new Promise((resolve, reject) => {
      const py = spawn('python3', ['AIChatter.py', id.toString(), task.toString()]);
      let result = '';
      let error = '';
      debugger;
      py.stdout.on('data', (data) => {
        result += data.toString();
        console.log("Got Description Data");
      });

      py.stderr.on('data', (data) => {
        error += data.toString();
      });

      py.on('close', (code) => {
        if (code !== 0) {
          console.error(`⚠️ Python process exited with code ${code}`);
          if (error) console.error(`Python Error: ${error}`);
          reject(new Error(error || `Exited with code ${code}`));
        } else {
          resolve(result.trim());
        }
      });
    });
    
    res.json({ success: true, output: result });
    console.log("returned promise");
  } catch (err) {
    console.error('Python error:', err);
    res.json({ success: false, output: null, error: err.toString() });
  }
});

// 🏁 Run runner.py ONCE when the server starts
const runner = spawn('python3', ['runner.py']);
let runnerReady = false;

runner.stdout.on('data', (data) => {
  console.log('🚀 runner.py output:', data.toString());
});

runner.stderr.on('data', (err) => {
  // console.error('runner.py error:', err.toString());
});

runner.on('close', (code) => {
  console.log(`🏁 runner.py finished with exit code ${code}`);
  runnerReady = true;
});

app.get('/api/runner-status', (req, res) => {
  res.json({ ready: runnerReady });
});


// Serve JSON directly from root (fix: use '/file' not './file')
app.get('/unique_functions_combined.json', (req, res) => {
  res.sendFile(path.join(__dirname, 'unique_functions_combined.json'));
});

app.get('/function_calls_combined.json', (req, res) => {
  res.sendFile(path.join(__dirname, 'function_calls_combined.json'));
});

// Start the Express server
app.listen(port, () => {
  console.log(`✅ Server running at http://localhost:${port}`);
});

