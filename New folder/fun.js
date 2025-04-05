
const filePath = "./function_analysis.json";

async function loadJSON() {
    try {
        const response = await fetch(filePath);
        if (!response.ok) throw new Error("Failed to load JSON file.");

        const jsonData = await response.json();
        generateGraph(jsonData);
    } catch (error) {
        console.error("Error loading JSON:", error);
        alert("Failed to load JSON file. Check the path and try again.");
    }
}
var simulation;
// **************** Functional Part ****************
// Prepare graph data, including optional per-node or per-link styling if provided.
function prepareGraphData(jsonData) {
    const nodesMap = new Map();

    jsonData.uniqueFunctions.forEach(d => {
        if (!d.id) {
            console.error("Missing id for function:", d);
        } else {
            const styledNode = { id: d.id, name: d.name };
            styledNode.style = getNodeStyle(d);  // ⬅️ Apply logic-based style
            nodesMap.set(d.id, styledNode);
        }
    });

    let unknownCounter = 0;

    const links = jsonData.functionCalls.map(d => {
        let sourceId = d.callerId;
        let targetId = d.calleeId;

        if (sourceId === "UNKNOWN") {
            sourceId = `UNKNOWN_${unknownCounter++}`;
            if (!nodesMap.has(sourceId)) {
                const unknownNode = { id: sourceId, name: `Unknown Caller ${unknownCounter}` };
                unknownNode.style = getNodeStyle(d);
                nodesMap.set(sourceId, unknownNode);
            }
        }

        if (!nodesMap.has(targetId) && targetId !== undefined) {
            console.error("Missing target node:", targetId);
            targetId = `UNKNOWN_${unknownCounter++}`;
            const unknownNode = { id: targetId, name: `Unknown Function ${targetId}` };
            unknownNode.style = getNodeStyle(d);
            nodesMap.set(targetId, unknownNode);
        }

        if (nodesMap.has(sourceId) && nodesMap.has(targetId)) {
            const link = { source: sourceId, target: targetId };
            link.style = getLinkStyle(d);  // ⬅️ Apply logic-based style
            return link;
        } else {
            console.warn("Skipping invalid link between:", sourceId, targetId);
            return null;
        }
    }).filter(link => link !== null);

    const nodes = Array.from(nodesMap.values());
    return { nodes, links };
}


