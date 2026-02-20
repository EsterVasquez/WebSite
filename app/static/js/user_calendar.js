const token = window.BOOKING_TOKEN;
const hasBookingError = window.HAS_BOOKING_ERROR;

const packageSelect = document.getElementById("packageSelect");
const datePicker = document.getElementById("datePicker");
const timeSlotsContainer = document.getElementById("timeSlots");
const confirmBtn = document.getElementById("confirmBtn");
const feedback = document.getElementById("feedback");
const customerNameInput = document.getElementById("customerName");
const customerPhoneInput = document.getElementById("customerPhone");
const customerNotesInput = document.getElementById("customerNotes");

const serviceNameEl = document.getElementById("serviceName");
const packageNameEl = document.getElementById("packageName");
const packageDurationEl = document.getElementById("packageDuration");
const packagePriceEl = document.getElementById("packagePrice");

let selectedTime = null;
let selectedPackageId = null;
let context = null;

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Error inesperado");
    }
    return data;
}

function renderPackageDetails(packageId) {
    const selectedPackage = context.packages.find((item) => item.id === Number(packageId));
    if (!selectedPackage) {
        return;
    }
    packageNameEl.textContent = selectedPackage.name;
    const duration = selectedPackage.duration_minutes || context.service.default_duration_minutes;
    packageDurationEl.textContent = `${duration} min`;
    packagePriceEl.textContent = `$ ${selectedPackage.price}`;
}

function renderPackageOptions() {
    packageSelect.innerHTML = "";
    context.packages.forEach((selectedPackage) => {
        const option = document.createElement("option");
        const duration = selectedPackage.duration_minutes || context.service.default_duration_minutes;
        option.value = selectedPackage.id;
        option.textContent = `${selectedPackage.name} - ${duration} min - $${selectedPackage.price} (anticipo $${selectedPackage.deposit_required})`;
        packageSelect.appendChild(option);
    });

    selectedPackageId = context.selected_package_id || context.packages[0]?.id;
    if (selectedPackageId) {
        packageSelect.value = selectedPackageId;
        renderPackageDetails(selectedPackageId);
    }
}

function applyDateLimits() {
    const serviceMin = context.service.min_booking_date;
    const serviceMax = context.service.max_booking_date;
    const selectedPackage = context.packages.find((item) => item.id === Number(selectedPackageId));

    let minDate = serviceMin;
    let maxDate = serviceMax;
    if (selectedPackage?.available_from && selectedPackage.available_from > minDate) {
        minDate = selectedPackage.available_from;
    }
    if (selectedPackage?.available_until) {
        if (!maxDate || selectedPackage.available_until < maxDate) {
            maxDate = selectedPackage.available_until;
        }
    }

    if (minDate) {
        datePicker.min = minDate;
    }
    if (maxDate) {
        datePicker.max = maxDate;
    } else {
        datePicker.removeAttribute("max");
    }
    if (datePicker.value && minDate && datePicker.value < minDate) {
        datePicker.value = minDate;
    }
    if (datePicker.value && maxDate && datePicker.value > maxDate) {
        datePicker.value = maxDate;
    }
    if (minDate && maxDate && minDate > maxDate) {
        feedback.textContent = "El paquete seleccionado no tiene un rango de fechas válido.";
        confirmBtn.disabled = true;
    }
}

function clearTimeSelection() {
    selectedTime = null;
    confirmBtn.disabled = true;
}

function renderTimeSlots(times) {
    timeSlotsContainer.innerHTML = "";
    if (!times.length) {
        timeSlotsContainer.innerHTML =
            '<p class="text-sm text-red-600 col-span-full">No hay horarios disponibles para ese día.</p>';
        return;
    }
    times.forEach((time) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = time;
        button.className = "border rounded-lg py-2 hover:bg-slate-100";
        button.addEventListener("click", () => {
            document
                .querySelectorAll("#timeSlots button")
                .forEach((item) => item.classList.remove("bg-slate-800", "text-white"));
            button.classList.add("bg-slate-800", "text-white");
            selectedTime = time;
            confirmBtn.disabled = false;
            feedback.textContent = `Horario seleccionado: ${time}`;
        });
        timeSlotsContainer.appendChild(button);
    });
}

async function loadContext() {
    context = await requestJson(`/api/calendar/${token}/context/`);
    serviceNameEl.textContent = context.service.name;
    customerNameInput.value = context.user.name || "";
    customerPhoneInput.value = context.user.phone_number || "";
    renderPackageOptions();
    applyDateLimits();
}

async function loadAvailableTimes() {
    if (!datePicker.value) {
        return;
    }
    clearTimeSelection();
    feedback.textContent = "Cargando horarios...";
    const query = new URLSearchParams({ date: datePicker.value });
    if (selectedPackageId) {
        query.set("package_id", String(selectedPackageId));
    }
    const data = await requestJson(`/api/calendar/${token}/available-times/?${query.toString()}`);
    renderTimeSlots(data.times);
    feedback.textContent = "";
}

async function confirmBooking() {
    if (!selectedTime || !datePicker.value) {
        return;
    }
    if (!customerNameInput.value.trim() || !customerPhoneInput.value.trim()) {
        throw new Error("Debes indicar nombre y teléfono para confirmar la cita.");
    }
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Confirmando...";

    const payload = {
        date: datePicker.value,
        time: selectedTime,
        package_id: selectedPackageId ? Number(selectedPackageId) : null,
        customer_name: customerNameInput.value.trim(),
        customer_phone: customerPhoneInput.value.trim(),
        customer_notes: customerNotesInput?.value.trim() || "",
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
    if (hasBookingError) {
        return;
    }
    await loadContext();
    const today = new Date().toISOString().slice(0, 10);
    const minDate = datePicker.min || today;
    datePicker.value = minDate > today ? minDate : today;
    applyDateLimits();
    await loadAvailableTimes();
}

packageSelect?.addEventListener("change", async (event) => {
    selectedPackageId = Number(event.target.value);
    renderPackageDetails(selectedPackageId);
    applyDateLimits();
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

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await bootstrap();
    } catch (error) {
        feedback.textContent = error.message;
    }
});
