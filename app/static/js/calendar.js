const tbody = document.getElementById("bookingsTbody");
const feedback = document.getElementById("dashboardFeedback");
const refreshBtn = document.getElementById("refreshBtn");
const doubtsList = document.getElementById("doubtsList");

const statTotal = document.getElementById("statTotal");
const statPending = document.getElementById("statPending");
const statConfirmed = document.getElementById("statConfirmed");
const statCancelled = document.getElementById("statCancelled");
const statDoubts = document.getElementById("statDoubts");

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function textValue(value, fallback = "-") {
    if (value === null || value === undefined || value === "") return fallback;
    const normalized = String(value).trim().toLowerCase();
    if (normalized === "undefined" || normalized === "null") return fallback;
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
    const safeLabel = escapeHtml(statusLabel);
    if (statusCode === "doubts") {
        return `<span class="px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-700 border border-orange-300">${safeLabel}</span>`;
    }
    if (statusCode === "confirmed") {
        return `<span class="px-2 py-1 rounded-full text-xs bg-emerald-100 text-emerald-700">${safeLabel}</span>`;
    }
    if (statusCode === "cancelled") {
        return `<span class="px-2 py-1 rounded-full text-xs bg-rose-100 text-rose-700">${safeLabel}</span>`;
    }
    return `<span class="px-2 py-1 rounded-full text-xs bg-amber-100 text-amber-700">${safeLabel}</span>`;
}

