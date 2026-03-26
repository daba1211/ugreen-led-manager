const DEFAULT_CONFIG = {
    power: { r: 0, g: 0, b: 255, brightness: 255 },
    netdev: { r: 0, g: 255, b: 0, brightness: 255 },
    disk1: {
        active: { r: 0, g: 255, b: 0, brightness: 255 },
        standby: { r: 255, g: 165, b: 0, brightness: 96 },
        error: { r: 255, g: 0, b: 0, brightness: 255 }
    },
    disk2: {
        active: { r: 0, g: 255, b: 0, brightness: 255 },
        standby: { r: 255, g: 165, b: 0, brightness: 96 },
        error: { r: 255, g: 0, b: 0, brightness: 255 }
    },
    disk3: {
        active: { r: 0, g: 255, b: 0, brightness: 255 },
        standby: { r: 255, g: 165, b: 0, brightness: 96 },
        error: { r: 255, g: 0, b: 0, brightness: 255 }
    },
    disk4: {
        active: { r: 0, g: 255, b: 0, brightness: 255 },
        standby: { r: 255, g: 165, b: 0, brightness: 96 },
        error: { r: 255, g: 0, b: 0, brightness: 255 }
    }
};

const I18N = {
    de: {
        title: "UGREEN LED Manager",
        subtitle: "LED-Konfiguration für UGREEN DXP",
        status: "Status",
        general: "Allgemein",
        disks: "Disks",
        result: "Antwort",
        save: "Speichern",
        off: "Alles aus",
        apply: "Speichern & Anwenden",
        power: "Power",
        network: "Netzwerk",
        active: "Aktiv",
        standby: "Standby",
        error: "Fehler",
        color: "Farbe",
        brightness: "Helligkeit",
        responseEmpty: "Noch keine Aktion ausgeführt.",
        loadingStatus: "Lade Status ...",
        mode: "Modus",
        state: "Status",
        ready: "bereit",
        notReady: "nicht bereit",
        cli: "CLI",
        diskLabel: "Disk",
        saveOk: "Konfiguration gespeichert.",
        rangeHint: "0 = aus, 255 = maximal"
    },
    en: {
        title: "UGREEN LED Manager",
        subtitle: "LED configuration for UGREEN DXP",
        status: "Status",
        general: "General",
        disks: "Disks",
        result: "Response",
        save: "Save",
        off: "All off",
        apply: "Save & Apply",
        power: "Power",
        network: "Network",
        active: "Active",
        standby: "Standby",
        error: "Error",
        color: "Color",
        brightness: "Brightness",
        responseEmpty: "No action executed yet.",
        loadingStatus: "Loading status ...",
        mode: "Mode",
        state: "State",
        ready: "ready",
        notReady: "not ready",
        cli: "CLI",
        diskLabel: "Disk",
        saveOk: "Configuration saved.",
        rangeHint: "0 = off, 255 = maximum"
    }
};

let currentConfig = structuredClone(DEFAULT_CONFIG);
let currentLang = localStorage.getItem("led-manager-lang")
    || (navigator.language && navigator.language.toLowerCase().startsWith("de") ? "de" : "en");

function t(key) {
    return I18N[currentLang][key] || key;
}

function deepMerge(base, update) {
    const result = structuredClone(base);

    for (const [key, value] of Object.entries(update || {})) {
        if (
            result[key] &&
            typeof result[key] === "object" &&
            !Array.isArray(result[key]) &&
            value &&
            typeof value === "object" &&
            !Array.isArray(value)
        ) {
            result[key] = deepMerge(result[key], value);
        } else {
            result[key] = value;
        }
    }

    return result;
}

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

function clampBrightness(value) {
    const n = Number(value);
    if (Number.isNaN(n)) return 255;
    return Math.max(0, Math.min(255, Math.round(n)));
}

function getNodeByPath(obj, path) {
    return path.split(".").reduce((acc, part) => acc[part], obj);
}

function baseId(path) {
    return path.replaceAll(".", "-");
}

function renderControlRow(path, label) {
    const id = baseId(path);

    return `
        <div class="control-row">
            <div class="control-label">${label}</div>
            <div class="control-main">
                <div class="color-line">
                    <span class="helper-text">${t("color")}</span>
                    <input type="color" id="${id}-color">
                    <span class="preview" id="${id}-preview"></span>
                </div>
                <div class="brightness-line">
                    <span class="helper-text">${t("brightness")}</span>
                    <input type="range" min="0" max="255" id="${id}-brightness-range">
                    <input type="number" min="0" max="255" id="${id}-brightness-number">
                    <span class="helper-text">${t("rangeHint")}</span>
                </div>
            </div>
        </div>
    `;
}

