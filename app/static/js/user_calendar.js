(() => {
    const monthLabel = document.getElementById("monthLabel");
    const todayLabel = document.getElementById("todayLabel");
    const calendarGrid = document.getElementById("calendarGrid");
    const bookingModal = document.getElementById("bookingModal");
    const bookingForm = document.getElementById("bookingForm");
    const bookDateInput = document.getElementById("bookDate");
    const bookTime = document.getElementById("bookTime");
    const bookName = document.getElementById("bookName");
    const bookPhone = document.getElementById("bookPhone");
    const cancelBooking = document.getElementById("cancelBooking");
    const closeModal = document.getElementById("closeModal");
    const toggleDark = document.getElementById("toggleDark");

    let current = new Date();
    current.setDate(1);
    // TODO: CAMBIAR EL USO DE LOCALSTORAGE A BACKEND
    const STORAGE_KEY = "userBookings";

    function loadBookings() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        } catch {
            return [];
        }
    }
    function saveBookings(list) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    }
    function isBooked(day) {
        const iso = day.toISOString().slice(0, 10);
        return loadBookings().some((b) => b.dateISO === iso);
    }
    function isPast(day) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return day < today;
    }

    function render() {
        const year = current.getFullYear(),
            month = current.getMonth();
        monthLabel.textContent = current.toLocaleDateString("es-ES", {
            month: "long",
            year: "numeric",
        });
        todayLabel.textContent = new Date().toLocaleDateString("es-ES");

        const firstDay = new Date(year, month, 1);
        const dayOfWeek = (firstDay.getDay() + 6) % 7; // lunes=0
        const start = new Date(firstDay);
        start.setDate(firstDay.getDate() - dayOfWeek);

        calendarGrid.innerHTML = "";
        for (let i = 0; i < 42; i++) {
            const day = new Date(start);
            day.setDate(start.getDate() + i);
            const btn = document.createElement("button");
            btn.className = "p-3 text-sm rounded text-center transition";
            if (day.getMonth() !== month)
                btn.classList.add("text-gray-400", "dark:text-gray-600");
            else
                btn.classList.add(
                    "text-gray-900",
                    "dark:text-white",
                    "bg-white",
                    "dark:bg-gray-800"
                );

            if (isPast(day)) {
                btn.classList.add("opacity-40", "cursor-not-allowed");
                btn.disabled = true;
            } else if (isBooked(day)) {
                btn.classList.add("bg-green-100", "dark:bg-green-900/30");
                btn.disabled = true;
            } else if (day.getMonth() === month) {
                btn.classList.add(
                    "hover:bg-gray-100",
                    "dark:hover:bg-gray-700"
                );
                btn.addEventListener("click", () => openBooking(day));
            } else {
                btn.disabled = true;
            }

            btn.innerHTML =
                `<div class="text-xs">${day.getDate()}</div>` +
                (isBooked(day)
                    ? `<div class="mt-1 text-[10px] text-green-700 dark:text-green-200">Reservado</div>`
                    : "");
            calendarGrid.appendChild(btn);
        }
    }

    function openBooking(day) {
        const iso = day.toISOString().slice(0, 10);
        bookDateInput.value = day.toLocaleDateString("es-ES", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
        });
        bookingForm.dataset.dateIso = iso;
        bookTime.value = "10:00";
        bookName.value = "";
        bookPhone.value = "";
        bookingModal.classList.remove("hidden");
        bookingModal.classList.add("flex", "items-center", "justify-center");
    }

    function closeBooking() {
        bookingModal.classList.add("hidden");
        bookingModal.classList.remove("flex", "items-center", "justify-center");
        bookingForm.removeAttribute("data-date-iso");
    }

    bookingForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const iso = bookingForm.dataset.dateIso;
        const time = bookTime.value;
        const name = bookName.value.trim();
        // prefer value from dropdown, fallback to dataset.serviceId (selection from list)
        const service = document.getElementById('bookService')?.value || bookingForm.dataset.serviceId || "";
        if (!iso || !time || !name) {
            alert("Completa nombre y hora.");
            return;
        }
        const all = loadBookings();
        all.push({ dateISO: iso, time, name, phone: bookPhone.value.trim(), service });
        saveBookings(all);
        closeBooking();
        render();
        setTimeout(
            () =>
                alert(
                    `Cita confirmada para ${name} el ${new Date(
                        iso
                    ).toLocaleDateString("es-ES")} a las ${time}`
                ),
            100
        );
        // TODO: enviar payload al servidor si se integra backend (incluye campo 'service')
    });

    cancelBooking.addEventListener("click", closeBooking);
    closeModal.addEventListener("click", closeBooking);

    document.getElementById("prevMonth").addEventListener("click", () => {
        current.setMonth(current.getMonth() - 1);
        render();
    });
    document.getElementById("nextMonth").addEventListener("click", () => {
        current.setMonth(current.getMonth() + 1);
        render();
    });

    toggleDark &&
        toggleDark.addEventListener("click", () => {
            document.documentElement.classList.toggle("dark");
            localStorage.setItem(
                "darkMode",
                document.documentElement.classList.contains("dark")
            );
        });

    if (localStorage.getItem("darkMode") === "true")
        document.documentElement.classList.add("dark");

    // initial
    render();
})();

