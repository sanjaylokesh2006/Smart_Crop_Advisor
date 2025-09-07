const btn = document.getElementById("btn");
const result = document.getElementById("result");

btn.addEventListener("click", async () => {
  const city = document.getElementById("city").value.trim();
  if (!city) {
    result.textContent = "Please enter a city name.";
    return;
  }

  result.textContent = "Loading…";

  try {
    const res = await fetch("http://127.0.0.1:8000/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city })
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errText}`);
    }

    const data = await res.json();
    result.innerHTML = `
      <p><strong>Crop:</strong> ${data.recommended_crop}</p>
      <p><strong>Soil pH:</strong> ${data.ph.toFixed(2)}</p>
      <p><strong>Temp:</strong> ${data.temperature} °C</p>
      <hr>
      <h3>🌫️ Air Quality</h3>
      <p><strong>AQI:</strong> ${data.air_quality.aqi}</p>
      <ul>
        ${Object.entries(data.air_quality.pollutants).map(
          ([key, val]) => `<li>${key}: ${val ?? "N/A"}</li>`
        ).join("")}
      </ul>
      <hr>
      <h3>🌪️ Disaster Alerts</h3>
      ${data.disaster_alerts.length === 0
        ? "<p>No current alerts.</p>"
        : data.disaster_alerts.map(alert => `
            <p><strong>${alert.type}</strong> (${alert.severity})<br>
            ${alert.description}</p>
          `).join("")}
    `;
  } catch (e) {
    result.textContent = "Error: " + e.message;
    console.error(e);
  }
});
