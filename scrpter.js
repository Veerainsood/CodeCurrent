const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const util = require('util');

const execPromise = util.promisify(exec);

const containerName = 'cpp_parser_container';
const imageName = 'veerain/cplusplusparser';
const mountDir = process.cwd(); // Current directory
const containerMountPath = '/src';
const outputJson = 'file.json';

async function isContainerRunning(name) {
  const { stdout } = await execPromise(`docker ps --filter "name=${name}" --format "{{.Names}}"`);
  return stdout.trim() === name;
}

async function startContainer() {
  const runCmd = `docker run -dit --name ${containerName} -v "${mountDir}":"${containerMountPath}" ${imageName} bash`;
  await execPromise(runCmd);
  console.log(`Started container: ${containerName}`);
}

async function runGenerator() {
  // Run generator.py for all cpp files inside container, create file.json inside /src
  const dockerCmd = `docker exec ${containerName} bash -c "cd /ast && > file.json; for f in *.cpp *.cc *.cxx *.C 2>/dev/null; do python3 generator.py \\\"\$f\\\" temp_output.json && cat temp_output.json >> file.json; done"`;
  await execPromise(dockerCmd);
  console.log(`Generated ${outputJson} inside current directory.`);
}

async function stopAndRemoveContainer() {
  await execPromise(`docker stop ${containerName}`);
  await execPromise(`docker rm ${containerName}`);
  console.log(`Stopped and removed container: ${containerName}`);
}

async function main() {
  try {
    const running = await isContainerRunning(containerName);
    if (!running) {
      console.log('Starting container...');
      await startContainer();
    } else {
      console.log('Container already running.');
    }

    console.log('Running generator on all C++ files...');
    await runGenerator();

    console.log('Cleaning up...');
    await stopAndRemoveContainer();

    console.log(`✅ Done. Check ${outputJson} in your current folder.`);
  } catch (err) {
    console.error('Something went wrong:', err);
  }
}

main();
