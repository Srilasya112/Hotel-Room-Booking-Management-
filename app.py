from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = "database.db"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/food_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            name TEXT
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY,
            staff_id INTEGER,
            hotel_name TEXT,
            address TEXT,
            number_of_rooms INTEGER,
            food_options TEXT,
            phone_number TEXT,
            staff_email TEXT,
            hotel_image_path TEXT,  -- Add this line to store the image filename or path
            FOREIGN KEY(staff_id) REFERENCES users(id)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            room_number TEXT,
            room_type TEXT,
            price REAL,
            FOREIGN KEY(hotel_id) REFERENCES hotels(id)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            guest_id INTEGER,
            hotel_id INTEGER,
            room_id INTEGER,
            room_type TEXT,
            food_selected TEXT,
            check_in TEXT,
            check_out TEXT,
            status TEXT,
            num_guests INTEGER DEFAULT 1,
            phone_number TEXT,
            total_cost REAL DEFAULT 0,
            FOREIGN KEY(guest_id) REFERENCES users(id),
            FOREIGN KEY(hotel_id) REFERENCES hotels(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            food_name TEXT,
            price REAL,
            image_path TEXT,
            FOREIGN KEY(hotel_id) REFERENCES hotels(id)
        )""")


if not os.path.exists(DATABASE):
    init_db()
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (email, password, role, name) VALUES (?, ?, ?, ?)",
                (email, password, role, name)
            )
            db.commit()
            flash('Registered successfully! Please sign in.')
            return redirect(url_for('signin'))
        except sqlite3.IntegrityError:
            flash('Email already exists.')
    return render_template('register.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=? AND password=? AND role=?",
            (email, password, role)
        ).fetchone()
        if user:
            session['user_id'] = user['id']
            session['role'] = role
            session['name'] = user['name']
            if role == 'staff':
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('guest_dashboard'))
        else:
            flash("Invalid credentials.")
    return render_template('signin.html')


# ------------------ STAFF PANEL ROUTES --------------------

@app.route('/staff/dashboard', methods=['GET', 'POST'])
def staff_dashboard():
    if session.get('role') != 'staff':
        return redirect(url_for('signin'))
    db = get_db()
    hotels = db.execute("SELECT * FROM hotels WHERE staff_id=?", (session['user_id'],)).fetchall()
    food_items = db.execute("""
        SELECT fi.* FROM food_items fi
        JOIN hotels h ON fi.hotel_id = h.id
        WHERE h.staff_id=?
    """, (session['user_id'],)).fetchall()
    return render_template('staff_dashboard.html', name=session['name'], hotels=hotels, food_items=food_items)

@app.route('/staff/add_hotel', methods=['GET', 'POST'])
def add_hotel():
    if session.get('role') != 'staff':
        return redirect(url_for('signin'))

    if request.method == 'POST':
        hotel_name = request.form.get('hotel_name', '').strip()
        address = request.form.get('address', '').strip()
        number_of_rooms = request.form.get('number_of_rooms', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        staff_email = request.form.get('staff_email', '').strip()
        food_options = ','.join(request.form.getlist('food_options'))

        # Validate required fields
        if not hotel_name or not address or not number_of_rooms or not phone_number or not staff_email:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('add_hotel'))

        # Validate number_of_rooms is integer
        try:
            number_of_rooms_int = int(number_of_rooms)
            if number_of_rooms_int <= 0:
                flash("Number of rooms must be a positive integer.", "danger")
                return redirect(url_for('add_hotel'))
        except ValueError:
            flash("Number of rooms must be a valid integer.", "danger")
            return redirect(url_for('add_hotel'))

        # Handle uploaded file
        file = request.files.get('hotel_image')
        if not file or file.filename == '':
            flash("Please upload a hotel image.", "danger")
            return redirect(url_for('add_hotel'))
        if not allowed_file(file.filename):
            flash("Invalid image format. Allowed formats: png, jpg, jpeg, gif.", "danger")
            return redirect(url_for('add_hotel'))

        filename = secure_filename(file.filename)
        # Ensure upload folder exists
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/hotel_images')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file.save(os.path.join(upload_folder, filename))

        db = get_db()
        try:
            db.execute(
                """
                INSERT INTO hotels 
                (staff_id, hotel_name, address, number_of_rooms, phone_number, staff_email, hotel_image_path, food_options)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session['user_id'], hotel_name, address, number_of_rooms_int, phone_number, staff_email, filename, food_options)
            )
            db.commit()
            flash("Hotel added successfully!", "success")
            return redirect(url_for('staff_dashboard'))
        except Exception as e:
            flash(f"An error occurred while adding hotel: {e}", "danger")
            return redirect(url_for('add_hotel'))

    # GET request
    return render_template('staff_add_hotel.html')

