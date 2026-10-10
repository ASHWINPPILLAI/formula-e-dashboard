import * as THREE from 'three';
import Chart from 'chart.js/auto';
import { sceneState, initScene, triggerSensorFault } from './scene.js';

// ---------------------------------------------------------------------------
// DOM Elements
// ---------------------------------------------------------------------------
const form = document.getElementById("telemetry-form");
const submitBtn = document.getElementById("submit-btn");
const errorBnr = document.getElementById("error-banner");
const faultBnr = document.getElementById("sensor-fault-banner");
const loadingInd = document.getElementById("loading-indicator");

// Results UI
const scoreBadge = document.getElementById("score-badge");
const ratingLabel = document.getElementById("rating-label");
const fbList = document.getElementById("feedback-list");
const ringPath = document.getElementById("ring-path");

// Chart UI
const chartCanvas = document.getElementById("chart-canvas");
let telemetryChart = null;

// Inputs
const iLap = document.getElementById("lap_number");
const iT3Num = document.getElementById("turn_3_regen_kw");
const iT3Rng = document.getElementById("turn_3_regen_kw_range");
const iT13Num = document.getElementById("turn_13_regen_kw");
const iT13Rng = document.getElementById("turn_13_regen_kw_range");
const iLcNum = document.getElementById("lift_coast_distance_meters");
const iLcRng = document.getElementById("lift_coast_distance_meters_range");

// ---------------------------------------------------------------------------
// Sync Inputs & 3D Scene
// ---------------------------------------------------------------------------
function syncInput(numEl, rngEl, stateKey) {
  const update = (val) => {
    let v = parseFloat(val) || 0;
    if (v < 0) v = 0;
    numEl.value = v;
    rngEl.value = v;
    sceneState[stateKey] = v;
  };
  numEl.addEventListener("input", (e) => update(e.target.value));
  rngEl.addEventListener("input", (e) => update(e.target.value));
  update(numEl.value);
}

syncInput(iT3Num, iT3Rng, "t3Kw");
syncInput(iT13Num, iT13Rng, "t13Kw");
syncInput(iLcNum, iLcRng, "liftCoastMeters");

// ---------------------------------------------------------------------------
// UI Helpers
// ---------------------------------------------------------------------------
function showError(msg) {
  errorBnr.textContent = msg;
  errorBnr.style.display = "block";
}
function hideError() {
  errorBnr.style.display = "none";
  faultBnr.style.display = "none";
}

function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    obj.innerHTML = Math.floor(progress * (end - start) + start);
    if (progress < 1) window.requestAnimationFrame(step);
    else obj.innerHTML = end;
  };
  window.requestAnimationFrame(step);
}

function animateRing(score) {
    // 283 is the stroke-dasharray circumference for r=45
    const offset = 283 - (283 * (score / 100));
    ringPath.style.strokeDashoffset = offset;
    
    // Change color based on score
    if (score >= 85) ringPath.style.stroke = 'var(--neon-green)';
    else if (score >= 60) ringPath.style.stroke = 'var(--gold)';
    else ringPath.style.stroke = 'var(--crimson)';
}

function updateChart(t3, t13, lc) {
    if (telemetryChart) telemetryChart.destroy();
    
    // Chart.js styling for Cyberpunk Bento UI
    Chart.defaults.color = '#8a7b7e';
    Chart.defaults.font.family = "'JetBrains Mono', monospace";
    
    telemetryChart = new Chart(chartCanvas, {
        type: 'bar',
        data: {
            labels: ['T3 REGEN', 'T13 REGEN', 'LIFT & COAST'],
            datasets: [{
                data: [t3, t13, lc],
                backgroundColor: [
                    t3 >= 600 ? '#ffffff' : (t3 >= 500 ? '#ff1e3c' : '#4a0510'),
                    t13 >= 600 ? '#ffffff' : (t13 >= 500 ? '#ff1e3c' : '#4a0510'),
                    lc >= 50 ? '#ff1e3c' : '#4a0510'
                ],
                borderColor: 'rgba(255, 30, 60, 0.5)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutExpo'
            }
        }
    });
}

// ---------------------------------------------------------------------------
// Form Submission & API call
// ---------------------------------------------------------------------------
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  
  submitBtn.disabled = true;
  loadingInd.classList.add("active");

  const payload = {
    driver_id: document.getElementById("driver_id").value.trim(),
    lap_number: parseInt(iLap.value, 10),
    turn_3_regen_kw: parseFloat(iT3Num.value),
    turn_13_regen_kw: parseFloat(iT13Num.value),
    lift_coast_distance_meters: parseFloat(iLcNum.value),
  };

  try {
    const res = await fetch("/api/v1/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => null);
      throw new Error(detail?.detail?.[0]?.msg || detail?.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    loadingInd.classList.remove("active");

    // Sync state for scene
    sceneState.efficiencyScore = data.efficiency_score;
    sceneState.historicalAvg = data.historical_average_score || 50;
    sceneState.sensorFault = data.sensor_fault_detected;

    if (data.sensor_fault_detected) {
      faultBnr.style.display = "block";
      triggerSensorFault();
    }

    // UI Updates
    animateValue(scoreBadge, 0, data.efficiency_score, 1000);
    animateRing(data.efficiency_score);

    const delta = data.score_delta;
    const deltaStr = delta > 0 ? `+${delta}` : `${delta}`;
    const deltaColor = delta > 0 ? 'var(--neon-green)' : (delta < 0 ? 'var(--crimson)' : 'var(--gold)');
    ratingLabel.innerHTML = `${data.rating.replace("_", " ")} <span style="font-size: 0.7em; color: ${deltaColor}">[${deltaStr} vs Avg]</span>`;

    // Feedback Terminal
    fbList.innerHTML = "";
    if (data.feedback.length === 0) {
      fbList.innerHTML = `<li>[SYS_OK] Perfect lap execution. No feedback generated.</li>`;
    } else {
      data.feedback.forEach((fb) => {
        const li = document.createElement("li");
        li.textContent = fb;
        if (fb.toLowerCase().includes("sensor fault")) li.classList.add("warning");
        fbList.appendChild(li);
      });
    }

    updateChart(payload.turn_3_regen_kw, payload.turn_13_regen_kw, payload.lift_coast_distance_meters);

  } catch (err) {
    loadingInd.classList.remove("active");
    showError("Request failed: " + err.message);
  } finally {
    submitBtn.disabled = false;
  }
});

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
initScene();

function connectWebSocket() {
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${wsProto}//${window.location.host}/ws/telemetry`);
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (!document.getElementById("submit-btn").disabled) {
                sceneState.efficiencyScore = data.efficiency_score;
                sceneState.historicalAvg = data.historical_average_score || 50;
            }
        } catch(e) {}
    };
    
    ws.onclose = () => setTimeout(connectWebSocket, 5000);
}
connectWebSocket();
