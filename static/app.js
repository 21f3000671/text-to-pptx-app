
const form = document.getElementById("genForm");
const statusEl = document.getElementById("status");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  statusEl.textContent = "Generating… this can take a moment depending on your model.";
  const fd = new FormData(form);

  try {
    const res = await fetch(form.action, { method: "POST", body: fd });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const msg = data.detail || `Server error (${res.status})`;
      statusEl.textContent = "";
      alert(msg);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "generated.pptx";
    a.click();
    URL.revokeObjectURL(url);
    statusEl.textContent = "Done! Your download should begin automatically.";
  } catch (err) {
    statusEl.textContent = "";
    alert("Network error: " + err);
  }
});
