import { getDescription } from "./getInfo.js";
let GeneratedSidePanel = [];
GeneratedSidePanel[2] = [];
GeneratedSidePanel[3] = [];
function createAnimatedPanel(panelId, clickX, clickY) {
  // Create a <style> tag if not already present to hold our custom animation
  if (!document.getElementById('dynamic-panel-styles')) {
    const styleEl = document.createElement('style');
    styleEl.id = 'dynamic-panel-styles';
    styleEl.innerHTML = `
      @keyframes burstIn {
        0% {
          transform: scale(0) rotate(0deg);
          opacity: 0;
          filter: blur(10px);
        }
        50% {
          transform: scale(1.2) rotate(10deg);
          opacity: 0.8;
          filter: blur(2px);
        }
        70% {
          transform: scale(0.95) rotate(-5deg);
          opacity: 0.95;
          filter: blur(0px);
        }
        100% {
          transform: scale(1) rotate(0deg);
          opacity: 1;
        }
      }
      .side-panel {
        background: linear-gradient(135deg, #ffffff 0%, #f7f7f7 100%);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        overflow: hidden;
        width: 400px; /* adjust as needed */
        height: 350px; /* adjust as needed */
        border: 1px solid rgba(0,0,0,0.1);
      }
      .side-panel.animate {
        animation: burstIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
      }
      /* Resize Handle Styling */
      .resize-handle {
        position: absolute;
        background: rgba(0, 0, 0, 0.15);
        transition: background 0.2s ease;
      }
      .resize-handle:hover {
        background: rgba(0, 0, 0, 0.25);
      }
      .resize-handle.top-left {
        top: -6px;
        left: -6px;
        width: 12px;
        height: 12px;
        cursor: nwse-resize;
      }
      .resize-handle.top-right {
        top: -6px;
        right: -6px;
        width: 12px;
        height: 12px;
        cursor: nesw-resize;
      }
      .resize-handle.bottom-left {
        bottom: -6px;
        left: -6px;
        width: 12px;
        height: 12px;
        cursor: nesw-resize;
      }
      .resize-handle.bottom-right {
        bottom: -6px;
        right: -6px;
        width: 12px;
        height: 12px;
        cursor: nwse-resize;
      }
      .resize-handle.top {
        top: -4px;
        left: 50%;
        transform: translateX(-50%);
        width: 16px;
        height: 8px;
        cursor: ns-resize;
      }
      .resize-handle.right {
        top: 50%;
        right: -4px;
        transform: translateY(-50%);
        width: 8px;
        height: 16px;
        cursor: ew-resize;
      }
      .resize-handle.bottom {
        bottom: -4px;
        left: 50%;
        transform: translateX(-50%);
        width: 16px;
        height: 8px;
        cursor: ns-resize;
      }
      .resize-handle.left {
        top: 50%;
        left: -4px;
        transform: translateY(-50%);
        width: 8px;
        height: 16px;
        cursor: ew-resize;
      }
      /* Panel Header */
      .panel-header {
        background: linear-gradient(90deg, #007bff, #0056b3);
        color: #fff;
        padding: 12px 16px;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.2);
      }
      .panel-header button.tab-btn {
        background: transparent;
        border: none;
        color: #fff;
        padding: 8px 12px;
        margin-right: 8px;
        font-size: 14px;
        cursor: pointer;
        transition: background 0.2s ease, color 0.2s ease;
      }
      .panel-header button.tab-btn.active {
        background: #ffffff;
        color: #0056b3;
        font-weight: bold;
        border-radius: 4px;
      }
      .panel-header button.tab-btn:hover {
        background: rgba(255, 255, 255, 0.2);
      }

      .panel-header button#closePanel-${panelId} {
        background: transparent;
        border: none;
        color: #fff;
        font-size: 24px;
        line-height: 1;
        cursor: pointer;
        padding: 4px;
        transition: color 0.2s ease;
      }
      .panel-header button#closePanel-${panelId}:hover {
        color: #ff6b6b;
      }
      /* Panel Content */
      .panel-content {
        padding: 3px;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        color: #333;
        background: #fff;
        overflow-y: auto;
        height: calc(100% - 56px); /* header height adjustment */
      }
      .panel-content h3 {
        margin-top: 0;
        font-size: 20px;
      }
      .panel-content p {
        font-size: 14px;
        line-height: 1.6;
      }
    `;
    document.head.appendChild(styleEl);
  }
  function setActiveTab(panelId, tabNum) {
    for (let i = 1; i <= 3; i++) {
      const btn = document.getElementById(`tab-btn-${i}-${panelId}`);
      if (btn) {
        btn.classList.toggle("active", i === tabNum);
      }
    }
  }
  
  const panelWidth = 400;
  const panelHeight = 350;

  const openUpward = clickY > window.innerHeight / 2;
  const openLeftward = clickX > window.innerWidth / 2;

  const panelTop = openUpward ? (clickY - panelHeight) : clickY;
  const panelLeft = openLeftward ? (clickX - panelWidth) : clickX;

  const originY = openUpward ? 'bottom' : 'top';
  const originX = openLeftward ? 'right' : 'left';

  // Create the container element with the panel HTML
  const container = document.createElement("div");
  container.innerHTML = `
    <div id="sidePanel-${panelId}" class="side-panel" 
         style="
            position: fixed; 
            top: ${panelTop}px;
            left: ${panelLeft}px;
            transform-origin: ${originY} ${originX};

         ">
      <!-- Resize Handles -->
      <div class="resize-handle top-left" data-dir="top-left"></div>
      <div class="resize-handle top-right" data-dir="top-right"></div>
      <div class="resize-handle bottom-left" data-dir="bottom-left"></div>
      <div class="resize-handle bottom-right" data-dir="bottom-right"></div>
      <div class="resize-handle top" data-dir="top"></div>
      <div class="resize-handle right" data-dir="right"></div>
      <div class="resize-handle bottom" data-dir="bottom"></div>
      <div class="resize-handle left" data-dir="left"></div>
  
      <!-- Panel Header with 3 Tab Buttons and the Close Button -->
      <div class="panel-header">
        <button id="tab-btn-1-${panelId}" class="tab-btn">Discription</button>
        <button id="tab-btn-2-${panelId}" class="tab-btn">Improvement</button>
        <button id="tab-btn-3-${panelId}" class="tab-btn">Smell</button>
        <button id="closePanel-${panelId}" 
                style="background: transparent; border: none; font-size: 24px; cursor: pointer;">
           &times;
        </button>
      </div>
  
      <!-- Tab Contents -->
      <div id="tab-content-1-${panelId}" class="panel-content" style="display: block;">
        <div id="info-panel-1-${panelId}" >
          <h3>Movable & Resizable Panel</h3>
          <p>Try dragging the header to move this panel. You can also resize it from any edge or corner.</p>
        </div>
      </div>
      <div id="tab-content-2-${panelId}" class="panel-content" style="display: none;">
        <div id="info-panel-2-${panelId}" >
          <h3>Movable & Resizable Panel</h3>
          <p>Try dragging the header to move this panel. You can also resize it from any edge or corner.</p>
        </div>
      </div>
      <div id="tab-content-3-${panelId}" class="panel-content" style="display: none;">
        <div id="info-panel-3-${panelId}" >
          <h3>Movable & Resizable Panel</h3>
          <p>Try dragging the header to move this panel. You can also resize it from any edge or corner.</p>
        </div>
      </div>
    </div>
  `;
  

  // Append the container to the body
  document.body.appendChild(container);
  setActiveTab(panelId, 1);
  // Script to handle tab switching using element.style.display
  document.getElementById(`tab-btn-1-${panelId}`).addEventListener('click', function() {
    setActiveTab(panelId, 1);
    document.getElementById(`tab-content-1-${panelId}`).style.display = "block";
    document.getElementById(`tab-content-2-${panelId}`).style.display = "none";
    document.getElementById(`tab-content-3-${panelId}`).style.display = "none";
  });
  
  document.getElementById(`tab-btn-2-${panelId}`).addEventListener('click', function() {
    setActiveTab(panelId, 2);
    if (!GeneratedSidePanel[2][panelId]) {
      getDescription(panelId, 2);
      GeneratedSidePanel[2][panelId] = true;
    }
    document.getElementById(`tab-content-1-${panelId}`).style.display = "none";
    document.getElementById(`tab-content-2-${panelId}`).style.display = "block";
    document.getElementById(`tab-content-3-${panelId}`).style.display = "none";
  });
  
  document.getElementById(`tab-btn-3-${panelId}`).addEventListener('click', function() {
    setActiveTab(panelId, 3);
    if (!GeneratedSidePanel[3][panelId]) {
      getDescription(panelId, 3);
      GeneratedSidePanel[3][panelId] = true;
    }
    document.getElementById(`tab-content-1-${panelId}`).style.display = "none";
    document.getElementById(`tab-content-2-${panelId}`).style.display = "none";
    document.getElementById(`tab-content-3-${panelId}`).style.display = "block";
  });
  

  // Use requestAnimationFrame to trigger the animation once rendered.
  requestAnimationFrame(() => {
    const panel = document.getElementById(`sidePanel-${panelId}`);
    
    // Adjust transform-origin dynamically if you want the panel to emerge 
    // more directly from the click point relative to its own dimensions.
    // For now, we're keeping it at "top left", but you could compute something like:
    // const rect = panel.getBoundingClientRect();
    // const originX = clickX - rect.left;
    // const originY = clickY - rect.top;
    // panel.style.transformOrigin = `${originX}px ${originY}px`;

    // Add the animation class to trigger the keyframe animation.
    panel.classList.add('animate');
  });
}


