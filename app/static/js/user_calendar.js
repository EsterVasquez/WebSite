const datePicker = document.getElementById("datePicker");
const timeSlotsContainer = document.getElementById("timeSlots");
const confirmBtn = document.getElementById("confirmBtn");

let selectedTime = null;
const BOOKING_ID = "{{ booking_id }}";

datePicker.addEventListener("change", async () => {
  const date = datePicker.value;
  selectedTime = null;
  confirmBtn.disabled = true;
  confirmBtn.classList.add("opacity-50", "cursor-not-allowed");

  timeSlotsContainer.innerHTML = `
    <p class="text-gray-400 col-span-full text-center">
      Cargando horarios...
    </p>
  `;

  const response = await fetch(
    `/api/available-times?date=${date}&booking_id=${BOOKING_ID}`
  );
  const data = await response.json();

  timeSlotsContainer.innerHTML = "";

  if (data.times.length === 0) {
    timeSlotsContainer.innerHTML = `
      <p class="text-red-500 col-span-full text-center">
        No hay horarios disponibles este día
      </p>
    `;
    return;
  }

  data.times.forEach(time => {
    const btn = document.createElement("button");
    btn.textContent = time;
    btn.className = `
      py-2 rounded-lg border
      hover:bg-blue-50
    `;

    btn.onclick = () => {
      document.querySelectorAll("#timeSlots button")
        .forEach(b => b.classList.remove("bg-blue-600", "text-white"));

      btn.classList.add("bg-blue-600", "text-white");
      selectedTime = time;

      confirmBtn.disabled = false;
      confirmBtn.classList.remove("opacity-50", "cursor-not-allowed");
    };

    timeSlotsContainer.appendChild(btn);
  });
});

confirmBtn.addEventListener("click", async () => {
  if (!selectedTime) return;

  confirmBtn.textContent = "Confirmando...";
  confirmBtn.disabled = true;

  await fetch("/api/confirm-booking/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      booking_id: BOOKING_ID,
      date: datePicker.value,
      time: selectedTime
    })
  });

  window.location.href = "/booking-success/";
});
