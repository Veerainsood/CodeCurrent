// import { spawn } from 'child_process';
import {updateDescriptionPanel} from './fun.js';
async function getDescription(id, task) {
    console.log("Fetching description for ID:", id, "and task:", task);
    let output = null;
    let a = fetch(`/api/desc/${id}/${task}`);
    console.log(a);
    while (!output) {
        const res = await fetch(`/api/desc/${id}/${task}`);
        const data = await res.json();

        output = data.output;

        if (!output) {
            // Wait before trying again (e.g., every 1 second)
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    updateDescriptionPanel(id, output, 1);
}

// Example usage
// getDescription(8684, 1);  // Replace with actual ID and task


export { getDescription };
// updateDescriptionPanel