@app.route('/staff/add_room', methods=['GET', 'POST'])
def add_room():
    if session.get('role') != 'staff':
        return redirect(url_for('signin'))
    db = get_db()
    hotels = db.execute("SELECT * FROM hotels WHERE staff_id=?", (session['user_id'],)).fetchall()
    if request.method == 'POST':
        hotel_id = request.form['hotel_id']
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        price = request.form['price']
        if not hotel_id or not room_number or not room_type or not price:
            flash('All fields are required.')
            return render_template('staff_add_room.html', hotels=hotels)
        try:
            db.execute(
                "INSERT INTO rooms (hotel_id, room_number, room_type, price) VALUES (?, ?, ?, ?)",
                (hotel_id, room_number, room_type, price))
            db.commit()
            flash("Room added successfully!")
            return redirect(url_for('add_room'))
        except Exception as e:
            flash(f"Error adding room: {e}")
    return render_template('staff_add_room.html', hotels=hotels)


@app.route('/staff/foods', methods=['GET', 'POST'])
def staff_foods():
    if session.get('role') != 'staff':
        return redirect(url_for('signin'))

    db = get_db()
    hotels = db.execute("SELECT * FROM hotels WHERE staff_id=?", (session['user_id'],)).fetchall()
    if not hotels:
        flash("Please add hotel details first.")
        return redirect(url_for('add_hotel'))

    # Step 1: Determine which hotel is selected
    hotel_id = request.form.get('hotel_id') if request.method == 'POST' else request.args.get('hotel_id')
    if hotel_id:
        selected_hotel = next((h for h in hotels if str(h['id']) == str(hotel_id)), hotels[0])
    else:
        selected_hotel = hotels[0]

    # Step 2: Handle Form Submission
    if request.method == 'POST':
        food_name = request.form['food_name']
        price = request.form['price']
        file = request.files['image']
        if not food_name or not price or not file or not hotel_id:
            flash("All fields required!", "danger")
        elif not allowed_file(file.filename):
            flash("Invalid file format! Only jpg/jpeg/png/gif allowed.", "danger")
        else:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            db.execute(
                "INSERT INTO food_items (hotel_id, food_name, price, image_path) VALUES (?, ?, ?, ?)",
                (hotel_id, food_name, float(price), filename))
            db.commit()
            flash("Food item added!", "success")
            # stay on the same hotel selection
            return redirect(url_for('staff_foods', hotel_id=hotel_id))

    # Step 3: Food list for selected hotel
    food_items = db.execute("SELECT * FROM food_items WHERE hotel_id=?", (selected_hotel['id'],)).fetchall()

    return render_template(
        'staff_foods.html',
        hotels=hotels,
        selected_hotel=selected_hotel,
        food_items=food_items
    )


@app.route('/staff/manage_bookings')
def manage_bookings():
    if session.get('role') != 'staff':
        return redirect(url_for('signin'))
    db = get_db()
    staff_id = session['user_id']
    bookings = db.execute("""
        SELECT 
            u.name AS guest_name,
            h.hotel_name,
            r.room_number,
            r.room_type,
            b.food_selected,
            b.check_in,
            b.check_out,
            b.status,
            b.num_guests,
            b.phone_number
        FROM bookings b
        JOIN users u ON b.guest_id = u.id
        JOIN hotels h ON b.hotel_id = h.id
        JOIN rooms r ON b.room_id = r.id
        WHERE h.staff_id = ?
        ORDER BY b.id DESC
    """, (staff_id,)).fetchall()
    return render_template('staff_manage_bookings.html', bookings=bookings)



# ------------------ END STAFF PANEL ROUTES ----------------


