const tbody = document.getElementById("bookingsTbody");
const feedback = document.getElementById("dashboardFeedback");
const refreshBtn = document.getElementById("refreshBtn");

const statTotal = document.getElementById("statTotal");
const statPending = document.getElementById("statPending");
const statConfirmed = document.getElementById("statConfirmed");
const statCancelled = document.getElementById("statCancelled");

function textValue(value, fallback = "-") {
    if (value === null || value === undefined || value === "") return fallback;
    return String(value);
}

function numberValue(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function moneyValue(value) {
    return numberValue(value, 0).toFixed(2);
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
}

function statusBadge(statusCode, statusLabel) {
    if (statusCode === "confirmed") {
        return `<span class="px-2 py-1 rounded-full text-xs bg-emerald-100 text-emerald-700">${statusLabel}</span>`;
    }
    if (statusCode === "cancelled") {
        return `<span class="px-2 py-1 rounded-full text-xs bg-rose-100 text-rose-700">${statusLabel}</span>`;
    }
    return `<span class="px-2 py-1 rounded-full text-xs bg-amber-100 text-amber-700">${statusLabel}</span>`;
}

function renderStats(bookings) {
    const total = bookings.length;
    const pending = bookings.filter((item) => item.status_code === "pending").length;
    const confirmed = bookings.filter((item) => item.status_code === "confirmed").length;
    const cancelled = bookings.filter((item) => item.status_code === "cancelled").length;

    statTotal.textContent = String(total);
    statPending.textContent = String(pending);
    statConfirmed.textContent = String(confirmed);
    statCancelled.textContent = String(cancelled);
}

async function updateStatus(bookingId, status, statusLabel) {
    const response = await fetch(`/api/dashboard/bookings/${bookingId}/status/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ status }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "No se pudo actualizar el estado.");
    }
    feedback.textContent = `Cita #${bookingId} actualizada a ${statusLabel}.`;
}

function renderRows(bookings) {
    if (bookings.length === 0) {
        tbody.innerHTML =
            '<tr><td colspan="11" class="px-4 py-6 text-center text-slate-500">No hay citas registradas.</td></tr>';
        return;
    }

    tbody.innerHTML = bookings
        .map(
            (booking) => `
            <tr class="border-t">
                <td class="px-4 py-3 font-medium text-slate-800">${textValue(booking.user_name, "Cliente")}</td>
                <td class="px-4 py-3 text-slate-600">${textValue(booking.phone_number, "Sin teléfono")}</td>
                <td class="px-4 py-3 text-slate-800">${textValue(booking.service, "Sin servicio")}</td>
                <td class="px-4 py-3 text-slate-600">${textValue(booking.package ?? booking.pre_sale, "Sin paquete")}</td>
                <td class="px-4 py-3 text-slate-600">${textValue(booking.date)}</td>
                <td class="px-4 py-3 text-slate-600">${textValue(booking.time)}</td>
                <td class="px-4 py-3 text-slate-600">$${moneyValue(booking.total_price)}</td>
                <td class="px-4 py-3 text-slate-600">$${moneyValue(booking.deposit_amount)}</td>
                <td class="px-4 py-3">${statusBadge(booking.status_code || "pending", textValue(booking.status, "Pendiente"))}</td>
                <td class="px-4 py-3 text-slate-600">${textValue(booking.source, "N/D")}</td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                        <select data-booking-id="${booking.id}" class="status-select border rounded px-2 py-1 text-xs">
                            <option value="pending" ${(booking.status_code || "pending") === "pending" ? "selected" : ""}>Pendiente</option>
                            <option value="confirmed" ${(booking.status_code || "pending") === "confirmed" ? "selected" : ""}>Confirmado</option>
                            <option value="cancelled" ${(booking.status_code || "pending") === "cancelled" ? "selected" : ""}>Cancelado</option>
                        </select>
                        <button data-booking-id="${booking.id}" class="status-save bg-slate-800 text-white px-2 py-1 rounded text-xs">Guardar</button>
                    </div>
                </td>
            </tr>
        `
        )
        .join("");
}

function bindStatusButtons() {
    document.querySelectorAll(".status-save").forEach((button) => {
        button.addEventListener("click", async (event) => {
            const bookingId = Number(event.currentTarget.dataset.bookingId);
            const select = document.querySelector(`.status-select[data-booking-id="${bookingId}"]`);
            if (!select) return;
            const status = select.value;
            const label = select.options[select.selectedIndex].text;
            try {
                await updateStatus(bookingId, status, label);
                await loadBookings();
            } catch (error) {
                feedback.textContent = error.message;
            }
        });
    });
}

async function loadBookings() {
    feedback.textContent = "Actualizando datos...";
    const response = await fetch("/api/dashboard/bookings/");
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "No se pudieron cargar las citas.");
    }
    renderStats(data.bookings);
    renderRows(data.bookings);
    bindStatusButtons();
    feedback.textContent = `Actualizado: ${new Date().toLocaleTimeString("es-MX")}`;
}

refreshBtn?.addEventListener("click", async () => {
    try {
        await loadBookings();
    } catch (error) {
        feedback.textContent = error.message;
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadBookings();
    } catch (error) {
        feedback.textContent = error.message;
    }
});
