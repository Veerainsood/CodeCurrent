import { spawn } from 'child_process';

function getDescription(id, task) {
    const py = spawn('python3', ['AIChatter.py', id.toString(), task.toString()]);

    py.stdout.on('data', (data) => {
        console.log(`✅ DeepSeek Result:\n${data.toString()}`);
    });

    py.stderr.on('data', (data) => {
        console.error(`❌ Python Error: ${data.toString()}`);
    });

    py.on('close', (code) => {
        if (code !== 0) {
            console.error(`⚠️ Python process exited with code ${code}`);
        }
    });
}

// Example usage
getDescription(8684, 1);  // Replace with actual ID and task



// updateDescriptionPanel