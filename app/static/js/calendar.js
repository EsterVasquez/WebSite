const tbody = document.getElementById("bookingsTbody");
const feedback = document.getElementById("dashboardFeedback");
const refreshBtn = document.getElementById("refreshBtn");

const statTotal = document.getElementById("statTotal");
const statPending = document.getElementById("statPending");
const statConfirmed = document.getElementById("statConfirmed");
const statCancelled = document.getElementById("statCancelled");

function statusBadge(status) {
    if (status === "Confirmado") {
        return '<span class="px-2 py-1 rounded-full text-xs bg-emerald-100 text-emerald-700">Confirmado</span>';
    }
    if (status === "Cancelado") {
        return '<span class="px-2 py-1 rounded-full text-xs bg-rose-100 text-rose-700">Cancelado</span>';
    }
    return '<span class="px-2 py-1 rounded-full text-xs bg-amber-100 text-amber-700">Pendiente</span>';
}

function renderStats(bookings) {
    const total = bookings.length;
    const pending = bookings.filter((item) => item.status === "Pendiente").length;
    const confirmed = bookings.filter((item) => item.status === "Confirmado").length;
    const cancelled = bookings.filter((item) => item.status === "Cancelado").length;

    statTotal.textContent = String(total);
    statPending.textContent = String(pending);
    statConfirmed.textContent = String(confirmed);
    statCancelled.textContent = String(cancelled);
}

function renderRows(bookings) {
    if (bookings.length === 0) {
        tbody.innerHTML =
            '<tr><td colspan="8" class="px-4 py-6 text-center text-slate-500">No hay reservaciones.</td></tr>';
        return;
    }

    tbody.innerHTML = bookings
        .map(
            (booking) => `
            <tr class="border-t">
                <td class="px-4 py-3 font-medium text-slate-800">${booking.user_name}</td>
                <td class="px-4 py-3 text-slate-600">${booking.phone_number}</td>
                <td class="px-4 py-3 text-slate-800">${booking.service}</td>
                <td class="px-4 py-3 text-slate-600">${booking.tier}</td>
                <td class="px-4 py-3 text-slate-600">${booking.date}</td>
                <td class="px-4 py-3 text-slate-600">${booking.time}</td>
                <td class="px-4 py-3">${statusBadge(booking.status)}</td>
                <td class="px-4 py-3 text-slate-600">${booking.source}</td>
            </tr>
        `
        )
        .join("");
}

async function loadBookings() {
    feedback.textContent = "Actualizando datos...";
    const response = await fetch("/api/dashboard/bookings/");
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "No se pudieron cargar reservaciones.");
    }
    renderStats(data.bookings);
    renderRows(data.bookings);
    feedback.textContent = `Actualizado: ${new Date().toLocaleTimeString("es-MX")}`;
}

refreshBtn.addEventListener("click", async () => {
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
