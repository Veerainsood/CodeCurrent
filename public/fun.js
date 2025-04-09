import { createPanel, reactivatePanel } from "./HeaderAndPanel.js";
import { getDescription } from "./getInfo.js";
// import uniqueFunctionsData from '../unique_functions_combined.json';
// import functionCallsData from '../function_calls_combined.json';
let jsonData;
const uniqueFunctionsPath = "/unique_functions_combined.json";
const functionCallsPath = "/function_calls_combined.json";

// Asynchronously load both JSON files and combine the data into one object.
async function loadJSON() {
    try {
        // Fetch both JSON files concurrently.
        const [uniqueFunctionsResponse, functionCallsResponse] = await Promise.all([
            fetch(uniqueFunctionsPath),
            fetch(functionCallsPath)
        ]);

        // Verify that both responses are OK.
        if (!uniqueFunctionsResponse.ok || !functionCallsResponse.ok) {
            throw new Error("Failed to load one or more JSON files.");
        }

        // Parse JSON from both responses.
        const uniqueFunctions = await uniqueFunctionsResponse.json();
        const functionCalls = await functionCallsResponse.json();

        // Combine the JSON data into one object.
        jsonData = {
            uniqueFunctions,   // from main/unique_functions_combined.json
            functionCalls      // from main/function_calls_combined.json
        };

        // Pass the combined data to your graph generation function.
        generateGraph(jsonData);
    } catch (error) {
        console.error("Error loading JSON:", error);
        alert("Failed to load JSON files. Check the paths and try again.");
    }
}

// Example placeholders for style logic (customize as needed).
// function getNodeStyle(d) {
//     return { color: d.language === 'C++' ? 'blue' : 'gray' };
// }

// function getLinkStyle(d) {
//     return { stroke: d.is_foreign_call ? 'red' : 'green' };
// }

// Prepare the graph data using the updated JSON structure and property names.
function prepareGraphData(jsonData) { 
    const nodesMap = new Map(); 

    // Use the data from uniqueFunctions.
    jsonData.uniqueFunctions.forEach(d => {
        if (!d.id) {
            console.error("Missing id for function:", d);
        } else {
            const styledNode = { 
                id: d.id, 
                name: d.name,
                file: d.file,
                language: d.language,
                details: d  // store complete details for additional panels or info
            };
            styledNode.style = getNodeStyle(d);  // Apply logic-based style for nodes
            nodesMap.set(d.id, styledNode);
        }
    });

    // Counter for unknown nodes.
    let unknownCounter = 0;
    const links = jsonData.functionCalls.map(d => {
        // Use the updated property names: caller_id and callee_id.
        let sourceId = d.caller_id;
        let targetId = d.callee_id;
        if(!sourceId) {
            console.log("Missing source node:", d);
        }

        // If the caller is explicitly marked as "UNKNOWN", create an unknown node.
        if (sourceId === "UNKNOWN") {
            sourceId = `UNKNOWN_${unknownCounter++}`;
            if (!nodesMap.has(sourceId)) {
                const unknownNode = { id: sourceId, name: `Unknown Caller ${unknownCounter}` };
                unknownNode.style = getNodeStyle(d);
                nodesMap.set(sourceId, unknownNode);
            }
        }

        // If the target does not exist in nodesMap, create an unknown node.
        if (!nodesMap.has(targetId) && targetId !== undefined) {
            console.error("Missing target node:", targetId);
            targetId = `UNKNOWN_${unknownCounter++}`;
            const unknownNode = { id: targetId, name: `Unknown Function ${targetId}` };
            unknownNode.style = getNodeStyle(d);
            nodesMap.set(targetId, unknownNode);
        }

        // Only add the link if both source and target nodes exist.
        
        if (nodesMap.has(sourceId) && nodesMap.has(targetId)) {
            const link = { source: sourceId, target: targetId };
            link.style = getLinkStyle(d);  // Apply style logic for links
            return link;
        } else {
            console.log("Skipping invalid link between:", sourceId, targetId);
            // console.log(nodesMap);
            return null;
        }
    }).filter(link => link !== null);

    const nodes = Array.from(nodesMap.values());
    return { nodes, links };
}


let GeneratedSidePanel = [];
let jsonDataList = [];

let simulationCount = 0;
let simulations = {}; // Store sim instances
let currentSimulationId = 0;
let currentID = 0;





// Suppose that you have loaded the two JSON files, for instance:
// import uniqueFunctionsData from '../unique_functions_combined.json';
// import functionCallsData from '../function_calls_combined.json';

// // Combine the arrays into one object to pass to the prepareGraphData function.
// const graphData = {
//     uniqueFunctions: uniqueFunctionsData,   // from main/unique_functions_combined.json
//     functionCalls: functionCallsData          // from main/function_calls_combined.json
// };

// function getNodeStyle(d) {
//     // Your style logic here; for example:
//     return { color: d.language === 'C++' ? 'blue' : 'gray' };
// }

// function getLinkStyle(d) {
//     // Style logic for links, possibly based on flags in d:
//     return { stroke: d.is_foreign_call ? 'red' : 'green' };
// }

// function prepareGraphData(jsonData) {
//     const nodesMap = new Map(); 

//     jsonData.uniqueFunctions.forEach(d => {
//         if (!d.id) {
//             console.error("Missing id for function:", d);
//         } else {
//             const styledNode = { 
//                 id: d.id, 
//                 name: d.name,
//                 file: d.file,
//                 language: d.language,
//                 details: d  // store the complete details for later use (e.g., in a panel)
//             };
//             styledNode.style = getNodeStyle(d);  // Apply logic-based node style
//             nodesMap.set(d.id, styledNode);
//         }
//     });

//     // We'll use a counter for unknown nodes
//     let unknownCounter = 0;
//     const links = jsonData.functionCalls.map(d => {
//         // Use d.caller_id and d.callee_id (adjusted based on your new JSON data)
//         let sourceId = d.caller_id;
//         let targetId = d.callee_id;

//         if (sourceId === "UNKNOWN") {
//             sourceId = `UNKNOWN_${unknownCounter++}`;
//             if (!nodesMap.has(sourceId)) {
//                 const unknownNode = { 
//                     id: sourceId, 
//                     name: `Unknown Caller ${unknownCounter}` 
//                 };
//                 unknownNode.style = getNodeStyle(d);
//                 nodesMap.set(sourceId, unknownNode);
//             }
//         }

//         if (!nodesMap.has(targetId) && targetId !== undefined) {
//             console.error("Missing target node:", targetId);
//             targetId = `UNKNOWN_${unknownCounter++}`;
//             const unknownNode = { 
//                 id: targetId, 
//                 name: `Unknown Function ${targetId}` 
//             };
//             unknownNode.style = getNodeStyle(d);
//             nodesMap.set(targetId, unknownNode);
//         }

//         // Only add a link if both nodes exist
//         if (nodesMap.has(sourceId) && nodesMap.has(targetId)) {
//             const link = { source: sourceId, target: targetId };
//             link.style = getLinkStyle(d);  // Apply logic-based link style
//             return link;
//         } else {
//             console.warn("Skipping invalid link between:", sourceId, targetId);
//             return null;
//         }
//     }).filter(link => link !== null);

//     const nodes = Array.from(nodesMap.values());
//     return { nodes, links };
// }

// // Example usage:
// const graph = prepareGraphData(graphData);
// console.log("Graph nodes:", graph.nodes);
// console.log("Graph links:", graph.links);

function buildGraph(nodes, links, styling) {
    clearSVG();
    const svg = setupSVGCanvas();
    const zoomGroup = setupZoom(svg, styling);
    const { linksLayer, modulesLayer } = createGraphLayers(zoomGroup);
    const legend = createLanguageLegend(svg, nodes, styling);
    simulations[currentSimulationId] = setupSimulation(nodes, links, styling);

    const { tempNodes, link, moduleGroups } = drawGraphElements({
        svg,
        zoomGroup,
        links,
        nodes,
        styling,
        linksLayer,
        modulesLayer
    });

    defineArrowMarkers(zoomGroup, styling);
    defineDropShadow(svg);

    handleSimulationTicks(simulations, tempNodes, link, moduleGroups, styling);
}

// --------------------------------------------
// Configuration Values (Easy to Change)
// --------------------------------------------

