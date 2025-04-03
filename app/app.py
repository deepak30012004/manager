from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import base64
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
import logging
import pdfkit 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
# SMTP Configuration


# Initialize Flask App
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "supersecurejwtkey"  # Change this for security
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Caching Configuration
app.config['CACHE_TYPE'] = 'SimpleCache'  # In-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Cache timeout (seconds)

# Initialize Caching
cache = Cache(app)

CORS(app, supports_credentials=True)
jwt = JWTManager(app)

DB_FILE = "visitors.db"
UPLOAD_FOLDER = os.path.join(os.getcwd(), "photo")  # Create a folder named 'pdfs' in the project directory

# Ensure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

PDF_FOLDER = os.path.join(os.getcwd(), "pdfs")  # Create a folder named 'pdfs' in the project directory

# Ensure the folder exists
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

# # System Failure Handling: Database Connection with Fault Tolerance
# def get_db_connection(retries=3, delay=2):
#     """
#     Establish a database connection with fault tolerance.
#     Retries up to retries times with a delay between attempts.
#     """
#     for attempt in range(retries):
#         try:
#             conn = sqlite3.connect(DB_FILE)
#             return conn
#         except sqlite3.Error as e:
#             logging.error(f"Database connection failed (Attempt {attempt+1}): {e}")
#             time.sleep(delay)  # Wait before retrying
#     raise ConnectionError("Failed to connect to the database after multiple attempts.")
# Initialize Database and Ensure 'role' Column Exists
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create Users table for staff and managers
    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff'
        )
    ''')

    # Create Visitors table for visitors
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            contact_info TEXT NOT NULL,
            purpose_of_visit TEXT NOT NULL,
          
            host_employee_name TEXT NOT NULL,
            host_department TEXT NOT NULL,
            company_name TEXT,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            photo_path TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Ensure the 'role' column exists
    cursor.execute("PRAGMA table_info(users);")
    columns = [column[1] for column in cursor.fetchall()]
    if 'role' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'staff';")
        conn.commit()
        app.logger.info("Added 'role' column to the 'users' table.")

    conn.commit()
    conn.close()

init_db()


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "deepaksingh30012004@gmail.com"  # Change this to your email
SENDER_PASSWORD = "pqmxvsiwfsnbkkia"



def send_email(recipient_email, visitor_name, visitor_id):
    """
    Sends an approval email with a QR code link to open the visitor card as a PDF.
    """
    subject = "Visitor Approval Notification"
    qr_code_link = f"http://127.0.0.1:5000/qr/{visitor_id}"  # Adjust domain for production

    body = f"""
    Dear {visitor_name},

    Your visit has been approved. You can download your Visitor Card from the link below:

    Visitor Card: {qr_code_link}

    Best Regards,
    Visitor Management Team
    """

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        app.logger.info(f"Approval email sent to {recipient_email}")
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")



from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

def generate_pdf(visitor_id, visitor_name, contact_info, purpose_of_visit, host_employee_name, check_in_time, photo_path):
    pdf_path = os.path.join(PDF_FOLDER, f"visitor_{visitor_id}.pdf")
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 14)

    c.drawString(200, 750, "Visitor Approval Receipt")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Visitor ID: {visitor_id}")
    c.drawString(100, 680, f"Full Name: {visitor_name}")
    c.drawString(100, 660, f"Contact Info: {contact_info}")
    c.drawString(100, 640, f"Purpose of Visit: {purpose_of_visit}")
    c.drawString(100, 620, f"Host Employee: {host_employee_name}")
    c.drawString(100, 600, f"Check-in Time: {check_in_time}")

    # **📸 Add Visitor's Photo**
    if photo_path and os.path.exists(photo_path):  
        img = ImageReader(photo_path)
        c.drawImage(img, 400, 620, width=100, height=100)  # Adjust size & position
    else:
        c.drawString(400, 620, "No Photo Available")

    c.showPage()
    c.save()
    
    return pdf_path





# User class for staff and managers (Encapsulation, Inheritance)
class User:
    def __init__(self, username, password_hash=None, role=None):
        self.username = username
        self.password_hash = password_hash
        self.role = role  # 'staff' or 'manager'

    def save_to_db(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           (self.username, self.password_hash, self.role))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Username already exists")
        finally:
            conn.close()

    @staticmethod
    def get_user_by_username(username):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return User(username, user[1], user[2])
        return None

# Visitor class for visitor management
class Visitor:
    def __init__(self, full_name, contact_info, purpose_of_visit, host_employee_name, host_department, company_name="", check_in_time=None, photo_path=None):
        self.full_name = full_name
        self.contact_info = contact_info
        self.purpose_of_visit = purpose_of_visit
        self.host_employee_name = host_employee_name
        self.host_department = host_department
        self.company_name = company_name
        self.check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
         # Convert to IST
       

        self.photo_path = photo_path
        self.photo_path = photo_path

    def save_to_db(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(''' 
        INSERT INTO visitors (full_name, contact_info, purpose_of_visit, host_employee_name, host_department, company_name, check_in_time, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.full_name, self.contact_info, self.purpose_of_visit, self.host_employee_name, self.host_department, self.company_name, self.check_in_time, self.photo_path))
        conn.commit()
        visitor_id = cursor.lastrowid
        conn.close()
        return visitor_id
    @classmethod
    def get_all_visitors(cls):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, full_name, contact_info, purpose_of_visit, 
               host_employee_name, check_in_time, check_out_time, 
               status, photo_path 
        FROM visitors 
        ORDER BY check_in_time DESC""")
        result = cursor.fetchall()
        conn.close()
        return result
   





   
    








# Initialize Flask routes
@app.route("/")
def home():
    return "Visitor Management System API is running!"



@app.route("/qr/<int:visitor_id>", methods=["GET"])
def serve_pdf(visitor_id):
    """
    Serve the visitor card as a downloadable PDF when the QR link is clicked.
    """
    pdf_path = os.path.join(PDF_FOLDER, f"visitor_{visitor_id}.pdf")
    
    if os.path.exists(pdf_path):
        return send_from_directory(PDF_FOLDER, f"visitor_{visitor_id}.pdf", as_attachment=True)
    else:
        return jsonify({"error": "Visitor card not found"}), 404

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        role = data.get("role")  # staff or manager

        if not username or not password or not role:
            return jsonify({"error": "Username, password, and role are required"}), 400

        hashed_password = generate_password_hash(password)

        user = User(username, hashed_password, role)
        user.save_to_db()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        app.logger.error(f"Error during signup: {e}")
        return jsonify({"error": "An error occurred during signup"}), 500


##LOGIN AUTHENTICATION
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.get_user_by_username(username)
    if user and check_password_hash(user.password_hash, password):
        token = create_access_token(identity=username)
        return jsonify({"message": "Login successful", "token": token, "role": user.role}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401





# # Ensure the "photo" directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), "photo")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # ✅ Create folder if not exists

@app.route('/visitors', methods=['POST'])
@jwt_required()
def add_visitor():
    current_user = get_jwt_identity()
    user = User.get_user_by_username(current_user)

    if user.role != 'staff':
        return jsonify({"error": "You do not have permission to add visitors"}), 403

    data = request.json
    full_name = data.get("full_name")
    contact_info = data.get("contact_info")
    purpose_of_visit = data.get("purpose_of_visit")
    host_employee_name = data.get("host_employee_name")
    host_department = data.get("host_department")
    company_name = data.get("company_name", "")
    check_in_time = data.get("check_in_time") or None
    photo_base64 = data.get("photo", "")

    photo_filename = None
    photo_path = None  # To store the path

    if photo_base64:
        try:
            if "," in photo_base64:
                photo_base64 = photo_base64.split(",")[1]  # Remove base64 header
            
            photo_data = base64.b64decode(photo_base64)  # Decode base64
            photo_filename = f"{full_name.replace(' ', '_')}.jpg"  # Filename
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)  # Full path
            
            # ✅ Ensure the "photo" directory exists
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)

            with open(photo_path, "wb") as f:
                f.write(photo_data)  # Save the image
            
            # ✅ Verify if the image was saved
            if os.path.exists(photo_path):
                app.logger.info(f"✅ Image saved successfully at {photo_path}")
            else:
                app.logger.error(f"❌ Image save failed!")
                photo_path = None  # Reset to None if save failed

        except Exception as e:
            app.logger.error(f"❌ Failed to save image for {full_name}: {e}")
            photo_path = None  # Reset to None in case of error

    # ✅ Store the photo **full path** in the database
    visitor = Visitor(
        full_name, contact_info, purpose_of_visit, 
        host_employee_name, host_department, company_name, 
        check_in_time, photo_path  # Save full path
    )
    visitor_id = visitor.save_to_db()

    return jsonify({
        "message": "Visitor added successfully", 
        "id": visitor_id,
        "photo_path": photo_path  # Return saved photo path
    }), 201


##AUTHENTICATION REQUIRE FOR FETTING VISITOR
@app.route('/visitors', methods=['GET'])
@jwt_required()
 # Cache for 60 seconds
def get_visitors():
    current_user = get_jwt_identity()
    user = User.get_user_by_username(current_user)

    # if user.role != 'manager':
    #     return jsonify({"error": "You do not have permission to view visitors"}), 403

    visitors = Visitor.get_all_visitors()
    visitor_list = [
        {"id": v[0], "full_name": v[1], "contact_info": v[2], "purpose_of_visit": v[3],"host_employee_name": v[4],"check_in_time":v[5],"check_out_time":v[6], "status": v[7], "photo_path": v[8]}
        
        for v in visitors
    ]
    return jsonify(visitor_list), 200

@app.route("/visitors/approve/<int:visitor_id>", methods=['PUT'])
@jwt_required()
def approve_visitor(visitor_id):
    """
    Approves a visitor and generates their visitor card as a PDF with photo.
    """
    current_user = get_jwt_identity()
    user = User.get_user_by_username(current_user)

    if user.role != 'manager':
        return jsonify({"error": "You do not have permission to approve visitors"}), 403

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT full_name, contact_info, purpose_of_visit, host_employee_name, check_in_time, photo_path FROM visitors WHERE id = ?", (visitor_id,))
        visitor = cursor.fetchone()
        if not visitor:
            return jsonify({"error": "Visitor not found"}), 404

        visitor_name, contact_info, purpose_of_visit, host_employee_name, check_in_time, photo_path = visitor

        cursor.execute("UPDATE visitors SET status = 'approved' WHERE id = ?", (visitor_id,))
        conn.commit()

        # Construct full photo path
        photo_path = os.path.join(UPLOAD_FOLDER, photo_path) if photo_path else None  

        # Generate PDF for the visitor card with photo
        pdf_path = generate_pdf(visitor_id, visitor_name, contact_info, purpose_of_visit, host_employee_name, check_in_time, photo_path)

        # Send email with the QR link
        send_email(contact_info, visitor_name, visitor_id)

    except Exception as e:
        conn.rollback()
        app.logger.error(f"❌ Failed to approve visitor {visitor_id}: {e}")
        return jsonify({"error": "Failed to approve visitor"}), 500
    finally:
        conn.close()

    return jsonify({"message": "✅ Visitor approved, PDF generated, and email sent"}), 200



from datetime import datetime

@app.route('/visitors/checkout/<int:visitor_id>', methods=['PUT'])
@jwt_required()
def checkout_visitor(visitor_id):
    """
    Updates the checkout time for a visitor when they check out.
    """
    current_user = get_jwt_identity()
    user = User.get_user_by_username(current_user)

    # Staff and Manager can update checkout time (if necessary)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Get the current time to store as checkout time
        checkout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update the checkout time in the database
        cursor.execute("UPDATE visitors SET check_out_time = ? WHERE id = ?", (checkout_time, visitor_id))
        conn.commit()

        return jsonify({"message": f"Visitor {visitor_id} checked out successfully at {checkout_time}."}), 200
    except Exception as e:
        conn.rollback()
        app.logger.error(f"❌ Failed to checkout visitor {visitor_id}: {e}")
        return jsonify({"error": "Failed to checkout visitor"}), 500
    finally:
        conn.close()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
