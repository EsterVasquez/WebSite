// Data
const services = {
    all: { name: "Todos los servicios", color: "bg-gray-500" },
    wedding: { name: "Bodas", color: "bg-pink-500" },
    portrait: { name: "Retratos", color: "bg-blue-500" },
    family: { name: "Familiar", color: "bg-green-500" },
    corporate: { name: "Corporativo", color: "bg-purple-500" },
    event: { name: "Eventos", color: "bg-orange-500" },
    product: { name: "Producto", color: "bg-yellow-500" },
};

const appointments = [
    {
        id: 1,
        date: new Date(2025, 6, 15),
        time: "10:00",
        duration: 120, //TODO: DELETE THIS LINE!!!!!!!!!!!!!!
        client: "María González",
        phone: "+52 55 1234 5678",
        service: "wedding",
        location: "Estudio Principal",
        status: "confirmed",
        notes: "Sesión de compromiso, traer vestido blanco",
    },
    {
        id: 2,
        date: new Date(2025, 6, 15),
        time: "14:00",
        duration: 60,
        client: "Carlos Ruiz",
        phone: "+52 55 9876 5432",
        service: "portrait",
        location: "Estudio 2",
        status: "pending",
        notes: "Fotos profesionales para LinkedIn",
    },
    {
        id: 3,
        date: new Date(2025, 6, 15),
        time: "18:00",
        duration: 90,
        client: "Familia Hernández",
        phone: "+52 55 5555 1234",
        service: "family",
        location: "Parque Chapultepec",
        status: "confirmed",
        notes: "Sesión familiar con 3 niños pequeños",
    },
    {
        id: 4,
        date: new Date(2025, 6, 15),
        time: "15:00",
        duration: 180,
        client: "Empresa TechCorp",
        phone: "+52 55 7777 8888",
        service: "corporate",
        location: "Oficinas del cliente",
        status: "confirmed",
        notes: "Fotos corporativas para 15 empleados",
    },
    {
        id: 5,
        date: new Date(2025, 6, 17),
        time: "15:00",
        duration: 60,
        client: "Ana López",
        phone: "+52 55 3333 4444",
        service: "portrait",
        location: "Estudio Principal",
        status: "confirmed",
        notes: "Sesión de headshots",
    },
];

let chats = {
    1: {
        id: 1,
        client: "María González",
        phone: "+52 55 1234 5678",
        initials: "MG",
        color: "bg-blue-500",
        priority: "urgent",
        lastMessage: "Necesito cambiar la fecha de mi sesión...",
        time: "10:30 AM",
        status: "active",
        messages: [
            {
                sender: "client",
                message: "Hola, necesito ayuda con mi cita",
                time: "10:25 AM",
            },
            {
                sender: "client",
                message: "El bot no pudo ayudarme a cambiar la fecha",
                time: "10:26 AM",
            },
            {
                sender: "client",
                message: "¿Pueden ayudarme por favor?",
                time: "10:30 AM",
            },
        ],
    },
    2: {
        id: 2,
        client: "Carlos Ruiz",
        phone: "+52 55 9876 5432",
        initials: "CR",
        color: "bg-green-500",
        priority: "consultation",
        lastMessage: "¿Pueden hacer fotos en exteriores?",
        time: "9:15 AM",
        status: "active",
        messages: [
            { sender: "client", message: "Buenos días", time: "9:10 AM" },
            {
                sender: "client",
                message: "¿Pueden hacer fotos en exteriores?",
                time: "9:15 AM",
            },
        ],
    },
    3: {
        id: 3,
        client: "Familia Hernández",
        phone: "+52 55 5555 1234",
        initials: "FH",
        color: "bg-purple-500",
        priority: "info",
        lastMessage: "Preguntas sobre paquetes familiares",
        time: "8:45 AM",
        status: "active",
        messages: [
            {
                sender: "client",
                message: "Hola, quería preguntar sobre los paquetes familiares",
                time: "8:45 AM",
            },
        ],
    },
};

let currentDate = new Date();
let currentView = "month";
let selectedService = "all";
let nonWorkingDays = [];
let currentChat = null;
let pendingChatAction = null;