const graphConfig = {
    svgWidth: 1500,
    svgHeight: 800,
    tooltipOffset: { x: 5, y: 5 },
    fontSize: 12,
};

// --------------------------------------------
// Step-by-Step Helper Functions
// --------------------------------------------

function clearSVG() {
    d3.select("svg").selectAll("*").remove();
}

function setupSVGCanvas() {
    d3.selectAll(".link.test")
    .style("filter", "url(#glow)");

    const s = d3.select("svg")
        .attr("width", graphConfig.svgWidth)
        .attr("height", graphConfig.svgHeight);

    defineGlowFilter(s);

    return s;
}

function setupZoom(svg, styling) {
    const zoomGroup = svg.append("g");
    const zoom = d3.zoom()
        .scaleExtent([styling.minZoom, styling.maxZoom])
        .on("zoom", (event) => {
            zoomGroup.attr("transform", event.transform);
        });
    svg.call(zoom);
    return zoomGroup;
}

function createGraphLayers(zoomGroup) {
    return {
        linksLayer: zoomGroup.append("g").attr("class", "links-layer"),
        modulesLayer: zoomGroup.append("g").attr("class", "modules-layer"),
    };
}
function createLanguageLegend(svg, nodes, styling) {
    const languages = Array.from(new Set(nodes.map(n => n.language)));
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(20,20)");

    languages.forEach((lang, i) => {
        // Use CSS.escape to safely escape any special characters in the language string.
        const safeLang = CSS.escape(lang);

        const row = legend.append("g")
            .attr("transform", `translate(0, ${i * 30})`)
            .style("cursor", "pointer")
            .on("click", () => {
                // Safely select nodes using the escaped language string.
                const selector = `.node.language-${safeLang}`;
                // Toggle opacity: if it's at full opacity, fade it; else, restore it.
                const currentOpacity = d3.selectAll(selector).style("opacity");
                const visible = currentOpacity === "" || currentOpacity === "1";
                d3.selectAll(selector)
                  .transition().duration(500)
                  .style("opacity", visible ? 0.2 : 1);
            });

        // Make the legend square have rounded corners and a subtle drop shadow.
        row.append("rect")
            .attr("width", 20)
            .attr("height", 20)
            .attr("rx", 4) // Rounded corners.
            .attr("ry", 4)
            .attr("fill", styling.languageColors[lang] || styling.defaultNodeColor)
            .attr("stroke", "#fff")
            .attr("stroke-width", 1)
            .style("filter", "drop-shadow(2px 2px 2px rgba(0,0,0,0.3))");

        row.append("text")
            .attr("x", 30)
            .attr("y", 15)
            .attr("fill", styling.textColor || "#ffffff")
            .text(lang)
            .style("font-size", styling.fontSize || "14px")
            .style("font-family", "sans-serif");
    });

    return legend;
}


function setupSimulation(nodes, links, styling) {
    return d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(styling.linkDistance))
        .force("charge", d3.forceManyBody()
            .strength(styling.chargeStrength)
            .distanceMax(styling.chargeDistanceMax))
        .force("center", d3.forceCenter(graphConfig.svgWidth / 2, graphConfig.svgHeight / 2));
}

// Ensure this is defined before drawing graph elements
function getNodeFill(d, styling) {
    return d.style?.fill ||
        (d.id.toString().startsWith("UNKNOWN")
            ? d.style?.unknownFill || styling.unknownNodeColor
            : styling.languageColors[d.language] || styling.defaultNodeColor);
}

