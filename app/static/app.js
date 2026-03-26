function rgbToHex(c) {
    return "#" + [c.r, c.g, c.b]
        .map(v => Number(v).toString(16).padStart(2, "0"))
        .join("");
}

function hexToRgb(hex) {
    const value = parseInt(hex.slice(1), 16);
    return {
        r: (value >> 16) & 255,
        g: (value >> 8) & 255,
        b: value & 255
    };
}

function setPreview(id) {
    const input = document.getElementById(id);
    const preview = document.getElementById(`preview-${id}`);
    if (input && preview) {
        preview.style.backgroundColor = input.value;
    }
}

function updateAllPreviews() {
    const ids = [
        "power",
        "netdev",
        "disk1-active", "disk1-standby", "disk1-error",
        "disk2-active", "disk2-standby", "disk2-error",
        "disk3-active", "disk3-standby", "disk3-error",
        "disk4-active", "disk4-standby", "disk4-error"
    ];

    ids.forEach(setPreview);
}

function bindPreviewEvents() {
    document.querySelectorAll('input[type="color"]').forEach(input => {
        input.addEventListener("input", () => {
            setPreview(input.id);
        });
    });
}

async function loadStatus() {
    const res = await fetch("/api/status");
    const data = await res.json();

    const statusText = document.getElementById("statusText");
    const mode = data.mode || "unknown";
    const ready = data.ready ? "bereit" : "nicht bereit";
    const cliPath = data.cli_path ? ` | CLI: ${data.cli_path}` : "";

    statusText.textContent = `Modus: ${mode} | Status: ${ready}${cliPath}`;
}

async function loadConfig() {
    const res = await fetch("/api/config");
    const cfg = await res.json();

    document.getElementById("power").value = rgbToHex(cfg.power);
    document.getElementById("netdev").value = rgbToHex(cfg.netdev);

    for (const disk of ["disk1", "disk2", "disk3", "disk4"]) {
        document.getElementById(`${disk}-active`).value = rgbToHex(cfg[disk].active);
        document.getElementById(`${disk}-standby`).value = rgbToHex(cfg[disk].standby);
        document.getElementById(`${disk}-error`).value = rgbToHex(cfg[disk].error);
    }

    updateAllPreviews();
}

function collectConfig() {
    const config = {
        power: hexToRgb(document.getElementById("power").value),
        netdev: hexToRgb(document.getElementById("netdev").value)
    };

    for (const disk of ["disk1", "disk2", "disk3", "disk4"]) {
        config[disk] = {
            active: hexToRgb(document.getElementById(`${disk}-active`).value),
            standby: hexToRgb(document.getElementById(`${disk}-standby`).value),
            error: hexToRgb(document.getElementById(`${disk}-error`).value)
        };
    }

    return config;
}

async function saveConfig() {
    const config = collectConfig();

    const res = await fetch("/api/config", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(config)
    });

    const result = await res.json();
    document.getElementById("resultBox").textContent = JSON.stringify(result, null, 2);
}

async function applyConfig() {
    await saveConfig();

    const res = await fetch("/api/apply", {
        method: "POST"
    });

    const result = await res.json();
    document.getElementById("resultBox").textContent = JSON.stringify(result, null, 2);
}

document.getElementById("saveBtn").addEventListener("click", saveConfig);
document.getElementById("applyBtn").addEventListener("click", applyConfig);

bindPreviewEvents();
loadStatus();
loadConfig();
