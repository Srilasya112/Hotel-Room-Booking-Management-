# 🏨 Hotel Room Booking Management System

A full-stack web application built during the **IIIT-H Summer Internship (2nd Year)** to simplify the process of booking and managing hotel rooms. This system ensures a seamless experience for both **guests** and **staff**, integrating everything from user registration to hotel/room/food management.

## 🚀 Features

- 🔐 **User & Staff Login**
- 📝 **Guest Registration**
- 📅 **Room Booking by Guests**
- 🏨 **Hotel & Room Management by Staff**
- 🍽️ **Food Item Selection for Guests**
- 🔔 **Instant Booking Updates**
- 📊 **User-Friendly Dashboards for Staff & Guests**
- 💾 **Data Stored in SQLite**

## 🛠 Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS (with modern UI layout)
- **Tools**: Jinja2, Flask-Routing, Bootstrap (optional)

---

## 📁 Project Structure

```bash
hotel-booking-system/
│
├── backend/
│   ├── app.py              # Flask application
│   ├── db.py               # SQLite DB setup
│   ├── models.py           # DB Models (Users, Hotels, Bookings, etc.)
│   ├── routes/
│   │   ├── guest.py        # Guest dashboard, booking
│   │   └── staff.py        # Staff panel, hotel/room mgmt
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── guest_dashboard.html
│   └── staff_dashboard.html
│
├── static/
│   └── styles.css
│
└── README.md
# Hotel-Room-Booking-Management-