// Helper function to get Monday as start of week
function getStartOfWeek(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is sunday
    return new Date(d.setDate(diff));
}

// Dark mode functionality
function initDarkMode() {
    const darkModeToggle = document.getElementById("darkModeToggle");
    const isDark = localStorage.getItem("darkMode") === "true";

    if (isDark) {
        document.documentElement.classList.add("dark");
    }

    darkModeToggle.addEventListener("click", () => {
        document.documentElement.classList.toggle("dark");
        const isDarkMode = document.documentElement.classList.contains("dark");
        localStorage.setItem("darkMode", isDarkMode);
    });
}

// Tab functionality
function initTabs() {
    const calendarTab = document.getElementById("calendarTab");
    const chatsTab = document.getElementById("chatsTab");
    const calendarSection = document.getElementById("calendarSection");
    const chatsSection = document.getElementById("chatsSection");

    calendarTab.addEventListener("click", () => {
        calendarTab.classList.add("active");
        chatsTab.classList.remove("active");
        calendarSection.classList.remove("hidden");
        chatsSection.classList.add("hidden");
    });

    chatsTab.addEventListener("click", () => {
        chatsTab.classList.add("active");
        calendarTab.classList.remove("active");
        chatsSection.classList.remove("hidden");
        calendarSection.classList.add("hidden");
    });
}

// Navigation functionality
function initNavigation() {
    const prevMonth = document.getElementById("prevMonth");
    const nextMonth = document.getElementById("nextMonth");
    const prevPeriod = document.getElementById("prevPeriod");
    const nextPeriod = document.getElementById("nextPeriod");
    const todayBtn = document.getElementById("todayBtn");

    prevMonth.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        updateCalendar();
    });

    nextMonth.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        updateCalendar();
    });

    prevPeriod.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        updateCalendar();
    });

    nextPeriod.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        updateCalendar();
    });

    todayBtn.addEventListener("click", () => {
        currentDate = new Date();
        updateCalendar();
    });
}

// Calendar functionality
function generateCalendar(date, containerId, isSettings = false) {
    const container = document.getElementById(containerId);
    const year = date.getFullYear();
    const month = date.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = getStartOfWeek(firstDay);

    let html = "";

    // Days of week header - starting with Monday
    const daysOfWeek = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
    daysOfWeek.forEach((day) => {
        html += `<div class="p-2 font-medium text-gray-500 dark:text-gray-400">${day}</div>`;
    });

    // Calendar days
    const current = new Date(startDate);
    for (let i = 0; i < 42; i++) {
        const isCurrentMonth = current.getMonth() === month;
        const isToday = current.toDateString() === new Date().toDateString();
        const isSelected =
            current.toDateString() === currentDate.toDateString();
        const hasAppointments = appointments.some(
            (apt) => apt.date.toDateString() === current.toDateString()
        );
        const isNonWorking = nonWorkingDays.some(
            (d) => d.toDateString() === current.toDateString()
        );

        let classes = `p-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors ${
            isCurrentMonth
                ? "text-gray-900 dark:text-white"
                : "text-gray-400 dark:text-gray-600"
        } ${isToday ? "bg-blue-100 dark:bg-blue-900 font-bold" : ""} ${
            isSelected && !isSettings ? "ring-2 ring-blue-500" : ""
        } ${
            hasAppointments && !isSettings ? "bg-blue-300 dark:bg-blue-300" : ""
        } ${isNonWorking ? "bg-red-50 dark:bg-red-900/30 line-through" : ""}`;

        html += `<div class="${classes}" data-date="${current.toISOString()}" ${
            isSettings
                ? 'onclick="toggleNonWorkingDay(this)"'
                : 'onclick="selectDate(this)"'
        }>${current.getDate()}</div>`;

        current.setDate(current.getDate() + 1);
    }

    container.innerHTML = html;

    // Update month/year display
    if (!isSettings) {
        const monthYear = document.getElementById("currentMonthYear");
        if (monthYear) {
            monthYear.textContent = date.toLocaleDateString("es-ES", {
                month: "long",
                year: "numeric",
            });
        }
    }
}