function renderStats(bookings, pendingDoubts) {
    const total = bookings.length;
    const pending = bookings.filter((item) => item.status_code === "pending").length;
    const confirmed = bookings.filter((item) => item.status_code === "confirmed").length;
    const cancelled = bookings.filter((item) => item.status_code === "cancelled").length;

    statTotal.textContent = String(total);
    statPending.textContent = String(pending);
    statConfirmed.textContent = String(confirmed);
    statCancelled.textContent = String(cancelled);
    statDoubts.textContent = String(pendingDoubts.length);
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

function renderDoubts(pendingDoubts) {
    if (!doubtsList) return;
    if (!pendingDoubts.length) {
        doubtsList.innerHTML = `
            <article class="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                No hay clientes pendientes por dudas en este momento.
            </article>
        `;
        return;
    }

    doubtsList.innerHTML = pendingDoubts
        .map((thread) => {
            const name = escapeHtml(textValue(thread.name, "Cliente"));
            const phone = escapeHtml(textValue(thread.phone_number, "Sin teléfono"));
            const preview = escapeHtml(textValue(thread.last_message, "Sin mensajes recientes"));
            const windowLabel = escapeHtml(textValue(thread.window_label, ""));
            const chatLink = `/chats/?user=${Number(thread.user_id)}`;

            return `
                <article class="rounded-2xl border border-orange-200 bg-orange-50 p-4 shadow-sm">
                    <div class="flex items-start justify-between gap-2">
                        <div>
                            <p class="font-semibold text-slate-900">${name}</p>
                            <p class="text-xs text-slate-600 mt-0.5">${phone}</p>
                        </div>
                        <span class="inline-flex px-2 py-1 rounded-full text-[11px] font-semibold bg-orange-100 text-orange-700 border border-orange-300">
                            Dudas
                        </span>
                    </div>
                    <p class="mt-3 text-sm text-slate-700 line-clamp-2">${preview}</p>
                    <p class="mt-2 text-xs ${thread.window_expired ? "text-rose-700" : "text-slate-500"}">${windowLabel}</p>
                    <div class="mt-4 flex flex-wrap gap-2">
                        <a href="${chatLink}" class="inline-flex items-center rounded-lg bg-orange-600 hover:bg-orange-500 text-white px-3 py-1.5 text-xs font-semibold">
                            Abrir chat
                        </a>
                    </div>
                </article>
            `;
        })
        .join("");
}

function renderRows(bookings) {
    if (bookings.length === 0) {
        tbody.innerHTML =
            '<tr><td colspan="12" class="px-4 py-6 text-center text-slate-500">No hay citas registradas.</td></tr>';
        return;
    }

    tbody.innerHTML = bookings
        .map(
            (booking) => `
            <tr class="border-t hover:bg-slate-50">
                <td class="px-4 py-3">
                    <p class="font-semibold text-slate-800">${escapeHtml(textValue(booking.user_name, "Cliente"))}</p>
                    ${booking.chat_pending ? '<span class="inline-flex mt-1 px-2 py-0.5 rounded-full text-[11px] bg-orange-100 text-orange-700">Requiere atención</span>' : ""}
                </td>
                <td class="px-4 py-3 text-slate-600">
                    <p>${escapeHtml(textValue(booking.phone_number, "Sin teléfono"))}</p>
                </td>
                <td class="px-4 py-3 text-slate-800">${escapeHtml(textValue(booking.service, "Sin servicio"))}</td>
                <td class="px-4 py-3 text-slate-600">${escapeHtml(textValue(booking.package ?? booking.pre_sale, "Sin paquete"))}</td>
                <td class="px-4 py-3 text-slate-600">${escapeHtml(textValue(booking.date))}</td>
                <td class="px-4 py-3 text-slate-600">${escapeHtml(textValue(booking.time))}</td>
                <td class="px-4 py-3 text-slate-600">$${moneyValue(booking.total_price)}</td>
                <td class="px-4 py-3 text-slate-600">$${moneyValue(booking.deposit_amount)}</td>
                <td class="px-4 py-3 text-slate-600 max-w-[260px]">
                    <p class="whitespace-normal break-words">${escapeHtml(textValue(booking.customer_notes, "Sin notas"))}</p>
                </td>
                <td class="px-4 py-3">${statusBadge(booking.status_code || "pending", textValue(booking.status, "Pendiente"))}</td>
                <td class="px-4 py-3 text-slate-600">${escapeHtml(textValue(booking.source, "N/D"))}</td>
                <td class="px-4 py-3">
                    <div class="flex flex-col gap-2 min-w-[170px]">
                        <select data-booking-id="${booking.id}" class="status-select border border-slate-300 rounded-lg px-2 py-1.5 text-xs">
                            <option value="pending" ${(booking.status_code || "pending") === "pending" ? "selected" : ""}>Pendiente</option>
                            <option value="confirmed" ${(booking.status_code || "pending") === "confirmed" ? "selected" : ""}>Confirmado</option>
                            <option value="cancelled" ${(booking.status_code || "pending") === "cancelled" ? "selected" : ""}>Cancelado</option>
                            <option value="doubts" ${(booking.status_code || "pending") === "doubts" ? "selected" : ""}>Dudas</option>
                        </select>
                        <div class="flex items-center gap-2">
                            <button data-booking-id="${booking.id}" class="status-save inline-flex items-center bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded-lg text-xs font-semibold">Guardar</button>
                            ${booking.chat_user_id ? `<a href="/chats/?user=${booking.chat_user_id}" class="inline-flex items-center bg-orange-600 hover:bg-orange-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold">Chat</a>` : ""}
                        </div>
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
                await loadDashboard();
            } catch (error) {
                feedback.textContent = error.message;
            }
        });
    });
}

async function loadDashboard() {
    feedback.textContent = "Actualizando datos...";
    const [bookingsResult, threadsResult] = await Promise.allSettled([
        fetch("/api/dashboard/bookings/"),
        fetch("/api/dashboard/chats/threads/"),
    ]);

    if (bookingsResult.status !== "fulfilled") {
        throw new Error("No se pudieron cargar las citas.");
    }

    const bookingsResponse = bookingsResult.value;
    const bookingsData = await bookingsResponse.json();
    if (!bookingsResponse.ok) {
        throw new Error(bookingsData.error || "No se pudieron cargar las citas.");
    }

    let pendingDoubts = [];
    if (threadsResult.status === "fulfilled") {
        const threadsResponse = threadsResult.value;
        const threadsData = await threadsResponse.json();
        if (threadsResponse.ok) {
            pendingDoubts = Array.isArray(threadsData.pending) ? threadsData.pending : [];
        }
    }
    renderStats(bookingsData.bookings, pendingDoubts);
    renderDoubts(pendingDoubts);
    renderRows(bookingsData.bookings);
    bindStatusButtons();
    feedback.textContent = `Actualizado: ${new Date().toLocaleTimeString("es-MX")}`;
}

refreshBtn?.addEventListener("click", async () => {
    try {
        await loadDashboard();
    } catch (error) {
        feedback.textContent = error.message;
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadDashboard();
    } catch (error) {
        feedback.textContent = error.message;
    }
});
