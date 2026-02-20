const token = window.BOOKING_TOKEN;
const hasBookingError = window.HAS_BOOKING_ERROR;

const packageSelect = document.getElementById("packageSelect");
const datePicker = document.getElementById("datePicker");
const daysGrid = document.getElementById("daysGrid");
const calendarMonthLabel = document.getElementById("calendarMonthLabel");
const prevMonthBtn = document.getElementById("prevMonthBtn");
const nextMonthBtn = document.getElementById("nextMonthBtn");
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

const dayConfirmModal = document.getElementById("dayConfirmModal");
const dayConfirmText = document.getElementById("dayConfirmText");
const cancelDayConfirmBtn = document.getElementById("cancelDayConfirmBtn");
const acceptDayConfirmBtn = document.getElementById("acceptDayConfirmBtn");
const toastSuccess = document.getElementById("toastSuccess");

let selectedTime = null;
let selectedPackageId = null;
let context = null;
let currentMonth = null;
let currentDaysData = {};
let pendingDaySelection = null;

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Error inesperado");
    }
    return data;
}

function toast(message) {
    toastSuccess.textContent = message;
    toastSuccess.classList.remove("hidden");
    setTimeout(() => toastSuccess.classList.add("hidden"), 2800);
}

function formatDateLabel(isoDate) {
    const date = new Date(`${isoDate}T00:00:00`);
    return date.toLocaleDateString("es-MX", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
    });
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

    selectedPackageId = context.selected_package_id || context.packages[0]?.id || null;
    if (selectedPackageId) {
        packageSelect.value = selectedPackageId;
        renderPackageDetails(selectedPackageId);
    }
}

function minDate() {
    const serviceMin = context.service.min_booking_date;
    const selectedPackage = context.packages.find((item) => item.id === Number(selectedPackageId));
    if (!selectedPackage?.available_from) {
        return serviceMin;
    }
    return selectedPackage.available_from > serviceMin ? selectedPackage.available_from : serviceMin;
}

function maxDate() {
    const serviceMax = context.service.max_booking_date;
    const selectedPackage = context.packages.find((item) => item.id === Number(selectedPackageId));
    if (!selectedPackage?.available_until) {
        return serviceMax;
    }
    if (!serviceMax) {
        return selectedPackage.available_until;
    }
    return selectedPackage.available_until < serviceMax ? selectedPackage.available_until : serviceMax;
}

function dateWithinRange(isoDate) {
    const min = minDate();
    const max = maxDate();
    if (min && isoDate < min) return false;
    if (max && isoDate > max) return false;
    return true;
}

function showDayConfirmModal(isoDate) {
    pendingDaySelection = isoDate;
    dayConfirmText.textContent = `¿Estás seguro de que deseas reservar tu cita para el día ${formatDateLabel(isoDate)}?`;
    dayConfirmModal.classList.remove("hidden");
    dayConfirmModal.classList.add("flex");
}

function hideDayConfirmModal() {
    pendingDaySelection = null;
    dayConfirmModal.classList.add("hidden");
    dayConfirmModal.classList.remove("flex");
}

async function loadAvailableDays() {
    if (!currentMonth) return;
    const query = new URLSearchParams({
        year: String(currentMonth.getFullYear()),
        month: String(currentMonth.getMonth() + 1),
    });
    if (selectedPackageId) {
        query.set("package_id", String(selectedPackageId));
    }
    const data = await requestJson(`/api/calendar/${token}/available-days/?${query.toString()}`);
    currentDaysData = data.days || {};
}

function renderCalendar() {
    if (!currentMonth) return;
    const monthLabel = currentMonth.toLocaleDateString("es-MX", {
        month: "long",
        year: "numeric",
    });
    calendarMonthLabel.textContent = monthLabel.charAt(0).toUpperCase() + monthLabel.slice(1);
    daysGrid.innerHTML = "";

    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const startWeekday = (firstDay.getDay() + 6) % 7;
    for (let i = 0; i < startWeekday; i += 1) {
        const empty = document.createElement("div");
        daysGrid.appendChild(empty);
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
        const isoDate = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        const status = currentDaysData[String(day)]?.status || "no_schedule";
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = String(day);
        button.className = "h-10 rounded border text-sm";

        if (!dateWithinRange(isoDate) || status === "out_of_range" || status === "no_schedule") {
            button.disabled = true;
            button.classList.add("bg-slate-200", "text-slate-500", "cursor-not-allowed");
        } else if (status === "full") {
            button.disabled = true;
            button.classList.add("bg-amber-200", "text-amber-800", "cursor-not-allowed");
        } else {
            button.classList.add("bg-emerald-500", "text-white", "hover:bg-emerald-600");
            button.addEventListener("click", () => showDayConfirmModal(isoDate));
        }

        if (datePicker.value === isoDate) {
            button.classList.add("ring-2", "ring-cyan-500");
        }
        daysGrid.appendChild(button);
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

async function loadContext() {
    context = await requestJson(`/api/calendar/${token}/context/`);
    serviceNameEl.textContent = context.service.name;
    customerNameInput.value = context.user.name || "";
    customerPhoneInput.value = context.user.phone_number || "";
    renderPackageOptions();
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
    const successMessage = `Tu cita ha sido reservada correctamente para el día ${data.booking.date}.`;
    feedback.textContent = successMessage;
    toast(successMessage);
    confirmBtn.textContent = "Cita confirmada";
}

async function refreshCalendar() {
    await loadAvailableDays();
    renderCalendar();
}

async function bootstrap() {
    if (hasBookingError) {
        return;
    }
    await loadContext();
    const min = minDate() || new Date().toISOString().slice(0, 10);
    datePicker.value = min;
    currentMonth = new Date(`${datePicker.value}T00:00:00`);
    currentMonth.setDate(1);
    await refreshCalendar();
    await loadAvailableTimes();
}

packageSelect?.addEventListener("change", async (event) => {
    selectedPackageId = Number(event.target.value);
    renderPackageDetails(selectedPackageId);
    if (datePicker.value && !dateWithinRange(datePicker.value)) {
        datePicker.value = minDate() || "";
    }
    currentMonth = new Date(`${(datePicker.value || minDate())}T00:00:00`);
    currentMonth.setDate(1);
    await refreshCalendar();
    await loadAvailableTimes();
});

prevMonthBtn?.addEventListener("click", async () => {
    currentMonth.setMonth(currentMonth.getMonth() - 1);
    await refreshCalendar();
});

nextMonthBtn?.addEventListener("click", async () => {
    currentMonth.setMonth(currentMonth.getMonth() + 1);
    await refreshCalendar();
});

acceptDayConfirmBtn?.addEventListener("click", async () => {
    if (!pendingDaySelection) return;
    const selected = pendingDaySelection;
    hideDayConfirmModal();
    datePicker.value = selected;
    feedback.textContent = `Fecha seleccionada: ${formatDateLabel(selected)}.`;
    await loadAvailableTimes();
    await refreshCalendar();
});

cancelDayConfirmBtn?.addEventListener("click", hideDayConfirmModal);

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