function selectDate(element) {
    const selectedDate = new Date(element.dataset.date);
    currentDate = selectedDate;

    if (window.innerWidth <= 768) {
        showMobileDaySummary(selectedDate);
    } else {
        updateCalendar();
    }
}

function showMobileDaySummary(date) {
    const dayAppointments = appointments.filter(
        (apt) =>
            apt.date.toDateString() === date.toDateString() &&
            (selectedService === "all" || apt.service === selectedService)
    );

    const container = document.getElementById("mobileDaySummary");
    let html = `<h3 class="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
        Citas del ${date.toLocaleDateString("es-ES", {
            weekday: "long",
            day: "numeric",
            month: "long",
        })}
    </h3>`;

    if (dayAppointments.length === 0) {
        html += `<p class="text-gray-500 dark:text-gray-400">No hay citas para este día</p>`;
    } else {
        html += `<div class="space-y-3">`;
        dayAppointments.forEach((apt) => {
            html += `
                <div
                    class="border rounded-lg p-3 border-gray-200 dark:border-gray-600 
                           hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                    onclick="showAppointmentDetails(${apt.id})"
                >
                    <div class="flex justify-between">
                        <span class="font-medium text-gray-900 dark:text-white">${
                            apt.time
                        }</span>
                        <span class="px-2 py-0.5 rounded text-xs text-white ${
                            services[apt.service].color
                        }">
                            ${services[apt.service].name}
                        </span>
                    </div>
                    <p class="font-semibold text-gray-900 dark:text-white">${
                        apt.client
                    }</p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">${
                        apt.location
                    }</p>
                </div>
            `;
        });
        html += `</div>`;
    }

    container.innerHTML = html;
    container.classList.remove("hidden");
}

function toggleNonWorkingDay(element) {
    const date = new Date(element.dataset.date);
    const index = nonWorkingDays.findIndex(
        (d) => d.toDateString() === date.toDateString()
    );

    if (index > -1) {
        nonWorkingDays.splice(index, 1);
        element.classList.remove(
            "bg-red-50",
            "dark:bg-red-900/30",
            "line-through"
        );
    } else {
        nonWorkingDays.push(date);
        element.classList.add(
            "bg-red-50",
            "dark:bg-red-900/30",
            "line-through"
        );
    }
}

function updateCalendar() {
    generateCalendar(currentDate, "miniCalendar");
    updateCalendarView();
    updateSelectedDateText();
}

function updateSelectedDateText() {
    const text = currentDate.toLocaleDateString("es-ES", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
    });
    document.getElementById("selectedDateText").textContent = `- ${text}`;
}

function updateCalendarView() {
    const container = document.getElementById("calendarView");
    container.innerHTML = generateMonthView();
}

// New function to show day expansion modal
function showDayExpansion(date) {
    const dayAppointments = appointments.filter(
        (apt) =>
            apt.date.toDateString() === date.toDateString() &&
            (selectedService === "all" || apt.service === selectedService)
    );

    const modal = document.getElementById("dayExpansionModal");
    const title = document.getElementById("dayExpansionTitle");
    const content = document.getElementById("dayExpansionContent");

    const dateStr = date.toLocaleDateString("es-ES", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
    });

    title.innerHTML = `<i class="fas fa-calendar-day"></i> Citas del ${dateStr}`;

    let html = '<div class="space-y-3">';

    if (dayAppointments.length === 0) {
        html +=
            '<p class="text-gray-500 dark:text-gray-400 text-center py-4">No hay citas programadas para este día</p>';
    } else {
        // Sort appointments by time
        dayAppointments.sort((a, b) => a.time.localeCompare(b.time));

        dayAppointments.forEach((apt) => {
            const statusColors = {
                confirmed:
                    "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
                pending:
                    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
                cancelled:
                    "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
            };

            const statusText = {
                confirmed: "Confirmada",
                pending: "Pendiente",
                cancelled: "Cancelada",
            };

            html += `
                        <div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                             onclick="showAppointmentDetails(${apt.id})">
                            <div class="flex items-start justify-between mb-2">
                                <div class="flex items-center gap-2">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        services[apt.service].color
                                    } text-white">
                                        ${services[apt.service].name}
                                    </span>
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        statusColors[apt.status]
                                    }">
                                        ${statusText[apt.status]}
                                    </span>
                                </div>
                                <span class="text-sm font-medium text-gray-900 dark:text-white">${
                                    apt.time
                                }</span>
                            </div>
                            <div class="space-y-1">
                                <p class="font-medium text-gray-900 dark:text-white">${
                                    apt.client
                                }</p>
                                <p class="text-sm text-gray-600 dark:text-gray-400">
                                    <i class="fas fa-map-marker-alt mr-1"></i>
                                    ${apt.location}
                                </p>
                                ${
                                    apt.notes
                                        ? `<p class="text-sm text-gray-500 dark:text-gray-400 italic">${apt.notes}</p>`
                                        : ""
                                }
                            </div>
                        </div>
                    `;
        });
    }

    html += "</div>";
    content.innerHTML = html;

    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