function drawGraphElements({ svg, zoomGroup, links, nodes, styling, linksLayer, modulesLayer }) {
    // Draw links.
    const link = linksLayer.selectAll(".link")
        .data(links)
        .enter().append("line")
        .attr("class", "link animated") // <- add 'animated' class
        .attr("stroke", d => (d.style?.stroke) || styling.linkColor)
        .attr("stroke-width", d => (d.style?.strokeWidth) || styling.linkStrokeWidth)
        .attr("marker-end", "url(#arrow)")
        .attr("stroke-dasharray", d => (d.style?.strokeDasharray) || null); // Ensure dash pattern

    // link.attr("stroke-dasharray", "5,5")
    //     .attr("stroke-dashoffset", 1000)
    //     .transition()
    //     .duration(2000)
    //     .ease(d3.easeLinear)
    //     .attr("stroke-dashoffset", 0);

    // Group nodes by file.
    const fileGroups = d3.group(nodes, d => d.file || "unknown");
    // Declare moduleGroups as a Map to store module groups.
    const moduleGroups = new Map();

    // Create a module group for each file.
    Array.from(fileGroups.entries()).forEach(([file, nodesInModule], i) => {
        const group = modulesLayer.append("g")
            .attr("class", "module-group")
            .attr("data-file", file);
        // group.append("rect")
        //     .attr("class", "module-bg")
        //     .attr("fill", styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length])
        //     .attr("fill-opacity", 0.1)
        //     .attr("stroke", styling.moduleBorderColor || styling.groupColors[i % styling.groupColors.length])
        //     .attr("stroke-dasharray", "4 2")
        //     .style("pointer-events", "none")
        //     // Creative: Animate a subtle background gradient effect.
        //     .transition().duration(2000)
        //     .ease(d3.easeLinear)
        //     .attrTween("fill", () => {
        //         // Create an interpolator between two colors.
        //         return d3.interpolateRgb(styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length], "#f0f0f0");
        //     })
        //     .on("end", function() {
        //         d3.select(this).attr("fill", styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length]);
        //     });
        moduleGroups.set(file, group);
    });

    const tempNodes = [];
    
    // Iterate through nodes and append each to its corresponding module group.
    nodes.forEach(d => {
        
        const fileKey = d.file || "unknown";
        let group = moduleGroups.get(fileKey);
        if (!group) {
            // Create a new group if one doesn't exist for this file.
            group = modulesLayer.append("g")
                .attr("class", "module-group")
                .attr("data-file", fileKey);
            // group.append("rect")
            //     .attr("class", "module-bg")
            //     .attr("fill", styling.moduleBgColor || styling.defaultModuleColor || "#ccc")
            //     .attr("fill-opacity", 0.1)
            //     .attr("stroke", styling.moduleBorderColor || styling.defaultModuleColor || "#ccc")
            //     .attr("stroke-dasharray", "4 2")
            //     .style("pointer-events", "none");
            moduleGroups.set(fileKey, group);
        }

        const node = group.append("g")
            .datum(d)
            .attr("class", `node language-${d.language}`)
            .attr("data-file", d.file)
            // .attr("data-return-type", d.details.returnType || "unknown")
            // .attr("data-class-name", d.details.parentClass || "unknown")
            // .attr("data-function-name", d.details.parentFunction || "unknown")
            // .attr("data-parameters", d.details.parameters || "unknown")
            // .attr("data-path", d.details.path || "unknown")
            .attr("filter", "url(#drop-shadow)")
            .call(d3.drag()
                .on("start", dragStart)
                .on("drag", dragged)
                .on("end", dragEnd));

        // Append circle with creative enhancements.
        node.append("circle")
            .attr("r", d.style?.radius || styling.nodeRadius)
            .attr("fill", getNodeFill(d, styling))
            .on("mouseover", function(event, hoveredNode) {
                // Add a glowing effect on hover.
                d3.select(this)
                    .attr("fill", hoveredNode.style?.hoverFill || styling.nodeHoverColor)
                    .transition().duration(300)
                    .attr("filter", "url(#glow)");
            
                // Highlight only directly connected links.
                link
                    .style("opacity", 0) // Hide all links first
                    .filter(l => l.source.id === hoveredNode.id || l.target.id === hoveredNode.id) // Keep only connected ones
                    .transition().duration(200)
                    .attr("stroke", l => l.style?.stroke || styling.highlightLinkColor)
                    .style("opacity", 1); // Show only connected links
            
                showTooltip(event, hoveredNode);
            })
            .on("mouseout", function(event, hoveredNode) {
                // Remove the glow on mouseout.
                d3.select(this)
                    .attr("fill", getNodeFill(hoveredNode, styling))
                    .attr("filter", null);

                link
                    .transition().duration(200)
                    .attr("stroke", l => l.style?.stroke || styling.linkColor)
                    .style("opacity", 1);

                d3.selectAll(".tooltip").remove();
                hideTooltip(event, hoveredNode);
            })
            .on("click", (event, d) => {
                // Creative: Add a pulse animation on click.
                const clickX = event.clientX;
                const clickY = event.clientY;
                const circle = d3.select(event.currentTarget);
                circle.transition()
                    .duration(150)
                    .attr("r", (d.style?.radius || styling.nodeRadius) * 1.2)
                    .transition()
                    .duration(150)
                    .attr("r", d.style?.radius || styling.nodeRadius);

                // Update a contextual info panel (assume updateInfoPanel exists).
                // updateInfoPanel(d);
                clicked(d, d.id, clickX, clickY);
            });

        // Append node label.
        node.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", -(d.style?.radius || styling.nodeRadius) - 4)
            .text(d.name)
            .attr("fill", "#ffffff")
            .style("font-size", `${graphConfig.fontSize}px`);

        // Creative: Optionally add an icon (if provided) to represent node type.
        if (d.icon) {
            
            node.append("image")
                .attr("xlink:href", d.icon)
                .attr("width", 16)
                .attr("height", 16)
                .attr("x", -(16 / 2))
                .attr("y", -(d.style?.radius || styling.nodeRadius) - 20);
        }
        
        tempNodes.push(node);
    });
    setupSearch(styling, svg, simulations, nodes, link); 
    return { tempNodes, link, moduleGroups };
}
function drawGraphElements2({ svg, zoomGroup, links, nodes, styling, linksLayer, modulesLayer }) {
    // Draw links.
    const link = linksLayer.selectAll(".link")
        .data(links)
        .enter().append("line")
        .attr("class", "link animated") // <- add 'animated' class
        .attr("stroke", d => (d.style?.stroke) || styling.linkColor)
        .attr("stroke-width", d => (d.style?.strokeWidth) || styling.linkStrokeWidth)
        .attr("marker-end", "url(#arrow)")
        .attr("stroke-dasharray", d => (d.style?.strokeDasharray) || "5,5"); // Ensure dash pattern

    link.attr("stroke-dasharray", "5,5")
        .attr("stroke-dashoffset", 1000)
        .transition()
        .duration(20)
        .ease(d3.easeLinear)
        .attr("stroke-dashoffset", 0);
      

    // Group nodes by file.
    const fileGroups = d3.group(nodes, d => d.file || "unknown");
    // Declare moduleGroups as a Map to store module groups and state.
    const moduleGroups = new Map();

    // Create a module group for each file.
    Array.from(fileGroups.entries()).forEach(([file, nodesInModule], i) => {
        const group = modulesLayer.append("g")
            .attr("class", "module-group")
            .attr("data-file", file)
            .attr("data-collapsed", "false");

        const bg = group.append("rect")
            .attr("class", "module-bg")
            .attr("fill", styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length])
            .attr("fill-opacity", 0.1)
            .attr("stroke", styling.moduleBorderColor || styling.groupColors[i % styling.groupColors.length])
            .attr("stroke-dasharray", "4 2")
            .style("pointer-events", "all")
            .on("click", function() {
                // Toggle collapse state.
                const isCollapsed = group.attr("data-collapsed") === "true";
                group.attr("data-collapsed", !isCollapsed);
                // Use the correct selection property (nodeContainer) for showing/hiding.
                moduleData.nodeContainer.style("display", isCollapsed ? "block" : "none");
                moduleData.moduleLabel.style("display", isCollapsed ? "block" : "none");
            })
            .transition().duration(2000)
            .ease(d3.easeLinear)
            .attrTween("fill", () => d3.interpolateRgb(
                styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length],
                "#f0f0f0"
            ))
            .on("end", function() {
                d3.select(this).attr("fill", styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length]);
            });

        // Container for nodes inside the module.
        const nodeContainer = group.append("g").attr("class", "module-nodes");

        // Label for collapsed module.
        const moduleLabel = group.append("text")
            .attr("class", "module-label")
            .attr("x", 10)
            .attr("y", 20)
            .attr("fill", styling.textColor)
            .style("font-size", "14px")
            .style("display", "none")
            .text(`${file} (${nodesInModule.length})`);

        // Save selections in a single object for this module.
        moduleGroups.set(file, { group, nodeContainer, moduleLabel });
    });

    const tempNodes = [];

    // Create a radial gradient definition for nodes.
    const defs = svg.append("defs");
    defs.append("radialGradient")
        .attr("id", "nodeGradient")
        .selectAll("stop")
        .data([
            { offset: "0%", color: "#fff" },
            { offset: "100%", color: styling.nodeColor || "#69b3a2" }
        ])
        .enter().append("stop")
        .attr("offset", d => d.offset)
        .attr("stop-color", d => d.color);

    // Iterate through nodes and append each to its corresponding module group.
    nodes.forEach(d => {
        const fileKey = d.file || "unknown";
        let moduleData = moduleGroups.get(fileKey);
        if (!moduleData) {
            // Create a new module if it doesn't exist.
            moduleData = {
                group: modulesLayer.append("g")
                    .attr("class", "module-group")
                    .attr("data-file", fileKey)
                    .attr("data-collapsed", "false"),
                nodeContainer: modulesLayer.append("g").attr("class", "module-nodes"),
                moduleLabel: modulesLayer.append("text")
                    .attr("class", "module-label")
                    .attr("x", 10)
                    .attr("y", 20)
                    .attr("fill", styling.textColor)
                    .style("font-size", "14px")
                    .style("display", "none")
            };
            moduleGroups.set(fileKey, moduleData);
        }
        const { nodeContainer } = moduleData;

        const node = nodeContainer.append("g")
            .datum(d)
            .attr("class", `node language-${d.language}`)
            .attr("filter", "url(#drop-shadow)")
            .call(d3.drag()
                .on("start", dragStart)
                .on("drag", dragged)
                .on("end", dragEnd));

        // Use a function expression so that 'this' points to the circle element.
        node.append("circle")
            .attr("r", d.style?.radius || styling.nodeRadius)
            .attr("fill", "url(#nodeGradient)")
            .on("mouseover", function(event, hoveredNode) {
                const newColor = hoveredNode.color || hoveredNode.style?.hoverFill || styling.nodeHoverColor || "#ffcc00";
                d3.select(this)
                    .transition().duration(300)
                    .attr("fill", newColor)
                    .attr("r", (d.style?.radius || styling.nodeRadius) * 1.1);
                link
                    .transition().duration(200)
                    .attr("stroke", l =>
                        (l.source.id === hoveredNode.id || l.target.id === hoveredNode.id)
                            ? styling.highlightLinkColor
                            : l.style?.stroke || styling.linkColor
                    )
                    .style("opacity", l =>
                        (l.source.id === hoveredNode.id || l.target.id === hoveredNode.id)
                            ? 1
                            : 0
                    );
                showEnhancedTooltip(event, hoveredNode);
            })
            .on("mouseout", function(event, hoveredNode) {
                d3.select(this)
                    .transition().duration(300)
                    .attr("fill", "url(#nodeGradient)")
                    .attr("r", d.style?.radius || styling.nodeRadius);
                link
                    .transition().duration(200)
                    .attr("stroke", l => l.style?.stroke || styling.linkColor)
                    .style("opacity", 1);
                d3.selectAll(".tooltip").remove();
            })
            .on("click", function(event, d) {
                // Use function expression so that 'this' is the clicked circle.
                const clickX = event.clientX;
                const clickY = event.clientY;
                const circle = d3.select(this);
                circle.transition()
                    .duration(150)
                    .attr("r", (d.style?.radius || styling.nodeRadius) * 1.2)
                    .attr("fill", d.color || styling.nodeClickColor || "#ff6600")
                    .transition()
                    .duration(150)
                    .attr("r", d.style?.radius || styling.nodeRadius)
                    .attr("fill", "url(#nodeGradient)");
                // updateInfoPanel(d);
                clicked(d, d.id, clickX, clickY);  // Call your custom function with node id and click position
            })
            .on("contextmenu", function(event, d) {
                event.preventDefault();
                showCustomContextMenu(event, d);
            });

        // Append node label.
        node.append("text")
            .attr("class", "node-label")
            .attr("text-anchor", "middle")
            .attr("dy", -(d.style?.radius || styling.nodeRadius) - 4)
            .text(d.name)
            .attr("fill", d.style?.textColor || styling.textColor)
            .style("font-size", `${graphConfig.fontSize}px`)
            .style("opacity", 0)
            .transition().duration(500)
            .style("opacity", 1);

        // Append extra text for key properties.
        node.append("text")
            .attr("class", "node-extra")
            .attr("text-anchor", "middle")
            .attr("dy", (d.style?.radius || styling.nodeRadius) + 14)
            .text(d.color ? `Color: ${d.color}` : "")
            .attr("fill", d.style?.textColor || styling.textColor)
            .style("font-size", "12px")
            .style("opacity", 0)
            .transition().delay(300)
            .duration(500)
            .style("opacity", 1);

        // Optionally add an icon if provided.
        if (d.icon) {
            node.append("image")
                .attr("xlink:href", d.icon)
                .attr("width", 16)
                .attr("height", 16)
                .attr("x", -8)
                .attr("y", -(d.style?.radius || styling.nodeRadius) - 20);
        }

        tempNodes.push(node);
    });

    return { tempNodes, link, moduleGroups };
}


