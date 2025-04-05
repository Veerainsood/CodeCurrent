const sidePanel = document.getElementById("sidePanel");
    const overlay = document.getElementById("overlay");
    const toggleBtn = document.getElementById("togglePanel");
    const closeBtn = document.getElementById("closePanel");
    
    toggleBtn.onclick = () => {
      sidePanel.classList.setActive(true);
      overlay.classList.setActive(true);
    };
    
    closeBtn.onclick = () => {
      sidePanel.classList.setActive(false);
      overlay.classList.setActive(false);
    };
    
    overlay.onclick = () => {
      sidePanel.classList.remove("active");
      overlay.classList.remove("active");
    };
    
    // --- Resizing logic ---
    const handles = document.querySelectorAll(".resize-handle");
    
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
              // Adjust left to keep panel's position consistent
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
              // Adjust top to keep panel's position consistent
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
    
    // --- Dragging (Moving) Logic ---
    const header = document.querySelector(".panel-header");
    let isDragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    
    header.addEventListener("mousedown", function(e) {
      // Only allow drag when not clicking on the close button
      if(e.target.id === "closePanel") return;
      
      isDragging = true;
      // Calculate offset between mouse position and panel's top-left corner
      dragOffsetX = e.clientX - sidePanel.offsetLeft;
      dragOffsetY = e.clientY - sidePanel.offsetTop;
      
      // Disable transitions during drag for smoother movement
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
        // Re-enable transitions if needed
        sidePanel.style.transition = "left 0.3s ease";
      }
    });