function generateMonthView() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const startDate = getStartOfWeek(firstDay);

    let html = '<div class="grid grid-cols-7 gap-1">';

    // Header - starting with Monday
    const daysOfWeek = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
    daysOfWeek.forEach((day) => {
        html += `<div class="text-center text-sm font-medium text-gray-500 dark:text-gray-400 p-2">${day}</div>`;
    });

    // Days
    const current = new Date(startDate);
    for (let i = 0; i < 42; i++) {
        const isCurrentMonth = current.getMonth() === month;
        const isToday = current.toDateString() === new Date().toDateString();
        const isSelected =
            current.toDateString() === currentDate.toDateString();
        const dayAppointments = appointments.filter(
            (apt) =>
                apt.date.toDateString() === current.toDateString() &&
                (selectedService === "all" || apt.service === selectedService)
        );
        const isNonWorking = nonWorkingDays.some(
            (d) => d.toDateString() === current.toDateString()
        );

        let classes = `min-h-[100px] p-1 border cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
            isCurrentMonth
                ? "bg-white dark:bg-gray-800"
                : "bg-gray-50 dark:bg-gray-700"
        } ${isToday ? "ring-2 ring-blue-500" : ""} ${
            isSelected ? "bg-blue-50 dark:bg-blue-900/30" : ""
        } ${isNonWorking ? "bg-red-50 dark:bg-red-900/30" : ""}`;

        html += `<div class="${classes}" onclick="selectDate(this)" data-date="${current.toISOString()}">`;
        html += `<div class="text-sm ${
            isCurrentMonth
                ? "text-gray-900 dark:text-white"
                : "text-gray-400 dark:text-gray-600"
        } ${isToday ? "font-bold text-blue-600" : ""} ${
            isNonWorking ? "text-red-500 line-through" : ""
        }">${current.getDate()}</div>`;

        // Appointments
        html += '<div class="space-y-1 mt-1">';
        dayAppointments.slice(0, 3).forEach((apt) => {
            html += `<div class="text-xs p-1 rounded cursor-pointer ${
                services[apt.service].color
            } text-white truncate" onclick="event.stopPropagation(); showAppointmentDetails(${
                apt.id
            })">${apt.time} ${apt.client}</div>`;
        });

        if (dayAppointments.length > 3) {
            html += `<div class="text-xs text-blue-600 dark:text-blue-400 text-center cursor-pointer hover:underline" onclick="event.stopPropagation(); showDayExpansion(new Date('${current.toISOString()}'))">+${
                dayAppointments.length - 3
            } más</div>`;
        }
        html += "</div>";
        html += "</div>";

        current.setDate(current.getDate() + 1);
    }

    html += "</div>";
    return html;
}