/* Helper functions (you will need to implement these):
   - dragStart, dragged, dragEnd: for node dragging functionality.
   - showEnhancedTooltip(event, hoveredNode): displays a tooltip with extra details.
   - updateInfoPanel(d): updates a side panel with node details.
   - clicked(nodeId): handles node click events.
   - showCustomContextMenu(event, d): displays a custom context menu at the pointer location.
*/

// Example implementation for enhanced tooltip.
function showEnhancedTooltip(event, node) {
    const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("pointer-events", "none")
        .style("background", "rgba(0, 0, 0, 0.7)")
        .style("color", "#fff")
        .style("padding", "5px 10px")
        .style("border-radius", "4px")
        .style("opacity", 0);
    
    // Show additional key properties in the tooltip.
    tooltip.html(`<strong>${node.name}</strong><br>ID: ${node.id}<br>Type: ${node.type || "N/A"}<br>Color: ${node.color || "Default"}`)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY + 10) + "px")
        .transition().duration(200)
        .style("opacity", 1);
}

// Example implementation for custom context menu.
function showCustomContextMenu(event, node) {
    // Remove any existing custom menus.
    d3.selectAll(".custom-context-menu").remove();

    // Create a menu container.
    const menu = d3.select("body").append("div")
        .attr("class", "custom-context-menu")
        .style("position", "absolute")
        .style("background", "#fff")
        .style("border", "1px solid #ccc")
        .style("padding", "5px")
        .style("border-radius", "4px")
        .style("box-shadow", "0 2px 5px rgba(0,0,0,0.2)")
        .style("left", event.pageX + "px")
        .style("top", event.pageY + "px");

    // Add menu items.
    menu.append("div")
        .attr("class", "menu-item")
        .text("Isolate Node")
        .on("click", () => { 
            isolateNode(node);
            menu.remove();
        });
    
    menu.append("div")
        .attr("class", "menu-item")
        .text("View Details")
        .on("click", () => {
            // updateInfoPanel(node);
            menu.remove();
        });
    
    // Remove menu when clicking elsewhere.
    d3.select("body").on("click.context-menu", function() {
        menu.remove();
    });
}

// Placeholder for node isolation.
function isolateNode(node) {
    console.log("Isolating node", node.id);
    // Implement your isolation logic here.
}



// function drawGraphElements({ svg, zoomGroup, links, nodes, styling, linksLayer, modulesLayer }) {
//     const link = linksLayer.selectAll(".link")
//         .data(links)
//         .enter().append("line")
//         .attr("class", "link")
//         .attr("stroke", d => (d.style?.stroke) || styling.linkColor)
//         .attr("stroke-width", d => (d.style?.strokeWidth) || styling.linkStrokeWidth)
//         .attr("marker-end", "url(#arrow)")
//         .attr("stroke-dasharray", d => (d.style?.strokeDasharray) || null);

//     const fileGroups = d3.group(nodes, d => d.file);
//     const moduleGroups = new Map();

//     Array.from(fileGroups.entries()).forEach(([file, nodesInModule], i) => {
//         const group = modulesLayer.append("g").attr("class", "module-group").attr("data-file", file);
//         group.append("rect")
//             .attr("class", "module-bg")
//             .attr("fill", styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length])
//             .attr("fill-opacity", 0.1)
//             .attr("stroke", styling.moduleBorderColor || styling.groupColors[i % styling.groupColors.length])
//             .attr("stroke-dasharray", "4 2");
//         moduleGroups.set(file, group);
//     });
//     // Create a background rectangle for each module group to act as a container.
//     // moduleGroups.forEach((group, file) => {
//     //     const nodesInModule = group.selectAll(".node").data(nodes.filter(n => n.file === file));
//     //     const minX = d3.min(nodesInModule, n => n.x) - styling.groupPadding;
//     //     const minY = d3.min(nodesInModule, n => n.y) - styling.groupPadding;
//     //     const maxX = d3.max(nodesInModule, n => n.x) + styling.groupPadding;
//     //     const maxY = d3.max(nodesInModule, n => n.y) + styling.groupPadding;
//     //     group.append("rect")
//     //         .attr("class", "module-bg")
//     //         .attr("x", minX)
//     //         .attr("y", minY)
//     //         .attr("width", maxX - minX + styling.groupPadding * 2)
//     //         .attr("height", maxY - minY + styling.groupPadding * 2)
//     //         .attr("fill", styling.groupColors[i % styling.groupColors.length])
//     //         .attr("fill-opacity", 0.1)
//     //         .attr("stroke", styling.groupColors[i % styling.groupColors.length])
//     //         .attr("stroke-width", 1)
//     //         .attr("stroke-dasharray", "4 2");
//     // });
//     const tempNodes = [];

// nodes.forEach(d => {
//     const group = moduleGroups.get(d.file);
//     const node = group.append("g")
//         .datum(d)
//         .attr("class", `node language-${d.language}`)
//         .attr("filter", "url(#drop-shadow)")
//         .call(d3.drag()
//             .on("start", dragStart)
//             .on("drag", dragged)
//             .on("end", dragEnd));

//     node.append("circle")
//         .attr("r", d.style?.radius || styling.nodeRadius)
//         .attr("fill", getNodeFill(d))
//         .on("mouseover", function(event) {
//             d3.select(this).attr("fill", d.style?.hoverFill || styling.nodeHoverColor);
//             link.filter(l => l.source.id === d.id || l.target.id === d.id)
//                 .transition().duration(200)
//                 .attr("stroke", styling.highlightLinkColor);
//             showTooltip(event, d);
//         })
//         .on("mouseout", function(event) {
//             d3.select(this).attr("fill", getNodeFill(d));
//             link.transition().duration(200).attr("stroke", l => l.style?.stroke || styling.linkColor);
//             d3.selectAll(".tooltip").remove();
//         })
//         .on("click", (event, d) => {
//             clicked(d.id);  // Call your custom function with node id
//         });

//     node.append("text")
//         .attr("text-anchor", "middle")
//         .attr("dy", -(d.style?.radius || styling.nodeRadius) - 4)
//         .text(d.name)
//         .attr("fill", d.style?.textColor || styling.textColor)
//         .style("font-size", `${graphConfig.fontSize}px`);

//     tempNodes.push(node);
// });

// function getNodeFill(d) {
//     return d.style?.fill ||
//         (d.id.toString().startsWith("UNKNOWN")
//             ? d.style?.unknownFill || styling.unknownNodeColor
//             : styling.languageColors[d.language] || styling.defaultNodeColor);
// }


//     // const tempNodes = zoomGroup.selectAll(".node")
//     //     .data(nodes)
//     //     .enter().append("g")
//     //     .attr("class", d => `node language-${d.language}`)
//     //     // .attr("data-file", d.file)
//     //     // .attr("data-return-type", d.details.returnType || "unknown")
//     //     // .attr("data-class-name", d.details.parentClass || "unknown")
//     //     // .attr("data-function-name", d.details.parentFunction || "unknown")
//     //     // .attr("data-parameters", d.details.parameters || "unknown")
//     //     // .attr("data-path", d.details.path || "unknown")
//     //     .attr("filter", "url(#drop-shadow)")
//     //     .call(d3.drag().on("start", dragStart).on("drag", dragged).on("end", dragEnd));

