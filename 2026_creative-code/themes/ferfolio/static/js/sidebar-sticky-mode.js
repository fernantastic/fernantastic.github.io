(() => {
  const sidebar = document.querySelector(".sidebar");

  if (!sidebar) {
    return;
  }

  const updateSidebarStickyMode = () => {
    const isSidebarTallerThanViewport = sidebar.offsetHeight > window.innerHeight;

    if (isSidebarTallerThanViewport) {
      sidebar.style.top = "auto";
      sidebar.style.bottom = "0";
      sidebar.style.alignSelf = "end";
      return;
    }

    sidebar.style.backgroundColor = "";
    sidebar.style.top = "0";
    sidebar.style.bottom = "auto";
    sidebar.style.alignSelf = "start";
  };

  updateSidebarStickyMode();
  window.addEventListener("load", updateSidebarStickyMode);
  window.addEventListener("resize", updateSidebarStickyMode);

  if ("ResizeObserver" in window) {
    const resizeObserver = new ResizeObserver(updateSidebarStickyMode);
    resizeObserver.observe(sidebar);
  }
})();