function showAppointmentDetails(appointmentId) {
    const appointment = appointments.find((apt) => apt.id === appointmentId);
    if (!appointment) return;

    // Close day expansion modal if it's open
    const dayExpansionModal = document.getElementById("dayExpansionModal");
    if (dayExpansionModal.classList.contains("flex")) {
        dayExpansionModal.classList.add("hidden");
        dayExpansionModal.classList.remove("flex");
    }

    const modal = document.getElementById("appointmentModal");
    const details = document.getElementById("appointmentDetails");

    const statusColors = {
        confirmed:
            "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
        pending:
            "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
        cancelled: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    };

    const statusText = {
        confirmed: "Confirmada",
        pending: "Pendiente",
        cancelled: "Cancelada",
    };

    details.innerHTML = `
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            statusColors[appointment.status]
                        }">
                            ${statusText[appointment.status]}
                        </span>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            services[appointment.service].color
                        } text-white">
                            ${services[appointment.service].name}
                        </span>
                    </div>

                    <div class="space-y-3">
                        <div class="flex items-center gap-3">
                            <i class="fas fa-user text-gray-500 dark:text-gray-400"></i>
                            <div>
                                <p class="font-medium text-gray-900 dark:text-white">${
                                    appointment.client
                                }</p>
                                <p class="text-sm text-gray-500 dark:text-gray-400">Cliente</p>
                            </div>
                        </div>

                        <div class="flex items-center gap-3">
                            <i class="fas fa-phone text-gray-500 dark:text-gray-400"></i>
                            <div>
                                <p class="font-medium text-gray-900 dark:text-white">${
                                    appointment.phone
                                }</p>
                                <p class="text-sm text-gray-500 dark:text-gray-400">WhatsApp</p>
                            </div>
                        </div>

                        <div class="flex items-center gap-3">
                            <i class="fas fa-clock text-gray-500 dark:text-gray-400"></i>
                            <div>
                                <p class="font-medium text-gray-900 dark:text-white">${
                                    appointment.time
                                }</p>
                                <p class="text-sm text-gray-500 dark:text-gray-400">${appointment.date.toLocaleDateString(
                                    "es-ES"
                                )}</p>
                            </div>
                        </div>

                        <div class="flex items-center gap-3">
                            <i class="fas fa-map-marker-alt text-gray-500 dark:text-gray-400"></i>
                            <div>
                                <p class="font-medium text-gray-900 dark:text-white">${
                                    appointment.location
                                }</p>
                                <p class="text-sm text-gray-500 dark:text-gray-400">Ubicación</p>
                            </div>
                        </div>
                    </div>

                    ${
                        appointment.notes
                            ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notas</label>
                            <textarea readonly class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white resize-none" rows="3">${appointment.notes}</textarea>
                        </div>
                    `
                            : ""
                    }
                </div>
            `;

    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

// Chat functionality
function initChats() {
    const chatItems = document.querySelectorAll(".chat-item");
    chatItems.forEach((item) => {
        item.addEventListener("click", () => {
            const chatId = parseInt(item.dataset.chatId);
            openChat(chatId);
        });
    });

    // Chat actions
    document.getElementById("markCompleted").addEventListener("click", () => {
        if (currentChat) {
            showChatActionModal(
                "completed",
                "Marcar como Finalizado",
                "¿Estás seguro de que quieres marcar este chat como finalizado?"
            );
        }
    });

    document.getElementById("archiveChat").addEventListener("click", () => {
        if (currentChat) {
            showChatActionModal(
                "archived",
                "Archivar Chat",
                "¿Estás seguro de que quieres archivar este chat?"
            );
        }
    });

    document.getElementById("deleteChat").addEventListener("click", () => {
        if (currentChat) {
            showChatActionModal(
                "deleted",
                "Eliminar Chat",
                "¿Estás seguro de que quieres eliminar este chat? Esta acción no se puede deshacer."
            );
        }
    });

    // Send message
    const sendMessage = document.getElementById("sendMessage");
    const messageInput = document.getElementById("messageInput");

    sendMessage.addEventListener("click", () => {
        sendChatMessage();
    });

    messageInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendChatMessage();
        }
    });
}

function openChat(chatId) {
    currentChat = chats[chatId];
    if (!currentChat) return;

    const chatHeader = document.getElementById("chatHeader");
    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");

    // Update header
    chatHeader.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 ${currentChat.color} rounded-full flex items-center justify-center text-white font-medium">
                            ${currentChat.initials}
                        </div>
                        <div>
                            <p class="font-medium text-gray-900 dark:text-white">${currentChat.client}</p>
                            <p class="text-sm text-gray-500 dark:text-gray-400">${currentChat.phone}</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <!-- Chat Actions -->
                        <div class="flex items-center gap-1 mr-4">
                            <button id="markCompleted" class="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded hover:bg-green-200 dark:hover:bg-green-800 transition-colors">
                                <i class="fas fa-check mr-1"></i>
                                Finalizar
                            </button>
                            <button id="archiveChat" class="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors">
                                <i class="fas fa-archive mr-1"></i>
                                Archivar
                            </button>
                            <button id="deleteChat" class="px-2 py-1 text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded hover:bg-red-200 dark:hover:bg-red-800 transition-colors">
                                <i class="fas fa-trash mr-1"></i>
                                Eliminar
                            </button>
                        </div>
                    </div>
                </div>
            `;

    // Re-attach event listeners for chat actions
    document.getElementById("markCompleted").addEventListener("click", () => {
        showChatActionModal(
            "completed",
            "Marcar como Finalizado",
            "¿Estás seguro de que quieres marcar este chat como finalizado?"
        );
    });

    document.getElementById("archiveChat").addEventListener("click", () => {
        showChatActionModal(
            "archived",
            "Archivar Chat",
            "¿Estás seguro de que quieres archivar este chat?"
        );
    });

    document.getElementById("deleteChat").addEventListener("click", () => {
        showChatActionModal(
            "deleted",
            "Eliminar Chat",
            "¿Estás seguro de que quieres eliminar este chat? Esta acción no se puede deshacer."
        );
    });

    // Update messages
    updateChatMessages();
    chatHeader.classList.remove("hidden");
    chatInput.classList.remove("hidden");
}

