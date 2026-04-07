(() => {
  const cornerRoot = document.querySelector(".corner-gif");
  const sidebarContent = document.querySelector(".sidebar-content");

  if (cornerRoot && sidebarContent) {
    const footerList = sidebarContent.querySelector("ul:last-of-type");
    if (footerList) {
      const row = document.createElement("div");
      row.className = "sidebar-footer-row";
      footerList.parentNode.insertBefore(row, footerList);
      row.appendChild(footerList);
      row.appendChild(cornerRoot);
    }
  }

  const setupCornerGif = async () => {
    if (!cornerRoot) return;
    const canvas = cornerRoot.querySelector(".corner-gif-canvas");
    if (!canvas) return;

    let gifPaths = [];
    try {
      gifPaths = JSON.parse(cornerRoot.dataset.cornerGifs || "[]");
    } catch (error) {
      console.error("Failed to parse corner gif list", error);
      return;
    }
    if (!gifPaths.length) return;
    if (!("ImageDecoder" in window)) return;

    const storageKey = "cornerGifIndex";
    let chosenIndex = 0;
    try {
      const storedIndex = Number(window.localStorage.getItem(storageKey) || "0");
      chosenIndex = ((storedIndex % gifPaths.length) + gifPaths.length) % gifPaths.length;
      window.localStorage.setItem(storageKey, String((chosenIndex + 1) % gifPaths.length));
    } catch (_error) {
      const fallbackSeed = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      let hash = 0;
      for (let i = 0; i < fallbackSeed.length; i += 1) {
        hash = (hash * 31 + fallbackSeed.charCodeAt(i)) >>> 0;
      }
      chosenIndex = hash % gifPaths.length;
    }
    const chosenPath = gifPaths[chosenIndex];
    const response = await fetch(chosenPath);
    if (!response.ok) {
      throw new Error(`Failed to load ${chosenPath}`);
    }

    const bytes = await response.arrayBuffer();
    const type = response.headers.get("content-type") || "image/gif";
    const decoder = new ImageDecoder({ data: bytes, type });
    await decoder.tracks.ready;

    const track = decoder.tracks.selectedTrack;
    const frameCount = Math.max(1, track.frameCount || 1);
    const frames = [];

    for (let i = 0; i < frameCount; i += 1) {
      const result = await decoder.decode({ frameIndex: i });
      frames.push(result.image);
    }

    const firstFrame = frames[0];
    const dpr = window.devicePixelRatio || 1;
    canvas.width = firstFrame.displayWidth * dpr;
    canvas.height = firstFrame.displayHeight * dpr;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    const maxScroll = () => Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    const frameIndexForScroll = () => {
      const progress = window.scrollY / maxScroll();
      const loopedProgress = (progress * 1.4) % 1;
      return Math.min(frameCount - 1, Math.floor(loopedProgress * frameCount));
    };

    const render = () => {
      const frame = frames[frameIndexForScroll()];
      ctx.clearRect(0, 0, firstFrame.displayWidth, firstFrame.displayHeight);
      ctx.drawImage(frame, 0, 0, firstFrame.displayWidth, firstFrame.displayHeight);
    };

    render();
    window.addEventListener("scroll", render, { passive: true });
    window.addEventListener("resize", render);
  };

  setupCornerGif().catch((error) => {
    console.error("Failed to set up corner gif", error);
  });
})();
