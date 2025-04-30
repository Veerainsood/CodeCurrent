function rotateAndReload(btn) {
    const icon = btn.querySelector('i');
    icon.classList.add('spin-once');
  
    setTimeout(() => {
      location.reload();
    }, 500);
  }
  
  function toggleDarkMode() {
    document.body.classList.toggle("light");
  
    // Save correct mode
    const isLight = document.body.classList.contains("light");
    localStorage.setItem("theme", isLight ? "light" : "dark");
  
    updateToggleIcon();
  }
  
  function updateToggleIcon() {
    const icon = document.querySelector('.toggle-btn i');
    const isLight = document.body.classList.contains("light");
  
    if (isLight) {
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon'); // moon = light mode icon
    } else {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun'); // sun = dark mode icon
    }
  }
  
  // Load theme on startup
  window.addEventListener("DOMContentLoaded", () => {
    document.querySelector('.toggle-btn').addEventListener('click', toggleDarkMode);
  });
  
  
export {toggleDarkMode,rotateAndReload}