function updateChatMessages() {
    const chatMessages = document.getElementById("chatMessages");
    let messagesHtml = "";

    currentChat.messages.forEach((msg) => {
        if (msg.sender === "client") {
            messagesHtml += `
                        <div class="flex items-start gap-2 mb-4">
                            <div class="w-8 h-8 ${currentChat.color} rounded-full flex items-center justify-center text-white text-xs font-medium">
                                ${currentChat.initials}
                            </div>
                            <div class="flex-1">
                                <div class="bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 max-w-xs">
                                    <p class="text-sm text-gray-900 dark:text-white">${msg.message}</p>
                                </div>
                                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">${msg.time}</p>
                            </div>
                        </div>
                    `;
        } else {
            messagesHtml += `
                        <div class="flex items-start gap-2 mb-4 justify-end">
                            <div class="flex-1">
                                <div class="bg-blue-600 rounded-lg px-3 py-2 max-w-xs ml-auto">
                                    <p class="text-sm text-white">${msg.message}</p>
                                </div>
                                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">${msg.time}</p>
                            </div>
                            <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-medium">
                                YO
                            </div>
                        </div>
                    `;
        }
    });

    chatMessages.innerHTML = messagesHtml;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendChatMessage() {
    const messageInput = document.getElementById("messageInput");
    const message = messageInput.value.trim();

    if (!message || !currentChat) return;

    // Add message to chat
    const now = new Date();
    const timeString = now.toLocaleTimeString("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
    });

    currentChat.messages.push({
        sender: "agent",
        message: message,
        time: timeString,
    });

    // Clear input
    messageInput.value = "";

    // Update messages display
    updateChatMessages();
}