//     // tempNodes.append("circle")
//     //     .attr("r", d => (d.style?.radius) || styling.nodeRadius)
//     //     .attr("fill", d => {
//     //         if (d.style?.fill) return d.style.fill;
//     //         return d.id.toString().startsWith("UNKNOWN")
//     //             ? d.style?.unknownFill || styling.unknownNodeColor
//     //             : styling.languageColors[d.language] || styling.defaultNodeColor;
//     //     })
//     //     .on("mouseover", function(event, d) {
//     //         d3.select(this).attr("fill", d.style?.hoverFill || styling.nodeHoverColor);
//     //         link.filter(l => l.source.id === d.id || l.target.id === d.id)
//     //             .transition().duration(200)
//     //             .attr("stroke", styling.highlightLinkColor);
//     //         showTooltip(event, d);
//     //     })
//     //     .on("mouseout", function(event, d) {
//     //         d3.select(this).attr("fill", () => d.style?.fill || styling.languageColors[d.language] || styling.defaultNodeColor);
//     //         link.transition().duration(200).attr("stroke", l => l.style?.stroke || styling.linkColor);
//     //         d3.selectAll(".tooltip").remove();
//     //     })
//     //     .on("click", (event, d) => {
//     //         d3.select("#detail-panel").html(`
//     //             <h3>${d.name}</h3>
//     //             <p><strong>File:</strong> ${d.file}</p>
//     //             <p><strong>Language:</strong> ${d.language}</p>
//     //             <p><strong>Path:</strong> ${d.details.path || "N/A"}</p>
//     //             <p><strong>Parent Class:</strong> ${d.details.parentClass || "N/A"}</p>
//     //             <p><strong>Parent Function:</strong> ${d.details.parentFunction || "N/A"}</p>
//     //             <p><strong>Parameters:</strong> ${JSON.stringify(d.details.parameters)}</p>
//     //         `);
//     //     });

//     // tempNodes.append("text")
//     //     .attr("text-anchor", "middle")
//     //     .attr("dy", d => -((d.style?.radius) || styling.nodeRadius) - 4)
//     //     .text(d => d.name)
//     //     .attr("fill", d => d.style?.textColor || styling.textColor)
//     //     .style("font-size", `${graphConfig.fontSize}px`);

//     // tempNodes.each(function(d) {
//     //     const moduleGroup = moduleGroups.get(d.file);
//     //     moduleGroup?.node().appendChild(this);
//     // });

//     return { tempNodes, link, moduleGroups };
// }

function defineArrowMarkers(zoomGroup, options) {
    const defs = zoomGroup.append("defs");

    // Reuse a simpler gradient if desired, or omit it to stick with a solid color.
    defs.append("linearGradient")
        .attr("id", "main-gradient")
        .attr("x1", "0%").attr("y1", "0%")
        .attr("x2", "100%").attr("y2", "100%")
        .selectAll("stop")
        .data([
            { offset: "0%", color: "#00e5ff" },
            { offset: "100%", color: "#18ffff" }
        ])
        .enter().append("stop")
        .attr("offset", d => d.offset)
        .attr("stop-color", d => d.color);

    // Marker configuration parameters.
    // Adjust refX to properly position the arrow relative to the node.
    const arrowRefX = 20;
    // Let the arrow use a solid color, or you can choose the gradient by "url(#main-gradient)"
    const arrowColor = options.arrowColor || "#a8d8ff";
    const arrowSize = options.arrowSize || 6;

    // Define a conventional arrow marker shape:
    // The shape "M0,-5 L10,0 L0,5 L2,0 Z" creates an arrow with a pointed tip,
    // a small notch at the base, and a closed path (Z) for a filled marker.
    const markerData = options.markers || [
        {
            id: "arrow",
            refX: arrowRefX,
            color: arrowColor,
            pathD: "M0,-5 L10,0 L0,5 L2,0 Z",
            width: arrowSize,
            height: arrowSize
        }
    ];

    // Append the marker elements.
    markerData.forEach(marker => {
        const m = defs.append("marker")
            .attr("id", marker.id)
            .attr("viewBox", "0 -5 12 10")
            .attr("refX", marker.refX)
            .attr("refY", 0)
            .attr("markerWidth", marker.width)
            .attr("markerHeight", marker.height)
            .attr("orient", "auto");

        m.append("path")
            .attr("d", marker.pathD)
            .attr("fill", marker.color);
    });
}



function defineGlowFilter(svg) {
    const defs = svg.select("defs").empty()
        ? svg.append("defs")
        : svg.select("defs");

    const glow = defs.append("filter")
        .attr("id", "glow")
        .attr("x", "-50%")
        .attr("y", "-50%")
        .attr("width", "200%")
        .attr("height", "200%");

    glow.append("feGaussianBlur")
        .attr("stdDeviation", 2.5)
        .attr("result", "coloredBlur");

    const merge = glow.append("feMerge");
    merge.append("feMergeNode").attr("in", "coloredBlur");
    merge.append("feMergeNode").attr("in", "SourceGraphic");
}

function defineDropShadow(svg, options = {}) {
    const {
        id = "drop-shadow",
        blur = 3,
        dx = 2,
        dy = 2,
        shadowColor = "#000d33",
        glow = true
    } = options;

    const defs = svg.append("defs");
    const filter = defs.append("filter")
        .attr("id", id)
        .attr("x", "-50%")
        .attr("y", "-50%")
        .attr("width", "200%")
        .attr("height", "200%");

    filter.append("feGaussianBlur")
        .attr("in", "SourceAlpha")
        .attr("stdDeviation", blur)
        .attr("result", "blur");

    filter.append("feOffset")
        .attr("in", "blur")
        .attr("dx", dx)
        .attr("dy", dy)
        .attr("result", "offsetBlur");

    if (glow) {
        filter.append("feFlood")
            .attr("flood-color", shadowColor)
            .attr("flood-opacity", 0.7)
            .attr("result", "flood");

        filter.append("feComposite")
            .attr("in", "flood")
            .attr("in2", "offsetBlur")
            .attr("operator", "in")
            .attr("result", "coloredBlur");

        const merge = filter.append("feMerge");
        merge.append("feMergeNode").attr("in", "coloredBlur");
        merge.append("feMergeNode").attr("in", "SourceGraphic");
    } else {
        const merge = filter.append("feMerge");
        merge.append("feMergeNode").attr("in", "offsetBlur");
        merge.append("feMergeNode").attr("in", "SourceGraphic");
    }
}


