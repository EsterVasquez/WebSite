const token = window.BOOKING_TOKEN;
const hasBookingError = window.HAS_BOOKING_ERROR;

const tierSelect = document.getElementById("tierSelect");
const datePicker = document.getElementById("datePicker");
const timeSlotsContainer = document.getElementById("timeSlots");
const confirmBtn = document.getElementById("confirmBtn");
const feedback = document.getElementById("feedback");

const serviceNameEl = document.getElementById("serviceName");
const tierNameEl = document.getElementById("tierName");
const tierDurationEl = document.getElementById("tierDuration");
const tierPriceEl = document.getElementById("tierPrice");

let selectedTime = null;
let selectedTierId = null;
let context = null;

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Error inesperado");
    }
    return data;
}

function renderTierDetails(tierId) {
    const tier = context.tiers.find((item) => item.id === Number(tierId));
    if (!tier) return;
    tierNameEl.textContent = tier.name;
    tierDurationEl.textContent = `${tier.duration_minutes} min`;
    tierPriceEl.textContent = `$ ${tier.price}`;
}

function renderTierOptions() {
    tierSelect.innerHTML = "";
    context.tiers.forEach((tier) => {
        const option = document.createElement("option");
        option.value = tier.id;
        option.textContent = `${tier.name} - ${tier.duration_minutes} min - $${tier.price}`;
        tierSelect.appendChild(option);
    });

    selectedTierId = context.selected_tier_id || context.tiers[0]?.id;
    if (selectedTierId) {
        tierSelect.value = selectedTierId;
        renderTierDetails(selectedTierId);
    }
}

function clearTimeSelection() {
    selectedTime = null;
    confirmBtn.disabled = true;
}

function renderTimeSlots(times) {
    timeSlotsContainer.innerHTML = "";
    if (times.length === 0) {
        timeSlotsContainer.innerHTML =
            '<p class="text-sm text-red-600 col-span-full">No hay horarios disponibles para ese día.</p>';
        return;
    }

    times.forEach((time) => {
        const button = document.createElement("button");
        button.textContent = time;
        button.className = "border rounded-lg py-2 hover:bg-slate-100";
        button.onclick = () => {
            document
                .querySelectorAll("#timeSlots button")
                .forEach((item) => item.classList.remove("bg-slate-800", "text-white"));
            button.classList.add("bg-slate-800", "text-white");
            selectedTime = time;
            confirmBtn.disabled = false;
            feedback.textContent = `Horario seleccionado: ${time}`;
        };
        timeSlotsContainer.appendChild(button);
    });
}

async function loadContext() {
    context = await requestJson(`/api/calendar/${token}/context/`);
    serviceNameEl.textContent = context.service.name;
    renderTierOptions();
}

async function loadAvailableTimes() {
    const date = datePicker.value;
    if (!date) return;
    clearTimeSelection();
    feedback.textContent = "Cargando horarios...";
    timeSlotsContainer.innerHTML = '<p class="text-sm text-slate-500 col-span-full">Cargando...</p>';

    const data = await requestJson(
        `/api/calendar/${token}/available-times/?date=${date}&tier_id=${selectedTierId}`
    );
    renderTimeSlots(data.times);
    feedback.textContent = "";
}

async function confirmBooking() {
    if (!selectedTime || !datePicker.value) return;
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Confirmando...";

    const payload = {
        date: datePicker.value,
        time: selectedTime,
        tier_id: Number(selectedTierId),
    };

    const data = await requestJson(`/api/calendar/${token}/confirm/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    feedback.textContent = `Cita registrada para ${data.booking.date} a las ${data.booking.time}.`;
    confirmBtn.textContent = "Cita confirmada";
}

async function bootstrap() {
    if (hasBookingError) return;
    try {
        await loadContext();

        const today = new Date();
        datePicker.value = today.toISOString().slice(0, 10);
        datePicker.min = today.toISOString().slice(0, 10);
        await loadAvailableTimes();
    } catch (error) {
        feedback.textContent = error.message;
    }
}

tierSelect?.addEventListener("change", async (event) => {
    selectedTierId = Number(event.target.value);
    renderTierDetails(selectedTierId);
    await loadAvailableTimes();
});

datePicker?.addEventListener("change", loadAvailableTimes);
confirmBtn?.addEventListener("click", async () => {
    try {
        await confirmBooking();
    } catch (error) {
        feedback.textContent = error.message;
        confirmBtn.textContent = "Confirmar cita";
        confirmBtn.disabled = false;
    }
});

document.addEventListener("DOMContentLoaded", bootstrap);