function showChatActionModal(action, title, message) {
    pendingChatAction = action;
    document.getElementById("chatActionTitle").textContent = title;
    document.getElementById("chatActionMessage").textContent = message;

    const modal = document.getElementById("chatActionModal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

function executeChatAction() {
    if (!currentChat || !pendingChatAction) return;

    if (pendingChatAction === "deleted") {
        // Remove chat from list
        delete chats[currentChat.id];

        // Remove from DOM
        const chatItem = document.querySelector(
            `[data-chat-id="${currentChat.id}"]`
        );
        if (chatItem) {
            chatItem.remove();
        }

        // Clear chat window
        clearChatWindow();
    } else {
        // Update chat status
        currentChat.status = pendingChatAction;

        // Update visual indicator or move to different section
        const chatItem = document.querySelector(
            `[data-chat-id="${currentChat.id}"]`
        );
        if (chatItem) {
            if (pendingChatAction === "completed") {
                chatItem.style.opacity = "0.6";
                chatItem.querySelector(".text-sm.font-medium").innerHTML +=
                    ' <i class="fas fa-check text-green-500 ml-1"></i>';
            } else if (pendingChatAction === "archived") {
                chatItem.style.opacity = "0.6";
                chatItem.querySelector(".text-sm.font-medium").innerHTML +=
                    ' <i class="fas fa-archive text-blue-500 ml-1"></i>';
            }
        }
    }

    // Update badge count
    updateChatsBadge();

    // Close modal
    const modal = document.getElementById("chatActionModal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");

    pendingChatAction = null;
}

function clearChatWindow() {
    const chatHeader = document.getElementById("chatHeader");
    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");

    chatHeader.classList.add("hidden");
    chatInput.classList.add("hidden");

    chatMessages.innerHTML = `
                <div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                    <div class="text-center">
                        <i class="fas fa-comments text-4xl mb-4"></i>
                        <p>Selecciona un chat para comenzar la conversación</p>
                    </div>
                </div>
            `;

    currentChat = null;
}

function updateChatsBadge() {
    const activeChats = Object.values(chats).filter(
        (chat) => chat.status === "active"
    ).length;
    const badge = document.getElementById("chatsBadge");

    if (activeChats > 0) {
        badge.textContent = activeChats;
        badge.classList.remove("hidden");
    } else {
        badge.classList.add("hidden");
    }
}

// Modal functionality
function initModals() {
    const settingsBtn = document.getElementById("settingsBtn");
    const settingsModal = document.getElementById("settingsModal");
    const cancelSettings = document.getElementById("cancelSettings");
    const saveSettings = document.getElementById("saveSettings");
    const appointmentModal = document.getElementById("appointmentModal");
    const closeAppointment = document.getElementById("closeAppointment");
    const dayExpansionModal = document.getElementById("dayExpansionModal");
    const closeDayExpansion = document.getElementById("closeDayExpansion");
    const chatActionModal = document.getElementById("chatActionModal");
    const cancelChatAction = document.getElementById("cancelChatAction");
    const confirmChatAction = document.getElementById("confirmChatAction");
    // Add Appointment Modal Elements
    const addAppointmentBtn = document.getElementById("addAppointmentBtn");
    const addAppointmentModal = document.getElementById("addAppointmentModal");
    const addAppointmentForm = document.getElementById("addAppointmentForm");
    const closeAddAppointment = document.getElementById("closeAddAppointment");
    const cancelAddAppointment = document.getElementById(
        "cancelAddAppointment"
    );

    // Add appointment events
    addAppointmentBtn.addEventListener("click", () => {
        // open modal and set default date/time
        document.getElementById("aptDate").value = currentDate
            .toISOString()
            .slice(0, 10);
        document.getElementById("aptTime").value = "10:00";
        addAppointmentModal.classList.remove("hidden");
        addAppointmentModal.classList.add("flex");
    });

    closeAddAppointment.addEventListener("click", () => {
        addAppointmentModal.classList.add("hidden");
        addAppointmentModal.classList.remove("flex");
    });

    cancelAddAppointment.addEventListener("click", () => {
        addAppointmentModal.classList.add("hidden");
        addAppointmentModal.classList.remove("flex");
    });

    // Submit add appointment (visual only for now; prepares payload for future API)
    addAppointmentForm.addEventListener("submit", (e) => {
        e.preventDefault();

        const dateVal = document.getElementById("aptDate").value;
        const timeVal = document.getElementById("aptTime").value;
        const clientVal = document.getElementById("aptClient").value.trim();
        const phoneVal = document.getElementById("aptPhone").value.trim();
        const serviceVal = document.getElementById("aptService").value;
        const locationVal = document.getElementById("aptLocation").value.trim();
        const notesVal = document.getElementById("aptNotes").value.trim();

        if (!dateVal || !timeVal || !clientVal) {
            alert("Fecha, hora y cliente son obligatorios.");
            return;
        }

        // Prepare payload for potential API
        const payload = {
            date: dateVal, // YYYY-MM-DD
            time: timeVal, // HH:MM
            client: clientVal,
            phone: phoneVal,
            service: serviceVal,
            location: locationVal,
            notes: notesVal,
        };

        console.log("Prepared appointment payload (for future API):", payload);

        // Visual-only: add to local appointments array and refresh UI
        const newId =
            (appointments.length
                ? Math.max(...appointments.map((a) => a.id))
                : 0) + 1;
        const newAppointment = {
            id: newId,
            date: new Date(dateVal + "T00:00:00"),
            time: timeVal,
            client: clientVal,
            phone: phoneVal,
            service: serviceVal,
            location: locationVal,
            status: "pending",
            notes: notesVal,
        };

        appointments.push(newAppointment);
        updateCalendar(); // refresh mini + main views

        // Close modal
        addAppointmentModal.classList.add("hidden");
        addAppointmentModal.classList.remove("flex");

        // Future: send payload to API
        // fetch('/api/appointments', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) })
        //   .then(r => r.json()).then(console.log).catch(console.error);
    });

    settingsBtn.addEventListener("click", () => {
        generateCalendar(currentDate, "nonWorkingCalendar", true);
        settingsModal.classList.remove("hidden");
        settingsModal.classList.add("flex");
    });

    cancelSettings.addEventListener("click", () => {
        settingsModal.classList.add("hidden");
        settingsModal.classList.remove("flex");
    });

    saveSettings.addEventListener("click", () => {
        settingsModal.classList.add("hidden");
        settingsModal.classList.remove("flex");
        updateCalendar();
    });

    closeAppointment.addEventListener("click", () => {
        appointmentModal.classList.add("hidden");
        appointmentModal.classList.remove("flex");
    });

    closeDayExpansion.addEventListener("click", () => {
        dayExpansionModal.classList.add("hidden");
        dayExpansionModal.classList.remove("flex");
    });

    cancelChatAction.addEventListener("click", () => {
        chatActionModal.classList.add("hidden");
        chatActionModal.classList.remove("flex");
        pendingChatAction = null;
    });

    confirmChatAction.addEventListener("click", () => {
        executeChatAction();
    });

    // Close modals on outside click
    [
        settingsModal,
        appointmentModal,
        dayExpansionModal,
        chatActionModal,
    ].forEach((modal) => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.classList.add("hidden");
                modal.classList.remove("flex");
                if (modal === chatActionModal) {
                    pendingChatAction = null;
                }
            }
        });
    });
}