// **************** Visual Part ****************
// Build and style the graph. This version uses per-node and per-link styles.
function buildGraph(nodes, links, styling) {
    // Clear any existing SVG content.
    d3.select("svg").selectAll("*").remove();

    const width = window.innerWidth, height = 600;
//     d3.selectAll(".link")
//   .style("stroke", d => getLinkStyle(d).stroke)
//   .style("stroke-width", d => getLinkStyle(d).strokeWidth)
//   .style("stroke-dasharray", d => getLinkStyle(d).strokeDasharray || null);

    const svg = d3.select("svg")
                  .attr("width", width)
                  .attr("height", height);

    // Create a zoomable group inside the SVG.
    const zoomGroup = svg.append("g");

    // Setup zoom behavior.
    const zoom = d3.zoom()
        .scaleExtent([styling.minZoom, styling.maxZoom])
        .on("zoom", (event) => {
            zoomGroup.attr("transform", event.transform);
        });
    svg.call(zoom);

    // ********** Marker (Arrow) Styling - Global **********
    // These settings remain global, but you can move them into link styles if desired.
    zoomGroup.append("defs").append("marker")
        .attr("id", "arrow")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", styling.markerRefX) // Adjust marker position here.
        .attr("refY", 0)
        .attr("markerWidth", styling.markerWidth)
        .attr("markerHeight", styling.markerHeight)
        .attr("orient", "auto")
        .append("path")
        .attr("d", styling.markerPathD) // Change marker shape if needed.
        .attr("fill", styling.markerColor); // Marker color.

    // Create simulation forces.
    simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(styling.linkDistance))
        .force("charge", d3.forceManyBody().strength(styling.chargeStrength))
        .force("center", d3.forceCenter(width / 2, height / 2));

    // ********** Create Links (Edges) **********
    const link = zoomGroup.selectAll(".link")
        .data(links)
        .enter().append("line")
        .attr("class", "link")
        // Use per-link styling if available; otherwise fall back to defaults.
        .attr("stroke", d => (d.style && d.style.stroke) || styling.linkColor) // Edge color.
        .attr("stroke-width", d => (d.style && d.style.strokeWidth) || styling.linkStrokeWidth) // Edge thickness.
        .attr("marker-end", "url(#arrow)");

    // ********** Create Nodes **********
    const node = zoomGroup.selectAll(".node")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragStart)
            .on("drag", dragged)
            .on("end", dragEnd));

    // Append circles for nodes with per-node styling.
    node.append("circle")
        .attr("r", d => (d.style && d.style.radius) || styling.nodeRadius) // Node radius.
        .attr("fill", d => {
            // Check for per-node fill color; for UNKNOWN nodes, allow separate styling.
            if (d.style && d.style.fill) return d.style.fill;
            return d.id.toString().startsWith("UNKNOWN")
                   ? (d.style && d.style.unknownFill) || styling.unknownNodeColor
                   : styling.defaultNodeColor;
        })
        .on("mouseover", function(event, d) {
            // Use per-node hover color if available.
            d3.select(this).attr("fill", (d.style && d.style.hoverFill) || styling.nodeHoverColor);
        })
        .on("mouseout", function(event, d) {
            // Revert to per-node or default fill.
            d3.select(this).attr("fill", d => {
                if (d.style && d.style.fill) return d.style.fill;
                return d.id.toString().startsWith("UNKNOWN")
                       ? (d.style && d.style.unknownFill) || styling.unknownNodeColor
                       : styling.defaultNodeColor;
            });
        });

    // Append text labels for nodes.
    node.append("text")
        .attr("dy", styling.textDy) // Vertical offset for text labels.
        .text(d => d.name)
        .attr("fill", d => (d.style && d.style.textColor) || styling.textColor); // Text color.

    // Update positions on each tick of the simulation.
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // ********** Drag Event Handlers **********
    function dragStart(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragEnd(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    const minX = 0, maxX = 2500; // or custom values
const minY = 0, maxY = 1200; // or custom values

simulation.on("tick", () => {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node.attr("transform", d => {
        // Clamp the x and y values.
        d.x = Math.max(minX, Math.min(maxX, d.x));
        d.y = Math.max(minY, Math.min(maxY, d.y));
        return `translate(${d.x},${d.y})`;
    });
});
}
// Turn off repulsion by removing the 'charge' force.
function disableRepulsion() {
    simulation.force("charge", null);
    simulation.alpha(1).restart(); // Restart simulation to see changes immediately.
    console.log("Repulsion disabled.");
}

// Turn on repulsion by re-adding the 'charge' force with a given strength.
function enableRepulsion(chargeStrength) {
    simulation.force("charge", d3.forceManyBody().strength(chargeStrength));
    simulation.alpha(1).restart();
}

// Freeze all nodes by fixing their current positions.
function freezeNodes() {
    simulation.nodes().forEach(function(d) {
        d.fx = d.x;
        d.fy = d.y;
    });
}

// Unfreeze all nodes by releasing their fixed positions.
function unfreezeNodes() {
    simulation.nodes().forEach(function(d) {
        d.fx = null;
        d.fy = null;
    });
}

// Make a particular node immovable by fixing its current position.
function makeNodeImmovable(node) {
    node.fx = node.x;
    node.fy = node.y;
}

// Set a particular node movable again by releasing its fixed position.
function makeNodeMovable(node) {
    node.fx = null;
    node.fy = null;
}


// **************** Global Default Styling Configuration ****************
// This object provides default values in case per-node or per-link styles are not provided.
const styling = {
    // Zoom configuration.
    minZoom: 0.5,
    maxZoom: 3,

    // Marker (arrow) styling - global.
    markerRefX: 15,        // Marker reference point; adjust for positioning.
    markerWidth: 6,        // Marker width.
    markerHeight: 6,       // Marker height.
    markerPathD: "M0,-5L10,0L0,5", // Marker shape.
    markerColor: "#999",   // Marker color.

    // Link (edge) default styling.
    linkDistance: 120,     // Distance between linked nodes.
    linkColor: "#999",     // Default edge color.
    linkStrokeWidth: 2,    // Default edge thickness.

    // Node default styling.
    nodeRadius: 10,        // Default node radius.
    defaultNodeColor: "steelblue", // Default node fill color.
    unknownNodeColor: "red",       // Default fill for UNKNOWN nodes.
    nodeHoverColor: "orange",      // Default hover fill color.

    // Text styling for node labels.
    textDy: -15,           // Vertical offset for text labels.
    textColor: "black",    // Default text color.

    // Simulation forces.
    chargeStrength: -80   // Node repulsion strength.
};

// **************** Main Function ****************
// This is the entry point: it separates data processing from visual rendering.
function generateGraph(jsonData) {
    // Functional part: Prepare nodes and links (including per-element style if provided).
    const { nodes, links } = prepareGraphData(jsonData);
    console.log("Nodes Data:", nodes);

    // Visual part: Build the graph using both the per-element and default styling.
    buildGraph(nodes, links, styling);
    // disableRepulsion();
    // freezeNodes();
}

function getNodeStyle(node) {
    // Main function
    if (node.name === "main") {
        return {
            fill: "#66bb6a",         // Soft Emerald
            radius: 16,
            hoverFill: "#a5d6a7",    // Mint Green
            textColor: "#ffffff"
        };
    }

    // Inside a class
    if (node.parentClass && node.parentClass !== "") {
        return {
            fill: "#ec407a",         // Pastel Rose
            radius: 13,
            hoverFill: "#f48fb1",    // Light Rose
            textColor: "#ffffff"
        };
    }

    // Test file
    if (node.path && node.path.includes("/tests/")) {
        return {
            fill: "#ffca28",         // Light Amber
            radius: 12,
            hoverFill: "#fff59d",    // Cream Yellow
            textColor: "#000000"
        };
    }

    // Language-specific
    switch ((node.language || "").toLowerCase()) {
        case "python":
            return {
                fill: "#42a5f5",      // Soft Sky Blue
                radius: 11,
                hoverFill: "#90caf9", // Pale Blue
                textColor: "#000000"
            };
        case "java":
            return {
                fill: "#ffb74d",      // Fresh Mango
                radius: 11,
                hoverFill: "#ffe082", // Light Apricot
                textColor: "#000000"
            };
        case "cpp":
        case "c++":
            return {
                fill: "#ab47bc",      // Soft Violet
                radius: 11,
                hoverFill: "#ce93d8", // Lavender Mist
                textColor: "#000000"
            };
        case "javascript":
            return {
                fill: "#26a69a",      // Seafoam Green
                radius: 11,
                hoverFill: "#80cbc4", // Mint Mist
                textColor: "#000000"
            };
        default:
            return {
                fill: "#78909c",      // Cool Slate
                radius: 10,
                hoverFill: "#b0bec5", // Light Slate
                textColor: "#000000"
            };
    }
}



function getLinkStyle(link) {
    console.log("Link Data:", link);
    if (link.isInsideClass) {
        return {
            stroke: "#3f51b5", // blue
            strokeWidth: 2,
            strokeDasharray: "2,4"
        };
    }

    if (link.isInsideIfElseOrSwitch) {
        return {
            stroke: "#999",
            strokeWidth: 2,
            strokeDasharray: "6,4" // dashed
        };
    }

    if (link.isInsideLoopOrEnvironment) {
        return {
            stroke: "#999",
            strokeWidth: 2,
            strokeDasharray: "2,4" // dotted
        };
    }

    if (link.isInsideFunction) {
        return {
            stroke: "#555",
            strokeWidth: 2 // bold
        };
    }

    // default style
    return {
        stroke: "#aaa",
        strokeWidth: 2
    };
}





// Load the JSON file and generate the graph when the window loads.


window.onload = loadJSON;
// freezeNodes(); // Freeze nodes on load.
