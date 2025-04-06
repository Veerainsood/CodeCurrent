
const filePath = "./function_analysis.json";
let simulation = null;
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

// **************** Functional Part ****************
// Prepare graph data, including optional per-node or per-link styling if provided.
// Enhanced function to prepare graph data.
function prepareGraphData(jsonData) {
    const nodesMap = new Map();

    jsonData.uniqueFunctions.forEach(d => {
        if (!d.id) {
            console.error("Missing id for function:", d);
        } else {
            const styledNode = { 
                id: d.id, 
                name: d.name,
                file: d.file,
                language: d.language,
                details: d  // store complete details for the panel
            };
            styledNode.style = getNodeStyle(d);  // Apply logic-based style
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
            link.style = getLinkStyle(d);  // Apply logic-based style
            return link;
        } else {
            console.warn("Skipping invalid link between:", sourceId, targetId);
            return null;
        }
    }).filter(link => link !== null);

    const nodes = Array.from(nodesMap.values());
    return { nodes, links };
}
function buildGraph(nodes, links, styling) {
    clearSVG();
    const svg = setupSVGCanvas();
    const zoomGroup = setupZoom(svg, styling);
    const { linksLayer, modulesLayer } = createGraphLayers(zoomGroup);
    const legend = createLanguageLegend(svg, nodes, styling);
    simulation = setupSimulation(nodes, links, styling);

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

    handleSimulationTicks(simulation, tempNodes, link, moduleGroups, styling);
}

// --------------------------------------------
// Configuration Values (Easy to Change)
// --------------------------------------------