function createPanel(panelId, x, y) {
  createAnimatedPanel(panelId, x, y);

  const sidePanel = document.getElementById(`sidePanel-${panelId}`);
  const handles = sidePanel.querySelectorAll(".resize-handle");
  const header = sidePanel.querySelector(".panel-header");
  const closeBtn = document.getElementById(`closePanel-${panelId}`);
  const toggleBtn = document.getElementById(`togglePanel-${panelId}`);

  // --- Resizing ---
  handles.forEach(handle => {
    handle.addEventListener("mousedown", function (e) {
      e.preventDefault();
      const dir = handle.dataset.dir;
      const startX = e.clientX;
      const startY = e.clientY;

      const startWidth = sidePanel.offsetWidth;
      const startHeight = sidePanel.offsetHeight;
      const startTop = sidePanel.offsetTop;
      const startLeft = sidePanel.offsetLeft;

      document.body.style.userSelect = 'none';
      document.body.style.cursor = window.getComputedStyle(handle).cursor;
      sidePanel.style.pointerEvents = 'none';

      function doResize(eMove) {
        let dx = eMove.clientX - startX;
        let dy = eMove.clientY - startY;

        if (dir.includes("right")) {
          sidePanel.style.width = Math.min(startWidth + dx, window.innerWidth - 50) + "px";
        }
        if (dir.includes("left")) {
          const newWidth = startWidth - dx;
          if (newWidth >= 280 && newWidth <= 600) {
            sidePanel.style.width = newWidth + "px";
            sidePanel.style.left = (startLeft + dx) + "px";
          }
        }
        if (dir.includes("bottom")) {
          sidePanel.style.height = Math.max(startHeight + dy, 200) + "px";
        }
        if (dir.includes("top")) {
          const newHeight = startHeight - dy;
          if (newHeight >= 200 && newHeight <= window.innerHeight) {
            sidePanel.style.height = newHeight + "px";
            sidePanel.style.top = (startTop + dy) + "px";
          }
        }
      }

      function stopResize() {
        document.removeEventListener("mousemove", doResize);
        document.removeEventListener("mouseup", stopResize);
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
        sidePanel.style.pointerEvents = '';
      }

      document.addEventListener("mousemove", doResize);
      document.addEventListener("mouseup", stopResize);
    });
  });

  // --- Dragging ---
  let isDragging = false;
  let dragOffsetX = 0;
  let dragOffsetY = 0;

  header.addEventListener("mousedown", function(e) {
    if (e.target.id === `closePanel-${panelId}`) return;

    isDragging = true;
    dragOffsetX = e.clientX - sidePanel.offsetLeft;
    dragOffsetY = e.clientY - sidePanel.offsetTop;

    sidePanel.style.transition = "none";
  });

  document.addEventListener("mousemove", function(e) {
    if (isDragging) {
      sidePanel.style.left = (e.clientX - dragOffsetX) + "px";
      sidePanel.style.top = (e.clientY - dragOffsetY) + "px";
    }
  });

  document.addEventListener("mouseup", function() {
    if (isDragging) {
      isDragging = false;
      sidePanel.style.transition = "left 0.3s ease";
    }
  });

  // --- Open/Close ---
  // toggleBtn.addEventListener("click", () => {
  //   sidePanel.style.display = "block";
  // });

  closeBtn.addEventListener("click", () => {
    sidePanel.style.display = "none";
    // container.remove(); // Completely remove the panel from the DOM
  });
}
function reactivatePanel(panelId, clickX, clickY) {
  const panel = document.getElementById(`sidePanel-${panelId}`);
  if (!panel) return; // Exit if the panel doesn't exist

  // Position the panel at the new coordinates.
  panel.style.top = `${clickY}px`;
  panel.style.left = `${clickX}px`;

  // Make sure the panel is visible.
  panel.style.display = 'block';

  // Reset animation state by removing any previous animation class.
  panel.classList.remove('animate');
  
  // Force reflow so that removing the class is acknowledged.
  void panel.offsetWidth;
  
  // Re-add the animation class to trigger the burst-in animation.
  panel.classList.add('animate');
}



// Create multiple panels
// createPanel(0); 

export { createPanel, reactivatePanel };
export default createPanel;