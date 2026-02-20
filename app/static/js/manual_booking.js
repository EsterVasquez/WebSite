const serviceSelect = document.getElementById("serviceSelect");
const packageSelect = document.getElementById("packageSelect");
const dateInput = document.getElementById("dateInput");
const timeSelect = document.getElementById("timeSelect");
const timeButtons = document.getElementById("timeButtons");
const statusSelect = document.getElementById("statusSelect");
const customerName = document.getElementById("customerName");
const customerPhone = document.getElementById("customerPhone");
const depositInput = document.getElementById("depositInput");
const notesInput = document.getElementById("notesInput");
const createBookingBtn = document.getElementById("createBookingBtn");
const feedback = document.getElementById("manualFeedback");

let services = [];
let selectedTime = "";

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Error inesperado.");
    }
    return data;
}

function findSelectedService() {
    return services.find((service) => service.id === Number(serviceSelect.value));
}

function findSelectedPackage() {
    const service = findSelectedService();
    if (!service || !packageSelect.value) return null;
    return service.packages.find((item) => item.id === Number(packageSelect.value)) || null;
}

function applyDateLimits() {
    const service = findSelectedService();
    if (!service) return;
    const selectedPackage = findSelectedPackage();

    let minDate = service.available_from;
    let maxDate = service.available_until;
    if (selectedPackage?.available_from && (!minDate || selectedPackage.available_from > minDate)) {
        minDate = selectedPackage.available_from;
    }
    if (selectedPackage?.available_until && (!maxDate || selectedPackage.available_until < maxDate)) {
        maxDate = selectedPackage.available_until;
    }

    if (minDate) {
        dateInput.min = minDate;
    } else {
        dateInput.removeAttribute("min");
    }
    if (maxDate) {
        dateInput.max = maxDate;
    } else {
        dateInput.removeAttribute("max");
    }

    const today = new Date().toISOString().slice(0, 10);
    if (!dateInput.value) {
        dateInput.value = minDate && minDate > today ? minDate : today;
    }
    if (dateInput.value && minDate && dateInput.value < minDate) {
        dateInput.value = minDate;
    }
    if (dateInput.value && maxDate && dateInput.value > maxDate) {
        dateInput.value = maxDate;
    }
}

function renderPackages() {
    const service = findSelectedService();
    packageSelect.innerHTML = '<option value="">Sin paquete</option>';
    if (!service) return;
    service.packages.forEach((pkg) => {
        const option = document.createElement("option");
        option.value = pkg.id;
        option.textContent = `${pkg.name} - $${pkg.price}`;
        packageSelect.appendChild(option);
    });
}

function renderTimes(times) {
    timeButtons.innerHTML = "";
    timeSelect.innerHTML = '<option value="">Selecciona una hora</option>';
    selectedTime = "";
    if (!times.length) {
        timeButtons.innerHTML = '<p class="text-sm text-red-600 col-span-full">No hay horarios disponibles.</p>';
        return;
    }
    times.forEach((time) => {
        const option = document.createElement("option");
        option.value = time;
        option.textContent = time;
        timeSelect.appendChild(option);

        const button = document.createElement("button");
        button.type = "button";
        button.textContent = time;
        button.className = "border rounded-lg py-2 hover:bg-slate-100";
        button.addEventListener("click", () => {
            document
                .querySelectorAll("#timeButtons button")
                .forEach((item) => item.classList.remove("bg-slate-800", "text-white"));
            button.classList.add("bg-slate-800", "text-white");
            selectedTime = time;
            timeSelect.value = time;
        });
        timeButtons.appendChild(button);
    });
}

async function loadServices() {
    const data = await requestJson("/api/dashboard/services/");
    services = data.services || [];
    serviceSelect.innerHTML = "";
    services.forEach((service) => {
        const option = document.createElement("option");
        option.value = service.id;
        option.textContent = service.name;
        serviceSelect.appendChild(option);
    });
    if (!services.length) {
        feedback.textContent = "No hay servicios activos para crear citas.";
        createBookingBtn.disabled = true;
        return;
    }
    renderPackages();
    applyDateLimits();
}

async function loadTimes() {
    const service = findSelectedService();
    if (!service || !dateInput.value) return;

    feedback.textContent = "Consultando horarios...";
    const query = new URLSearchParams({
        service_id: String(service.id),
        date: dateInput.value,
    });
    if (packageSelect.value) {
        query.set("package_id", packageSelect.value);
    }
    const data = await requestJson(`/api/dashboard/manual/available-times/?${query.toString()}`);
    renderTimes(data.times || []);
    feedback.textContent = "";
}

async function createBooking() {
    const service = findSelectedService();
    if (!service) throw new Error("Debes seleccionar un servicio.");
    if (!dateInput.value) throw new Error("Debes seleccionar una fecha.");
    if (!timeSelect.value && !selectedTime) throw new Error("Debes seleccionar una hora.");
    if (!customerName.value.trim()) throw new Error("El nombre del cliente es obligatorio.");
    if (!customerPhone.value.trim()) throw new Error("El teléfono del cliente es obligatorio.");

    const response = await requestJson("/api/dashboard/manual/bookings/create/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
            service_id: service.id,
            package_id: packageSelect.value ? Number(packageSelect.value) : null,
            date: dateInput.value,
            time: timeSelect.value || selectedTime,
            customer_name: customerName.value.trim(),
            customer_phone: customerPhone.value.trim(),
            customer_notes: notesInput.value.trim(),
            deposit_amount: Number(depositInput.value || 0),
            status: statusSelect.value,
        }),
    });
    return response.booking;
}

serviceSelect?.addEventListener("change", async () => {
    try {
        renderPackages();
        applyDateLimits();
        await loadTimes();
    } catch (error) {
        feedback.textContent = error.message;
    }
});

packageSelect?.addEventListener("change", async () => {
    try {
        applyDateLimits();
        await loadTimes();
    } catch (error) {
        feedback.textContent = error.message;
    }
});

dateInput?.addEventListener("change", async () => {
    try {
        await loadTimes();
    } catch (error) {
        feedback.textContent = error.message;
    }
});

timeSelect?.addEventListener("change", () => {
    selectedTime = timeSelect.value;
});

createBookingBtn?.addEventListener("click", async () => {
    try {
        createBookingBtn.disabled = true;
        createBookingBtn.textContent = "Guardando...";
        const booking = await createBooking();
        feedback.textContent = `Cita #${booking.id} creada para ${booking.date} a las ${booking.time}.`;
    } catch (error) {
        feedback.textContent = error.message;
    } finally {
        createBookingBtn.disabled = false;
        createBookingBtn.textContent = "Crear cita";
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadServices();
        await loadTimes();
    } catch (error) {
        feedback.textContent = error.message;
    }
});
