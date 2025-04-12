import { updateDescriptionPanel } from './fun.js';

async function fetchWithTimeout(url, timeout) {
    return Promise.race([
        fetch(url),
        new Promise(resolve => setTimeout(() => resolve('timeout'), timeout))
    ]);
}

async function getDescription(id, task) {
    console.log("Fetching description for ID:", id, "and task:", task);
    const url = `/api/desc/${id}/${task}`;

    // First request with 15s timeout
    let res = await fetchWithTimeout(url, 15000);
    if (res !== 'timeout') {
        const data = await res.json();
        if (data.output) {
            console.log("got the output 15");
            updateDescriptionPanel(id, data.output, task);
            return;
        }
    }

    // Second request with 20s timeout
    res = await fetchWithTimeout(url, 20000);
    if (res !== 'timeout') {
        const data = await res.json();
        if (data.output) {
            console.log("got the output 20");
            updateDescriptionPanel(id, data.output, task);
            return;
        }
    }

    // Timeout or no valid response
    updateDescriptionPanel(id, 'Timeout: No response received', task);
}

export { getDescription };
