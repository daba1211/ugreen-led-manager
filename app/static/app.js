async function loadStatus() {
    const res = await fetch("/api/status");
    const data = await res.json();
    document.getElementById("statusBox").textContent =
        JSON.stringify(data, null, 2);
}

loadStatus();