function handleSimulationTicks(simulations, tempNodes, link, moduleGroups, styling) {
    simulations[currentSimulationId].on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

            tempNodes.forEach(node => {
                node.attr("transform", d => `translate(${d.x},${d.y})`);
            });
            

        moduleGroups.forEach((moduleGroup) => {
            const moduleNodes = moduleGroup.selectAll(".node").data();
            if (!moduleNodes.length) return;
            const minX = d3.min(moduleNodes, n => n.x);
            const minY = d3.min(moduleNodes, n => n.y);
            const maxX = d3.max(moduleNodes, n => n.x);
            const maxY = d3.max(moduleNodes, n => n.y);
            moduleGroup.select("rect.module-bg")
                .attr("x", minX - styling.groupPadding)
                .attr("y", minY - styling.groupPadding)
                .attr("width", (maxX - minX) + styling.groupPadding * 2)
                .attr("height", (maxY - minY) + styling.groupPadding * 2);
        });
    });
}
function hideTooltip() {
    d3.select("#custom-tooltip")
        .transition()
        .duration(200)
        .style("opacity", 0)
        .on("end", function () {
            d3.select(this).remove();
        });
}
function showTooltip(event, d) {
    let tooltip = d3.select("#custom-tooltip");

    // Reuse or create new tooltip div
    if (tooltip.empty()) {
        tooltip = d3.select("body").append("div")
            .attr("id", "custom-tooltip")
            .style("position", "absolute")
            .style("max-width", "250px")
            .style("background", "rgba(30, 30, 30, 0.9)")
            .style("color", "#fff")
            .style("padding", "10px")
            .style("border-radius", "8px")
            .style("box-shadow", "0px 4px 12px rgba(0, 0, 0, 0.3)")
            .style("font-family", "sans-serif")
            .style("font-size", "14px")
            .style("pointer-events", "none")
            .style("opacity", 0)
            .style("transition", "opacity 0.3s ease");
    }

    // Data with fallbacks
    const name = d.name || "Unnamed";
    const file = d.file || "N/A";
    const lang = d.language || "Unknown";
    const cls = d.class || "None";
    const ret = d.returnType || "void";
    const id = d.id !== undefined ? `<small>ID: ${d.id}</small>` : "";

    // Positioning logic
    const tooltipOffset = graphConfig.tooltipOffset || { x: 10, y: 10 };
    let left = event.pageX + tooltipOffset.x;
    let top = event.pageY + tooltipOffset.y;
    const tooltipWidth = 250, tooltipHeight = 120;
    if (left + tooltipWidth > window.innerWidth) left = event.pageX - tooltipWidth - 20;
    if (top + tooltipHeight > window.innerHeight) top = event.pageY - tooltipHeight - 20;

    // Check for modifier key
    const advancedDetails = event.shiftKey;

    tooltip.html(`
        <div style="border-bottom: 1px solid #555; padding-bottom: 5px; margin-bottom: 5px;">
            <strong>${name}</strong><br/>
            <span style="color:#aaa;">${file}</span>
        </div>
        <div>
            Language: <span style="color:#ffd700;">${lang}</span><br/>
            ${
                advancedDetails
                ? `Class: ${cls}<br/>Return: ${ret}<br/>${id}`
                : '<em>Hold Shift or click for details</em>'
            }
        </div>
    `);

    tooltip
        .style("left", `${left}px`)
        .style("top", `${top}px`)
        .transition()
        .duration(200)
        .style("opacity", 1);
}


// --------------------------------------------
// Drag Handlers
// --------------------------------------------
function dragStart(event, d) {
    if (!event.active) simulations[currentSimulationId].alphaTarget(0.3).restart(); // <== REHEAT
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnd(event, d) {
    if (!event.active) simulations[currentSimulationId].alphaTarget(0); // cool down
    d.fx = null;
    d.fy = null;
}
function setupSearch(styling, svg, simulations, nodes, link) {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    // Create a styled, animated search bar
    const searchInput = d3.select(".search-box").append("input")
        .attr("id", "search-input")
        
        .attr("placeholder", "🔍 Search nodes...")
        .style("background", "white")
        // .style("position", "absolute")
        // .style("top", "20px")
        .style("right", "20px")
        .style("padding", "8px 12px")
        .style("font-size", "14px")
        .style("border", "2px solid #ccc")
        .style("border-radius", "8px")
        .style("box-shadow", "0px 2px 10px rgba(0,0,0,0.1)")
        .style("transition", "all 0.3s")

    const history = [];

    // Autocomplete container
    const dropdown = d3.select("body").append("div")
        .attr("id", "autocomplete")
        .style("position", "absolute")
        .style("top", "50px")
        .style("right", "20px")
        .style("background", "black")
        .style("border", "1px solid #ccc")
        .style("border-radius", "6px")
        .style("max-height", "150px")
        .style("overflow-y", "auto")
        .style("box-shadow", "0 4px 8px rgba(0,0,0,0.1)")
        .style("display", "none")
        .style("width", "200px");

    // Define a custom CSS animation for glow pulse
    const styleEl = d3.select("head").append("style").text(`
        @keyframes glowPulse {
            0% { filter: drop-shadow(0 0 0px ${styling.highlightStroke}); }
            50% { filter: drop-shadow(0 0 10px ${styling.highlightStroke}); }
            100% { filter: drop-shadow(0 0 0px ${styling.highlightStroke}); }
        }
        .glow-pulse {
            animation: glowPulse 2s ease-in-out infinite;
        }
    `);

    searchInput.on("input", function () {
        const term = this.value.toLowerCase();
        dropdown.selectAll("*").remove();

        if (!term) {
            dropdown.style("display", "none");
            return;
        }

        // Use the provided nodes array directly
        const matches = nodes.filter(d => d.name.toLowerCase().includes(term));
        if (matches.length > 0) {
            dropdown.style("display", "block");
            matches.forEach(match => {
                dropdown.append("div")
                    .text(match.name)
                    .style("padding", "5px 10px")
                    .style("cursor", "pointer")
                    .on("click", () => {
                        searchInput.property("value", match.name);
                        focusNode(match);
                        dropdown.style("display", "none");
                        
                    });
            });
        }

        // Highlight matching nodes on the canvas with a quick stroke change
        d3.selectAll(".node")
            .style("stroke", d =>
                d.name.toLowerCase().includes(term) ? styling.highlightStroke : "none"
            )
            .style("stroke-width", d =>
                d.name.toLowerCase().includes(term) ? 3 : 0
            );
    });

    function focusNode(d) {
        // Zoom to the node
        const zoom = d3.zoom().on("zoom", ({ transform }) => {
            svg.select("g").attr("transform", transform);
        });

        svg.transition().duration(750).call(
            zoom.transform,
            d3.zoomIdentity.translate(width / 2 - d.x * 1.5, height / 2 - d.y * 1.5).scale(1.5)
        );

        // Add a ripple effect centered at the node
        svg.append("circle")
            .attr("cx", d.x)
            .attr("cy", d.y)
            .attr("r", 0)
            .attr("fill", "none")
            .attr("stroke", styling.highlightStroke)
            .attr("stroke-width", 2)
            .style("pointer-events", "none")
            .transition()
            .duration(800)
            .attr("r", 30)
            .style("opacity", 0)
            .remove();

        // Add a glow-pulse effect to the node for a visual cue
        const nodeSelection = d3.selectAll(".node").filter(n => n === d);
        nodeSelection.classed("glow-pulse", true);
        nodeSelection.transition().duration(200)
            .style("fill", styling.highlightFill || "#ff0")
            .transition().delay(2000).duration(800)
            .style("fill", d.originalFill || "#fff")
            .on("end", () => nodeSelection.classed("glow-pulse", false));

        // Dim all other nodes to make the selected one stand out
        d3.selectAll(".node")
          .transition()
          .duration(300)
          .style("opacity", n => n === d ? 1 : 0.3);
        
        // After 4.5 seconds, restore opacity to all nodes
        setTimeout(() => {
            d3.selectAll(".node")
              .transition()
              .duration(500)
              .style("opacity", 1);
        }, 1500);

        // Store in history
        if (!history.includes(d.name)) history.unshift(d.name);
    }

    // Clamp simulations[currentSimulationId] as before
    const minX = 0, maxX = 2500, minY = 0, maxY = 1200;
    simulations[currentSimulationId].on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        d3.selectAll(".node").attr("transform", d => {
            d.x = Math.max(minX, Math.min(maxX, d.x));
            d.y = Math.max(minY, Math.min(maxY, d.y));
            return `translate(${d.x},${d.y})`;
        });
    });

    // Optional: press ↑ to show history
    d3.select("body").on("keydown", (event) => {
        if (event.key === "ArrowUp" && history.length > 0) {
            dropdown.style("display", "block");
            dropdown.selectAll("*").remove();
            history.forEach(h => {
                dropdown.append("div")
                    .text(h)
                    .style("padding", "5px 10px")
                    .style("cursor", "pointer")
                    .on("click", () => {
                        searchInput.property("value", h);
                        const match = nodes.find(d => d.name === h);
                        if (match) focusNode(match);
                        dropdown.style("display", "none");
                    });
            });
        }
    });
}



// Turn off repulsion by removing the 'charge' force.
function disableRepulsion() {
    simulations[currentSimulationId].force("charge", null);
    simulations[currentSimulationId].alpha(1).restart(); // Restart simulations[currentSimulationId] to see changes immediately.
    console.log("Repulsion disabled.");
}

// Turn on repulsion by re-adding the 'charge' force with a given strength.
function enableRepulsion(chargeStrength) {
    simulations[currentSimulationId].force("charge", d3.forceManyBody().strength(chargeStrength));
    simulations[currentSimulationId].alpha(1).restart();
}