const graphConfig = {
    svgWidth: window.innerWidth,
    svgHeight: 600,
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
    return d3.select("svg")
        .attr("width", graphConfig.svgWidth)
        .attr("height", graphConfig.svgHeight);
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
    const legend = svg.append("g").attr("class", "legend").attr("transform", "translate(20,20)");

    languages.forEach((lang, i) => {
        const row = legend.append("g")
            .attr("transform", `translate(0, ${i * 20})`)
            .style("cursor", "pointer")
            .on("click", () => {
                const visible = d3.selectAll(`.node.language-${lang}`).style("opacity") !== "0.2";
                d3.selectAll(`.node.language-${lang}`)
                  .transition().duration(500)
                  .style("opacity", visible ? 0.2 : 1);
            });

        row.append("rect")
            .attr("width", 15)
            .attr("height", 15)
            .attr("fill", styling.languageColors[lang] || styling.defaultNodeColor);

        row.append("text")
            .attr("x", 20)
            .attr("y", 12)
            .attr("fill", "#333")
            .text(lang)
            .style("font-size", graphConfig.fontSize);
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

function drawGraphElements({ svg, zoomGroup, links, nodes, styling, linksLayer, modulesLayer }) {
    const link = linksLayer.selectAll(".link")
        .data(links)
        .enter().append("line")
        .attr("class", "link")
        .attr("stroke", d => (d.style?.stroke) || styling.linkColor)
        .attr("stroke-width", d => (d.style?.strokeWidth) || styling.linkStrokeWidth)
        .attr("marker-end", "url(#arrow)")
        .attr("stroke-dasharray", d => (d.style?.strokeDasharray) || null);

    const fileGroups = d3.group(nodes, d => d.file);
    const moduleGroups = new Map();

    Array.from(fileGroups.entries()).forEach(([file, nodesInModule], i) => {
        const group = modulesLayer.append("g").attr("class", "module-group").attr("data-file", file);
        group.append("rect")
            .attr("class", "module-bg")
            .attr("fill", styling.moduleBgColor || styling.groupColors[i % styling.groupColors.length])
            .attr("fill-opacity", 0.1)
            .attr("stroke", styling.moduleBorderColor || styling.groupColors[i % styling.groupColors.length])
            .attr("stroke-dasharray", "4 2");
        moduleGroups.set(file, group);
    });
    // Create a background rectangle for each module group to act as a container.
    // moduleGroups.forEach((group, file) => {
    //     const nodesInModule = group.selectAll(".node").data(nodes.filter(n => n.file === file));
    //     const minX = d3.min(nodesInModule, n => n.x) - styling.groupPadding;
    //     const minY = d3.min(nodesInModule, n => n.y) - styling.groupPadding;
    //     const maxX = d3.max(nodesInModule, n => n.x) + styling.groupPadding;
    //     const maxY = d3.max(nodesInModule, n => n.y) + styling.groupPadding;
    //     group.append("rect")
    //         .attr("class", "module-bg")
    //         .attr("x", minX)
    //         .attr("y", minY)
    //         .attr("width", maxX - minX + styling.groupPadding * 2)
    //         .attr("height", maxY - minY + styling.groupPadding * 2)
    //         .attr("fill", styling.groupColors[i % styling.groupColors.length])
    //         .attr("fill-opacity", 0.1)
    //         .attr("stroke", styling.groupColors[i % styling.groupColors.length])
    //         .attr("stroke-width", 1)
    //         .attr("stroke-dasharray", "4 2");
    // });
    const tempNodes = [];

nodes.forEach(d => {
    const group = moduleGroups.get(d.file);
    const node = group.append("g")
        .datum(d)
        .attr("class", `node language-${d.language}`)
        .attr("filter", "url(#drop-shadow)")
        .call(d3.drag()
            .on("start", dragStart)
            .on("drag", dragged)
            .on("end", dragEnd));

    node.append("circle")
        .attr("r", d.style?.radius || styling.nodeRadius)
        .attr("fill", getNodeFill(d))
        .on("mouseover", function(event) {
            d3.select(this).attr("fill", d.style?.hoverFill || styling.nodeHoverColor);
            link.filter(l => l.source.id === d.id || l.target.id === d.id)
                .transition().duration(200)
                .attr("stroke", styling.highlightLinkColor);
            showTooltip(event, d);
        })
        .on("mouseout", function(event) {
            d3.select(this).attr("fill", getNodeFill(d));
            link.transition().duration(200).attr("stroke", l => l.style?.stroke || styling.linkColor);
            d3.selectAll(".tooltip").remove();
        })
        .on("click", (event) => {
            d3.select("#detail-panel").html( /* ...same panel code... */ );
        });

    node.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", -(d.style?.radius || styling.nodeRadius) - 4)
        .text(d.name)
        .attr("fill", d.style?.textColor || styling.textColor)
        .style("font-size", `${graphConfig.fontSize}px`);

    tempNodes.push(node);
});

function getNodeFill(d) {
    return d.style?.fill ||
        (d.id.toString().startsWith("UNKNOWN")
            ? d.style?.unknownFill || styling.unknownNodeColor
            : styling.languageColors[d.language] || styling.defaultNodeColor);
}


    // const tempNodes = zoomGroup.selectAll(".node")
    //     .data(nodes)
    //     .enter().append("g")
    //     .attr("class", d => `node language-${d.language}`)
    //     // .attr("data-file", d.file)
    //     // .attr("data-return-type", d.details.returnType || "unknown")
    //     // .attr("data-class-name", d.details.parentClass || "unknown")
    //     // .attr("data-function-name", d.details.parentFunction || "unknown")
    //     // .attr("data-parameters", d.details.parameters || "unknown")
    //     // .attr("data-path", d.details.path || "unknown")
    //     .attr("filter", "url(#drop-shadow)")
    //     .call(d3.drag().on("start", dragStart).on("drag", dragged).on("end", dragEnd));

    // tempNodes.append("circle")
    //     .attr("r", d => (d.style?.radius) || styling.nodeRadius)
    //     .attr("fill", d => {
    //         if (d.style?.fill) return d.style.fill;
    //         return d.id.toString().startsWith("UNKNOWN")
    //             ? d.style?.unknownFill || styling.unknownNodeColor
    //             : styling.languageColors[d.language] || styling.defaultNodeColor;
    //     })
    //     .on("mouseover", function(event, d) {
    //         d3.select(this).attr("fill", d.style?.hoverFill || styling.nodeHoverColor);
    //         link.filter(l => l.source.id === d.id || l.target.id === d.id)
    //             .transition().duration(200)
    //             .attr("stroke", styling.highlightLinkColor);
    //         showTooltip(event, d);
    //     })
    //     .on("mouseout", function(event, d) {
    //         d3.select(this).attr("fill", () => d.style?.fill || styling.languageColors[d.language] || styling.defaultNodeColor);
    //         link.transition().duration(200).attr("stroke", l => l.style?.stroke || styling.linkColor);
    //         d3.selectAll(".tooltip").remove();
    //     })
    //     .on("click", (event, d) => {
    //         d3.select("#detail-panel").html(`
    //             <h3>${d.name}</h3>
    //             <p><strong>File:</strong> ${d.file}</p>
    //             <p><strong>Language:</strong> ${d.language}</p>
    //             <p><strong>Path:</strong> ${d.details.path || "N/A"}</p>
    //             <p><strong>Parent Class:</strong> ${d.details.parentClass || "N/A"}</p>
    //             <p><strong>Parent Function:</strong> ${d.details.parentFunction || "N/A"}</p>
    //             <p><strong>Parameters:</strong> ${JSON.stringify(d.details.parameters)}</p>
    //         `);
    //     });

    // tempNodes.append("text")
    //     .attr("text-anchor", "middle")
    //     .attr("dy", d => -((d.style?.radius) || styling.nodeRadius) - 4)
    //     .text(d => d.name)
    //     .attr("fill", d => d.style?.textColor || styling.textColor)
    //     .style("font-size", `${graphConfig.fontSize}px`);

    // tempNodes.each(function(d) {
    //     const moduleGroup = moduleGroups.get(d.file);
    //     moduleGroup?.node().appendChild(this);
    // });

    return { tempNodes, link, moduleGroups };
}

function defineArrowMarkers(zoomGroup, styling) {
    zoomGroup.append("defs").append("marker")
        .attr("id", "arrow")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", styling.markerRefX)
        .attr("refY", 0)
        .attr("markerWidth", styling.markerWidth)
        .attr("markerHeight", styling.markerHeight)
        .attr("orient", "auto")
        .append("path")
        .attr("d", styling.markerPathD)
        .attr("fill", styling.markerColor);
}

function defineDropShadow(svg) {
    const defs = svg.append("defs");
    const filter = defs.append("filter")
        .attr("id", "drop-shadow")
        .attr("x", "-50%").attr("y", "-50%")
        .attr("width", "200%").attr("height", "200%");

    filter.append("feGaussianBlur").attr("in", "SourceAlpha").attr("stdDeviation", 3).attr("result", "blur");
    filter.append("feOffset").attr("in", "blur").attr("dx", 2).attr("dy", 2).attr("result", "offsetBlur");
    const merge = filter.append("feMerge");
    merge.append("feMergeNode").attr("in", "offsetBlur");
    merge.append("feMergeNode").attr("in", "SourceGraphic");
}

function handleSimulationTicks(simulation, tempNodes, link, moduleGroups, styling) {
    simulation.on("tick", () => {
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

function showTooltip(event, d) {
    const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("background", "#fff")
        .style("padding", "5px")
        .style("border", "1px solid #ccc")
        .style("pointer-events", "none")
        .html(`<strong>${d.name}</strong><br/>File: ${d.file}<br/>Language: ${d.language}`);
    tooltip.style("left", (event.pageX + graphConfig.tooltipOffset.x) + "px")
           .style("top", (event.pageY + graphConfig.tooltipOffset.y) + "px");
}

// --------------------------------------------
// Drag Handlers
// --------------------------------------------
function dragStart(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart(); // <== REHEAT
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnd(event, d) {
    if (!event.active) simulation.alphaTarget(0); // cool down
    d.fx = null;
    d.fy = null;
}



// Additional feature: search filter to highlight nodes.
function setupSearch(styling) {
    const searchInput = d3.select("body").append("input")
        .attr("id", "search-input")
        .attr("placeholder", "Search nodes...")
        .style("position", "absolute")
        .style("top", "20px")
        .style("right", "20px")
        .style("padding", "5px");

    searchInput.on("input", function() {
        const term = this.value.toLowerCase();
        d3.selectAll(".node").style("stroke", d => {
            return d.name.toLowerCase().includes(term) ? styling.highlightStroke : "none";
        }).style("stroke-width", d => {
            return d.name.toLowerCase().includes(term) ? 3 : 0;
        });
    });


// Call setupSearch after building the graph.

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
    chargeStrength: -4500,         // Repulsion strength (adjust this)
    chargeDistanceMax: 400,   
    minZoom: 0.5,
    maxZoom: 5,
    nodeRadius: 10,
    linkDistance: 150,
    chargeStrength: -300,
    textDy: 4,
    groupPadding: 10,
    groupColors: ["#ccc", "#ddd"],
    languageColors: {
        python: "#3572A5",
        javascript: "#f1e05a",
        java: "#b07219"
        // add more language color mappings as needed
    },
    defaultNodeColor: "#999",
    unknownNodeColor: "#f00",
    nodeHoverColor: "#ff0",
    linkColor: "#666",
    linkStrokeWidth: 1.5,
    markerRefX: 10,
    markerWidth: 6,
    markerHeight: 6,
    markerPathD: "M0,-5L10,0L0,5",
    markerColor: "#666"
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
    // Base style applied to all nodes, including a drop shadow filter.
    const baseNodeStyle = {
        stroke: "#333",        // Common outline
        strokeWidth: 1.5,      // Common border width
        fontSize: 12,          // Common text size
        filter: "url(#drop-shadow)" // Apply drop shadow (ensure you define this filter in your SVG defs)
    };

    let specificStyle = {};

    if (node.name === "main") {
        specificStyle = {
            fill: "#66bb6a",
            radius: 16,
            hoverFill: "#a5d6a7",
            textColor: "#ffffff"
        };
    } else if (node.parentClass && node.parentClass !== "") {
        specificStyle = {
            fill: "#ec407a",
            radius: 13,
            hoverFill: "#f48fb1",
            textColor: "#ffffff"
        };
    } else if (node.path && node.path.includes("/tests/")) {
        specificStyle = {
            fill: "#ffca28",
            radius: 12,
            hoverFill: "#fff59d",
            textColor: "#000000"
        };
    } else {
        switch ((node.language || "").toLowerCase()) {
            case "python":
                specificStyle = {
                    fill: "#42a5f5",
                    radius: 11,
                    hoverFill: "#90caf9",
                    textColor: "#000000"
                };
                break;
            case "java":
                specificStyle = {
                    fill: "#ffb74d",
                    radius: 11,
                    hoverFill: "#ffe082",
                    textColor: "#000000"
                };
                break;
            case "cpp":
            case "c++":
                specificStyle = {
                    fill: "#ab47bc",
                    radius: 11,
                    hoverFill: "#ce93d8",
                    textColor: "#000000"
                };
                break;
            case "javascript":
                specificStyle = {
                    fill: "#26a69a",
                    radius: 11,
                    hoverFill: "#80cbc4",
                    textColor: "#000000"
                };
                break;
            default:
                specificStyle = {
                    fill: "#78909c",
                    radius: 10,
                    hoverFill: "#b0bec5",
                    textColor: "#000000"
                };
        }
    }

    return { ...baseNodeStyle, ...specificStyle };
}

function getLinkStyle(link) {
    // Base style applied to all links.
    const baseLinkStyle = {
        opacity: 0.9,           // Common transparency
        pointerEvents: "auto",  // Enable interaction
        transition: "stroke-dasharray 0.3s ease" // Smooth transition for dash changes
    };

    let specificStyle = {};

    if (link.isInsideClass) {
        specificStyle = {
            stroke: "#3f51b5",
            strokeWidth: 2,
            strokeDasharray: "2,4" // Dashed line
        };
    } else if (link.isInsideIfElseOrSwitch) {
        specificStyle = {
            stroke: "#999",
            strokeWidth: 2,
            strokeDasharray: "6,4" // Longer dashes
        };
    } else if (link.isInsideLoopOrEnvironment) {
        specificStyle = {
            stroke: "#999",
            strokeWidth: 2,
            strokeDasharray: "2,4" // Similar to inside class
        };
    } else if (link.isInsideFunction) {
        specificStyle = {
            stroke: "#555",
            strokeWidth: 2,
            strokeDasharray: "" // Solid line
        };
    } else {
        specificStyle = {
            stroke: "#aaa",
            strokeWidth: 2,
            strokeDasharray: "" // Solid line as default
        };
    }

    return { ...baseLinkStyle, ...specificStyle };
}





// Load the JSON file and generate the graph when the window loads.


window.onload = loadJSON;
// freezeNodes(); // Freeze nodes on load.