@app.route('/guest/dashboard')
def guest_dashboard():
    if session.get('role') != 'guest':
        return redirect(url_for('signin'))
    db = get_db()
    bookings = db.execute("""
        SELECT 
            b.*, 
            h.hotel_name, 
            h.address,
            h.hotel_image_path,
            h.phone_number AS hotel_phone_number,
            h.staff_email
        FROM bookings b
        JOIN hotels h ON b.hotel_id = h.id
        WHERE b.guest_id=?
        ORDER BY b.id DESC
    """, (session['user_id'],)).fetchall()
    return render_template('guest_dashboard.html', name=session['name'], bookings=bookings)


@app.route('/hotels')
def hotels():
    db = get_db()
    hotels = db.execute("SELECT * FROM hotels").fetchall()
    return render_template('hotel_list.html', hotels=hotels)


@app.route('/book/<int:hotel_id>', methods=['GET', 'POST'])
def book(hotel_id):
    if session.get('role') != 'guest':
        return redirect(url_for('signin'))

    db = get_db()

    hotel = db.execute("SELECT * FROM hotels WHERE id = ?", (hotel_id,)).fetchone()

    food_items = db.execute("SELECT * FROM food_items WHERE hotel_id = ?", (hotel_id,)).fetchall()
    food_items_menu = [dict(row) for row in food_items]

    room_rows = db.execute("SELECT * FROM rooms WHERE hotel_id = ?", (hotel_id,)).fetchall()
    rooms = [dict(row) for row in room_rows]

    if request.method == 'POST':
        try:
            room_type = request.form['room_type']
            room_id = request.form['room_id']
            check_in = request.form['check_in']
            check_out = request.form['check_out']
            num_guests = int(request.form['num_guests'])
            phone_number = request.form.get('phone_number', '').strip()
            status = "Confirmed"

            selected_food_ids = request.form.getlist('food_items_selected')
            selected_food_names = []
            if selected_food_ids:
                placeholders = ','.join('?' for _ in selected_food_ids)
                food_rows = db.execute(
                    f"SELECT food_name FROM food_items WHERE id IN ({placeholders})", selected_food_ids
                ).fetchall()
                selected_food_names = [row['food_name'] for row in food_rows]

            custom_food_raw = request.form.get('custom_food', '').strip()
            custom_food_items = []
            if custom_food_raw:
                custom_food_items = [item.strip() for item in custom_food_raw.split('\n') if item.strip()]
                custom_food_names = [f"Custom: {item}" for item in custom_food_items]
                selected_food_names.extend(custom_food_names)

            food_selected_str = ', '.join(selected_food_names)

            room_info = db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
            if room_info is None:
                flash("Selected room does not exist.", "danger")
                return redirect(url_for('book', hotel_id=hotel_id))
            room_price = room_info['price']

            dt_check_in = datetime.strptime(check_in, "%Y-%m-%d")
            dt_check_out = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (dt_check_out - dt_check_in).days
            if nights <= 0:
                flash("Check-out date must be after check-in date.", "danger")
                return redirect(url_for('book', hotel_id=hotel_id))

            cost_room = room_price * nights
            cost_guests = 0
            if num_guests > 1:
                cost_guests = 500 * (num_guests - 1)
            cost_custom_food = 250 * len(custom_food_items)

            total_cost = cost_room + cost_guests + cost_custom_food

            db.execute("""
                INSERT INTO bookings 
                (guest_id, hotel_id, room_id, room_type, food_selected, check_in, check_out, status, num_guests, phone_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session['user_id'], hotel_id, room_id, room_type, food_selected_str,
                check_in, check_out, status, num_guests, phone_number
            ))
            db.commit()

            flash(f"Booking successful! Total cost: ₹{total_cost:.2f}", "success")
            return redirect(url_for('guest_dashboard'))

        except Exception as e:
            db.rollback()
            flash(f"An error occurred during booking: {str(e)}", "danger")
            return redirect(url_for('book', hotel_id=hotel_id))

    return render_template('book.html', hotel=hotel, food_items_menu=food_items_menu, rooms=rooms)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    init_db()    # Initialize or verify DB schema at startup
    app.run(debug=True)