// Freeze all nodes by fixing their current positions.
function freezeNodes() {
    simulations[currentSimulationId].nodes().forEach(function(d) {
        d.fx = d.x;
        d.fy = d.y;
    });
}

// Unfreeze all nodes by releasing their fixed positions.
function unfreezeNodes() {
    simulations[currentSimulationId].nodes().forEach(function(d) {
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
    chargeStrength: -300,               // Repulsion
    chargeDistanceMax: 400,
    linkDistance: 150,
    gravity: 0.1,                        // Mild pull to center
    collisionRadius: 20,                // Node overlap prevention

    minZoom: 0.3,
    maxZoom: 6,
    zoomSpeed: 0.05,

    nodeRadius: 12,
    nodestrokeWidth:  2,
    nodeStrokeColor: "#fff",
    defaultNodeColor: "#888",
    unknownNodeColor: "#ff4444",
    nodeHoverColor: "#ffd700",
    nodeSelectedColor: "#00ffff",
    nodePulseAnimation: true,           // Pulsing effect on important nodes

    fontFamily: "Fira Code, monospace",
    fontSize: 12,
    fontColor: "#ffffff",
    textDy: 4,
    showLabelsOnHover: true,

    linkColor: "#bbb",
    linkHoverColor: "#ff5722",
    linkstrokeWidth:  1.5,
    dashedLinks: true,
    linkHighlightWidth: 3,

    markerRefX: 10,
    markerWidth: 6,
    markerHeight: 6,
    markerPathD: "M0,-5L10,0L0,5",
    markerColor: "#999",
    markerGlow: true,

    groupPadding: 10,
    groupColors: ["#eee", "#ddd", "#ccc", "#bbb"],

    languageColors: {
        python: "#3572A5",
        javascript: "#f1e05a",
        java: "#b07219",
        typescript: "#2b7489",
        go: "#00ADD8",
        rust: "#dea584",
        cplusplus: "#f34b7d",
        html: "#e34c26",
        css: "#563d7c"
    },

    glowEffect: {
        enabled: true,
        color: "#00ffff",
        blur: 4,
        strength: 0.7
    },

    enableDrag: true,
    focusOnClick: true,
    bounceOnHover: true,

    showTooltips: true,
    tooltipStyle: {
        background: "#fff",
        border: "1px solid #ccc",
        padding: "6px",
        borderRadius: "6px",
        fontSize: "13px",
        color: "#222"
    },

    theme: "dark",  
};


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
    const baseNodeStyle = {
        stroke: "#444",
        strokeWidth:  1.5,
        fontSize: 13,
        filter: "url(#drop-shadow)",
        transition: "fill 0.25s ease, r 0.2s ease, stroke 0.2s ease",
    };

    let specificStyle = {};

    if (node.name === "main") {
        specificStyle = {
            fill: "url(#main-gradient)",        // Gradient fill (defined in SVG defs)
            radius: 20,
            hoverFill: "#a7ffeb",
            textColor: "#ccffff",
            glow: true,
            pulse: true
        };
    }


    else if (node.parentClass) {
        specificStyle = {
            fill: "#f06292",                    // Elegant pink
            radius: 14,
            hoverFill: "#f8bbd0",
            textColor: "#ccffff",
            dashedBorder: true
        };
    }

    // else if (node.activityLevel >= 75) {
    //     specificStyle = {
    //         fill: "#ff8a65",                    // Vibrant orange
    //         radius: 16,
    //         hoverFill: "#ffccbc",
    //         textColor: "#ccffff",
    //         pulse: true
    //     };
    // }

    // // 🏷️ Tag-based (optional flag-based design)
    else if (node.tags?.includes("core")) {
        specificStyle = {
            fill: "#81d4fa",                    // Light sky blue
            radius: 14,
            hoverFill: "#b3e5fc",
            textColor: "#ccffff",
            borderGlow: true
        };
    }

    else {
        switch ((node.language || "").toLowerCase()) {
            case "python":
                specificStyle = {
                    fill: "#42a5f5",
                    radius: 13,
                    hoverFill: "#bbdefb",
                    textColor: "#ccffff"
                };
                break;
            case "java":
                specificStyle = {
                    fill: "#fbc02d",
                    radius: 13,
                    hoverFill: "#fff176",
                    textColor: "#ccffff"
                };
                break;
            case "cpp":
            case "C++":
            case "c++":
                specificStyle = {
                    fill: "#ba68c8",
                    radius: 13,
                    hoverFill: "#e1bee7",
                    textColor: "#ccffff"
                };
                break;
            case "javascript":
                specificStyle = {
                    fill: "#4db6ac",
                    radius: 13,
                    hoverFill: "#b2dfdb",
                    textColor: "#ccffff"
                };
                break;
            case "html":
                specificStyle = {
                    fill: "#ef9a9a",
                    radius: 13,
                    hoverFill: "#ffcdd2",
                    textColor: "#ccffff"
                };
                break;
            case "css":
                specificStyle = {
                    fill: "#90caf9",
                    radius: 13,
                    hoverFill: "#e3f2fd",
                    textColor: "#ccffff"
                };
                break;
            default:
                specificStyle = {
                    fill: "#cfd8dc",             // Subtle grey
                    radius: 12,
                    hoverFill: "#eceff1",
                    textColor: "#ccffff",
                    pulse: node.isRecentlyModified
                };
        }
    }

    return { ...baseNodeStyle, ...specificStyle };
}


function getLinkStyle(link) {
    // renderLink(link); // Call renderLink to create the SVG element
    const baseLinkStyle = {
        opacity: 0.95,
        pointerEvents: "auto",
        transition: "stroke-dasharray 0.3s ease, stroke 0.3s ease, opacity 0.2s ease",
        markerEnd: "url(#arrow)", // Ensure you've defined an SVG arrow marker in <defs>
    };

    let specificStyle = {};

    // 🎯 Class internal call (blue dashed)
    if (link.isInsideClass) {
        specificStyle = {
            stroke: "#5c6bc0", // Indigo
            strokeWidth:  2.5,
            strokeDasharray: "4,4"
        };
    }

    // 🔁 Control structure (gray long dash)
    else if (link.isInsideIfElseOrSwitch) {
        specificStyle = {
            stroke: "#90a4ae", // Cool gray
            strokeWidth:  2.2,
            strokeDasharray: "6,4"
        };
    }

    // 🔁 Loop or environment (teal short dash)
    else if (link.isInsideLoopOrEnvironment) {
        specificStyle = {
            stroke: "#26a69a", // Teal
            strokeWidth:  2.2,
            strokeDasharray: "3,3"
        };
    }

    // 🧠 Function call (solid neutral)
    else if (link.isInsideFunction) {
        specificStyle = {
            stroke: "#455a64", // Slate blue-gray
            strokeWidth:  2,
            strokeDasharray: ""
        };
    }

    // 🚀 Experimental: Interfunction & intermodule calls (light, thick, with animated pulse)
    else if (link.isInterFunction || link.isInterModule) {
        specificStyle = {
            stroke: "#e0e0e0",   // Light color (suits dark backgrounds)
            strokeWidth:  3.5,    // Thicker line
            strokeDasharray: "",
            // For experimental pulse effect: add an SVG animation via a custom property.
            svgAnimation: `
              <animate 
                attributeName="stroke-width" 
                from="3.5" 
                to="4.5" 
                dur="0.6s" 
                begin="0s" 
                repeatCount="indefinite" 
                fill="freeze" />`
        };
    }

    // 🧪 Test-specific link (yellow glow)
    else if (link.path && link.path.includes("/tests/")) {
        specificStyle = {
            stroke: "#fdd835",
            strokeWidth:  2,
            strokeDasharray: "1,5",
            glow: true // Optional: apply glow via CSS or SVG filter
        };
    }

    // 🔗 Async/dependency links (optional custom types)
    else if (link.isAsync) {
        specificStyle = {
            stroke: "#7e57c2", // Purple
            strokeWidth:  2,
            strokeDasharray: "5,5"
        };
    }

    // ✨ Default link (soft gray-blue solid)
    else {
        specificStyle = {
            stroke: "#cfd8dc", // Light cool gray
            strokeWidth:  1.8,
            strokeDasharray: ""
        };
    }

    return { ...baseLinkStyle, ...specificStyle };
}



function clicked(node, nodeId, x, y) {
    if(GeneratedSidePanel[nodeId]) {
        reactivatePanel(nodeId, x, y);
    }
    else{
        getDescription(nodeId, 1);
        GeneratedSidePanel[nodeId] = true;
        createPanel(nodeId, x, y);
        updateInfoPanel(node, nodeId, 0.85, 0.85);
        updateEthicsPanel(nodeId)
        updateOptimizationPanel(nodeId);
    }
    console.log("Node clicked:", nodeId, x, y);
}
function updateInfoPanel(node, id, scale = 1, textScale = 1) {
    const infoPanel = d3.select(`#info-panel-1-${id}`);
  
    infoPanel.html(`
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        .info-card, .description-card {
            font-family: 'Roboto', sans-serif;
            border: 1px solid #444;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            overflow: hidden;
            background-color: #1e1e1e;
            transform: scale(${scale});
            transition: transform 1s linear;
            margin-bottom: 2px;
        }
        .info-card { width: 400px; height: auto; }
        .description-card { width: 400px; height: auto; }
  
        .card-header, .description-header {
            background: linear-gradient(135deg, #212121, #424242);
            color: #fff;
            padding: 5px;
            text-align: center;
        }
        .card-header h3, .description-header h3 {
            margin: 0;
            font-size: ${1.3 * textScale}em;
        }
        .card-body, .description-body {
            padding: 5px;
            color: #ddd;
            font-size: ${1 * textScale}em;
        }
        .flex-class {
            display: flex;
            justify-content: space-between;
        }
        .info-item {
            margin-bottom: 5px;
            display: flex;
            align-items: center;
        }
        .info-item span.label {
            width: 200px;
            font-weight: 500;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
            background: #333;
            padding: 7px;
            border-radius: 5px;
            flex: 1;
            font-size: ${0.9 * textScale}em;
            color: #ccc;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
      </style>
  
      <div class="card info-card" style="animation: fadeIn 0.5s ease-in-out;">
        <div class="card-header">
          <h3>${node.name}</h3>
        </div>
        <div class="card-body">
          <div class="info-item">
            <span class="label">Path:</span>
            <span>${node.details.path || "N/A"}</span>
          </div>
          <div class="info-item">
            <span class="label">Language:</span>
            <span>${node.language}</span>
          </div>
          <div class="info-item" style="align-items: flex-start;">
            <span class="label">Parameters:</span>
            <pre>${JSON.stringify(node.details.parameters, null, 2)}</pre>
          </div>
        </div>
      </div>
  
      <div class="card description-card" id="description-panel-${id}" style="animation: fadeIn 0.5s ease-in-out;">
        <div class="description-header flex-class">
          <div></div>
          <h3>Description</h3>
          <button class="refresh-btn" id="reload-1-${id}" title="Refresh">
            <i class="fas fa-rotate-right"></i>
          </button>
        </div>
        <div class="description-body">
          <div class="loading" id="spinner-1-${id}">
            <div class="spinner"></div>
            Analyzing<span id="opt-dots-${id}"></span>
          </div>
          <div id="description-body-${id}">
          </div>
        </div>
      </div>
    `);
  
    // Animate dots
    const dotsEl = document.getElementById(`desc-dots-${id}`);
    let count = 0;
    setInterval(() => {
      count = (count + 1) % 4;
      if(dotsEl)
      dotsEl.textContent = '.'.repeat(count);
    }, 500);
  
    // Attach refresh functionality
    const reloadBtn = document.querySelector(`#reload-1-${id}`);
    if (reloadBtn) {
      reloadBtn.onclick = function () {
        d3.select(`#spinner-1-${id}`).style("display", "flex");
        d3.select(`#description-body-${id}`).style("display", "none");
        getDescription(id, 1);
      };
    }
  }
  
function updateOptimizationPanel(id) {
    const infoPanel = d3.select(`#info-panel-2-${id}`);
  
    infoPanel.html(`
      <div class="card description-card" id="optimization-panel-${id}" style="animation: fadeIn 0.5s ease-in-out;">
        <div class="description-header flex-class">
          <div></div>
          <h3>Optimization</h3>
          <button class="refresh-btn" id="reload-2-${id}" title="Refresh">
            <i class="fas fa-rotate-right"></i>
          </button>
        </div>
        <div class="description-body">
          <div class="loading" id="spinner-2-${id}">
            <div class="spinner"></div>
            Analyzing<span id="opt-dots-${id}"></span>
          </div>
          <div id="optimization-body-${id}">

          </div>
        </div>
      </div>
    `);
  
    // Animate dots
    const dotsEl = document.getElementById(`opt-dots-${id}`);
    let count = 0;
    setInterval(() => {
      count = (count + 1) % 4;
      if(dotsEl)
      dotsEl.textContent = '.'.repeat(count);
    }, 500);
  
    // Bind reload button
    document.querySelector(`#reload-2-${id}`).onclick = function () {
      d3.select(`#spinner-2-${id}`).style("display", "flex");
      d3.select(`#optimization-body-${id}`).style("display", "none");
      getDescription(id, 2);
    };
  }
  
  function updateEthicsPanel(id) {
    const infoPanel = d3.select(`#info-panel-3-${id}`);
    
    // Update HTML safely (fixed duplicate ID and dots ID)
    infoPanel.html(`
      <div class="card description-card" id="ethics-panel-${id}" style="animation: fadeIn 0.5s ease-in-out;">
        <div class="description-header flex-class">
          <div></div>
          <h3>Code Ethics</h3>
          <button class="refresh-btn" id="reload-3-${id}" title="Refresh">
            <i class="fas fa-rotate-right"></i>
          </button>
        </div>
        <div class="description-body">
          <div class="loading" id="spinner-3-${id}">
            <div class="spinner"></div>
            Analyzing<span id="opt-dots-${id}"></span>
          </div>
          <div id="ethics-body-${id}">
          </div>
        </div>
      </div>
    `);
  
    // Animate dots
    const dotsEl = document.getElementById(`ethics-dots-${id}`);
    let count = 0;
    setInterval(() => {
      count = (count + 1) % 4;
      if(dotsEl)
      dotsEl.textContent = '.'.repeat(count);
    }, 500);
  
    // Bind refresh button logic
    document.querySelector(`#reload-3-${id}`).onclick = function () {
      d3.select(`#spinner-3-${id}`).style("display", "flex");
      d3.select(`#ethics-body-${id}`).style("display", "none");
      getDescription(id, 3);
    };
  }
  

  // Call this function when your description is ready
  function updateDescriptionPanel(id, description, type) {
    d3.select(`#spinner-${type}-${id}`).style("display", "none");  
    if (type === 1) {
      const descriptionBody = d3.select(`#description-body-${id}`);
      descriptionBody.style("display", "block");  
      descriptionBody.html(description);
    } else if (type === 2) {
      const optimizationBody = d3.select(`#optimization-body-${id}`);
      optimizationBody.style("display", "block"); 
      optimizationBody.html(description);
    } else if (type === 3) {
      const ethicsBody = d3.select(`#ethics-body-${id}`);
      ethicsBody.style("display", "block"); 
      ethicsBody.html(description);
    }
  }
  
  
  
// function updateInfoPanel(node) {
//     const infoPanel = d3.select("#info-panel");
//     infoPanel.html(`
//         <h3>${node.name}</h3>
//         <p><strong>File:</strong> ${node.file}</p>
//         <p><strong>Language:</strong> ${node.language}</p>
//         <p><strong>Path:</strong> ${node.details.path || "N/A"}</p>
//         <p><strong>Parent Class:</strong> ${node.details.parentClass || "N/A"}</p>
//         <p><strong>Parent Function:</strong> ${node.details.parentFunction || "N/A"}</p>
//         <p><strong>Parameters:</strong> ${JSON.stringify(node.details.parameters)}</p>
//     `);
// }


// Load the JSON file and generate the graph when the window loads.
function Start() {
    loadJSON()
        .then(data => {
            document.getElementById("loading-screen").style.display = "none"; // Hide loading screen
            document.getElementById("main-screen").style.display = "block"; // Show graph container
        })

}
document.getElementById("reload-All").onclick = function () {Start();}
// freezeNodes(); // Freeze nodes on load.

export {updateDescriptionPanel};
