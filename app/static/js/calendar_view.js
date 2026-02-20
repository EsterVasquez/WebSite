const feedback = document.getElementById("calendarFeedback");
const container = document.getElementById("calendarContainer");
const reloadButton = document.getElementById("reloadCalendarBtn");

let calendarInstance = null;

async function fetchEvents() {
    const response = await fetch("/api/dashboard/bookings/events/");
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "No se pudieron cargar los eventos.");
    }
    return data.events;
}

function buildEventInfo(event) {
    const extra = event.extendedProps || {};
    const notes = extra.notes ? ` | Nota: ${extra.notes}` : "";
    return `${event.title} | ${extra.status || ""} | ${extra.package || ""} | ${extra.phone_number || ""}${notes}`;
}

function renderCalendar(events) {
    if (calendarInstance) {
        calendarInstance.destroy();
    }

    const isMobile = window.innerWidth < 768;
    calendarInstance = new FullCalendar.Calendar(container, {
        locale: "es",
        initialView: isMobile ? "timeGridDay" : "dayGridMonth",
        height: "auto",
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: isMobile ? "dayGridMonth,timeGridDay" : "dayGridMonth,timeGridWeek,timeGridDay",
        },
        dayMaxEvents: true,
        navLinks: true,
        nowIndicator: true,
        editable: false,
        slotMinTime: "06:00:00",
        slotMaxTime: "23:00:00",
        eventTimeFormat: { hour: "2-digit", minute: "2-digit", meridiem: false },
        events,
        eventClick(info) {
            feedback.textContent = buildEventInfo(info.event);
        },
    });
    calendarInstance.render();
}

async function loadCalendar() {
    feedback.textContent = "Cargando calendario...";
    const events = await fetchEvents();
    renderCalendar(events);
    feedback.textContent = `Eventos cargados: ${events.length}`;
}

reloadButton?.addEventListener("click", async () => {
    try {
        await loadCalendar();
    } catch (error) {
        feedback.textContent = error.message;
    }
});

window.addEventListener("resize", () => {
    if (!calendarInstance) return;
    const targetView = window.innerWidth < 768 ? "timeGridDay" : "dayGridMonth";
    if (calendarInstance.view.type !== targetView) {
        calendarInstance.changeView(targetView);
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadCalendar();
    } catch (error) {
        feedback.textContent = error.message;
    }
});