// Service filtering
function initServiceFilter() {
    const serviceFilter = document.getElementById("serviceFilter");
    serviceFilter.addEventListener("change", (e) => {
        selectedService = e.target.value;
        updateCalendarView();
    });
}

// Initialize everything
document.addEventListener("DOMContentLoaded", () => {
    initDarkMode();
    initTabs();
    initNavigation();
    initModals();
    initServiceFilter();
    initChats();
    updateCalendar();
    updateChatsBadge();
});

// Add CSS for active states
const style = document.createElement("style");
style.textContent = `
            .tab-button.active {
                border-color: #3b82f6;
                color: #3b82f6;
            }
            .tab-button {
                border-color: transparent;
                color: #6b7280;
            }
            .tab-button:hover {
                color: #374151;
            }
            .dark .tab-button {
                color: #9ca3af;
            }
            .dark .tab-button:hover {
                color: #d1d5db;
            }
            .dark .tab-button.active {
                color: #60a5fa;
                border-color: #60a5fa;
            }
            .view-btn.active {
                background-color: #3b82f6;
                color: white;
            }
            .view-btn {
                color: #6b7280;
            }
            .view-btn:hover {
                background-color: #f3f4f6;
            }
            .dark .view-btn:hover {
                background-color: #374151;
            }
            .dark .view-btn {
                color: #9ca3af;
            }
        `;
document.head.appendChild(style);