function renderUI() {
    document.getElementById("titleText").textContent = t("title");
    document.getElementById("subtitleText").textContent = t("subtitle");
    document.getElementById("statusHeading").textContent = t("status");
    document.getElementById("generalHeading").textContent = t("general");
    document.getElementById("diskHeading").textContent = t("disks");
    document.getElementById("resultHeading").textContent = t("result");

    document.getElementById("saveBtn").textContent = t("save");
    document.getElementById("offBtn").textContent = t("off");
    document.getElementById("applyBtn").textContent = t("apply");

    document.getElementById("langDeBtn").classList.toggle("active", currentLang === "de");
    document.getElementById("langEnBtn").classList.toggle("active", currentLang === "en");

    document.getElementById("generalControls").innerHTML = [
        renderControlRow("power", t("power")),
        renderControlRow("netdev", t("network"))
    ].join("");

    const diskCards = [];
    for (let i = 1; i <= 4; i++) {
        diskCards.push(`
            <div class="disk-card">
                <h3>${t("diskLabel")} ${i}</h3>
                ${renderControlRow(`disk${i}.active`, t("active"))}
                ${renderControlRow(`disk${i}.standby`, t("standby"))}
                ${renderControlRow(`disk${i}.error`, t("error"))}
            </div>
        `);
    }

    document.getElementById("diskGrid").innerHTML = diskCards.join("");
    fillControlsFromConfig();
    bindControlEvents();
}

function fillControl(path) {
    const id = baseId(path);
    const node = getNodeByPath(currentConfig, path);
    document.getElementById(`${id}-color`).value = rgbToHex(node);
    document.getElementById(`${id}-brightness-range`).value = clampBrightness(node.brightness);
    document.getElementById(`${id}-brightness-number`).value = clampBrightness(node.brightness);
    document.getElementById(`${id}-preview`).style.backgroundColor = rgbToHex(node);
}

function fillControlsFromConfig() {
    fillControl("power");
    fillControl("netdev");

    for (let i = 1; i <= 4; i++) {
        fillControl(`disk${i}.active`);
        fillControl(`disk${i}.standby`);
        fillControl(`disk${i}.error`);
    }
}

function bindBrightnessSync(id) {
    const range = document.getElementById(`${id}-brightness-range`);
    const number = document.getElementById(`${id}-brightness-number`);

    range.addEventListener("input", () => {
        number.value = clampBrightness(range.value);
    });

    number.addEventListener("input", () => {
        const value = clampBrightness(number.value);
        number.value = value;
        range.value = value;
    });
}

function bindColorPreview(id) {
    const color = document.getElementById(`${id}-color`);
    const preview = document.getElementById(`${id}-preview`);

    color.addEventListener("input", () => {
        preview.style.backgroundColor = color.value;
    });
}

function bindControlEvents() {
    const ids = [
        "power",
        "netdev",
        "disk1-active", "disk1-standby", "disk1-error",
        "disk2-active", "disk2-standby", "disk2-error",
        "disk3-active", "disk3-standby", "disk3-error",
        "disk4-active", "disk4-standby", "disk4-error"
    ];

    ids.forEach(id => {
        bindBrightnessSync(id);
        bindColorPreview(id);
    });
}

async function loadStatus() {
    document.getElementById("statusText").textContent = t("loadingStatus");

    const res = await fetch("/api/status");
    const data = await res.json();

    const readyText = data.ready ? t("ready") : t("notReady");
    const cliText = data.cli_path ? ` | ${t("cli")}: ${data.cli_path}` : "";

    document.getElementById("statusText").textContent =
        `${t("mode")}: ${data.mode} | ${t("state")}: ${readyText}${cliText}`;
}

async function loadConfig() {
    const res = await fetch("/api/config");
    const cfg = await res.json();
    currentConfig = deepMerge(DEFAULT_CONFIG, cfg);
    fillControlsFromConfig();
}

function collectControl(path) {
    const id = baseId(path);
    return {
        ...hexToRgb(document.getElementById(`${id}-color`).value),
        brightness: clampBrightness(document.getElementById(`${id}-brightness-number`).value)
    };
}

function collectConfig() {
    return {
        power: collectControl("power"),
        netdev: collectControl("netdev"),
        disk1: {
            active: collectControl("disk1.active"),
            standby: collectControl("disk1.standby"),
            error: collectControl("disk1.error")
        },
        disk2: {
            active: collectControl("disk2.active"),
            standby: collectControl("disk2.standby"),
            error: collectControl("disk2.error")
        },
        disk3: {
            active: collectControl("disk3.active"),
            standby: collectControl("disk3.standby"),
            error: collectControl("disk3.error")
        },
        disk4: {
            active: collectControl("disk4.active"),
            standby: collectControl("disk4.standby"),
            error: collectControl("disk4.error")
        }
    };
}

async function saveConfig() {
    currentConfig = collectConfig();

    const res = await fetch("/api/config", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(currentConfig)
    });

    const result = await res.json();
    document.getElementById("resultBox").textContent = JSON.stringify({
        message: t("saveOk"),
        ...result
    }, null, 2);
}

async function applyConfig() {
    await saveConfig();

    const res = await fetch("/api/apply", {
        method: "POST"
    });

    const result = await res.json();
    document.getElementById("resultBox").textContent = JSON.stringify(result, null, 2);
}

async function allOff() {
    const res = await fetch("/api/off", {
        method: "POST"
    });

    const result = await res.json();
    document.getElementById("resultBox").textContent = JSON.stringify(result, null, 2);
}

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("led-manager-lang", lang);
    renderUI();
    loadStatus();
}

document.getElementById("saveBtn").addEventListener("click", saveConfig);
document.getElementById("applyBtn").addEventListener("click", applyConfig);
document.getElementById("offBtn").addEventListener("click", allOff);
document.getElementById("langDeBtn").addEventListener("click", () => setLanguage("de"));
document.getElementById("langEnBtn").addEventListener("click", () => setLanguage("en"));

renderUI();
loadStatus();
loadConfig();
document.getElementById("resultBox").textContent = t("responseEmpty");
