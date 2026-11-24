// RoomBook page. Finished and owned by the frontend team: do not edit.
// It talks to the backend only through the HTTP API in docs/spec.md.

const statusEl = document.getElementById("status");
const dayEl = document.getElementById("day");
const roomsEl = document.getElementById("rooms");
const formEl = document.getElementById("book-form");
const roomEl = document.getElementById("room");
const startEl = document.getElementById("start");
const endEl = document.getElementById("end");
const nameEl = document.getElementById("name");
const formMessageEl = document.getElementById("form-message");

// What the page tells the user for each error code the backend can send.
const MESSAGES = {
  invalid_request: "The request was not valid.",
  invalid_name: "Enter your name, 40 characters at most.",
  invalid_time: "Check the times: bookings start and end on the hour or half hour, between 08:00 and 22:00, and last at most 3 hours.",
  room_not_found: "That room does not exist. Reload the page.",
  booking_not_found: "That booking was already cancelled.",
  overlap: "That room is already booked for part of that time. Pick another time or room.",
  daily_limit: "You already have 2 bookings on that day. Cancel one to book another."
};

let rooms = [];

class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function api(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  if (response.status === 204) {
    return null;
  }
  let data = null;
  try {
    data = await response.json();
  } catch (err) {
    data = null;
  }
  if (!response.ok) {
    const code = data && typeof data.error === "string" ? data.error : "";
    const message = data && typeof data.message === "string" ? data.message : "";
    throw new ApiError(response.status, code, message);
  }
  return data;
}

function explain(err) {
  if (err instanceof ApiError) {
    const known = MESSAGES[err.code];
    if (known && err.code === "invalid_request" && err.message) {
      return known + " " + err.message;
    }
    if (known) {
      return known;
    }
    return "The server answered " + err.status + (err.message ? ": " + err.message : ".");
  }
  return "Cannot reach the server. Is the backend running?";
}

function todayIso() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return now.getFullYear() + "-" + month + "-" + day;
}

function halfHours(from, to) {
  // Every "HH:MM" from `from` to `to` inclusive, in 30-minute steps.
  const times = [];
  for (let minutes = from * 60; minutes <= to * 60; minutes += 30) {
    const h = String(Math.floor(minutes / 60)).padStart(2, "0");
    const m = String(minutes % 60).padStart(2, "0");
    times.push(h + ":" + m);
  }
  return times;
}

function fillSelect(select, values, selected) {
  select.innerHTML = "";
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    if (value === selected) {
      option.selected = true;
    }
    select.appendChild(option);
  }
}

function renderRooms(bookings) {
  roomsEl.innerHTML = "";
  for (const room of rooms) {
    const card = document.createElement("article");
    card.className = "room";

    const title = document.createElement("h2");
    title.textContent = room.name;
    const seats = document.createElement("p");
    seats.className = "seats";
    seats.textContent = "Seats " + room.capacity;
    card.appendChild(title);
    card.appendChild(seats);

    const list = document.createElement("ul");
    const mine = bookings.filter((b) => b.room_id === room.id);
    if (mine.length === 0) {
      const empty = document.createElement("li");
      empty.className = "empty";
      empty.textContent = "Free all day";
      list.appendChild(empty);
    }
    for (const booking of mine) {
      const item = document.createElement("li");
      const text = document.createElement("span");
      text.textContent = booking.start + " to " + booking.end + ", " + booking.booked_by;
      const cancel = document.createElement("button");
      cancel.type = "button";
      cancel.className = "cancel";
      cancel.textContent = "Cancel";
      cancel.setAttribute("aria-label", "Cancel the booking from " + booking.start + " to " + booking.end + " for " + booking.booked_by);
      cancel.addEventListener("click", () => cancelBooking(booking.id));
      item.appendChild(text);
      item.appendChild(cancel);
      list.appendChild(item);
    }
    card.appendChild(list);
    roomsEl.appendChild(card);
  }
}

async function loadDay() {
  statusEl.textContent = "Loading...";
  try {
    const bookings = await api("GET", "/api/bookings?date=" + encodeURIComponent(dayEl.value));
    renderRooms(bookings);
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = explain(err);
  }
}

async function start() {
  dayEl.value = todayIso();
  fillSelect(startEl, halfHours(8, 21.5), "09:00");
  fillSelect(endEl, halfHours(8.5, 22), "10:00");
  try {
    rooms = await api("GET", "/api/rooms");
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      statusEl.textContent = "The server answered 404 for /api/rooms. The backend is not built yet.";
    } else {
      statusEl.textContent = explain(err);
    }
    return;
  }
  roomEl.innerHTML = "";
  for (const room of rooms) {
    const option = document.createElement("option");
    option.value = String(room.id);
    option.textContent = room.name + " (seats " + room.capacity + ")";
    roomEl.appendChild(option);
  }
  await loadDay();
}

async function book(event) {
  event.preventDefault();
  formMessageEl.textContent = "";
  const body = {
    room_id: Number(roomEl.value),
    date: dayEl.value,
    start: startEl.value,
    end: endEl.value,
    booked_by: nameEl.value
  };
  try {
    const booking = await api("POST", "/api/bookings", body);
    formMessageEl.textContent = "Booked " + booking.start + " to " + booking.end + " for " + booking.booked_by + ".";
    nameEl.value = "";
    await loadDay();
  } catch (err) {
    formMessageEl.textContent = explain(err);
  }
}

async function cancelBooking(id) {
  formMessageEl.textContent = "";
  try {
    await api("DELETE", "/api/bookings/" + id);
    formMessageEl.textContent = "Booking cancelled.";
  } catch (err) {
    formMessageEl.textContent = explain(err);
  }
  await loadDay();
}

dayEl.addEventListener("change", loadDay);
formEl.addEventListener("submit", book);
start();
