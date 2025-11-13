console.log("✅ sidebar.js loaded successfully");

document.addEventListener("DOMContentLoaded", () => {
  // Watch for clicks on any .ucr-btn
  document.body.addEventListener("click", (e) => {
    const btn = e.target.closest(".ucr-btn");
    if (!btn) return;

    const threadId = btn.dataset.thread;
    if (window?.chat && threadId) {
      // Send special message to backend
      window.chat.sendMessage(`resume:${threadId}`);
    }
  });
});
