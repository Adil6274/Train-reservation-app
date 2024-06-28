from flask import Flask, render_template, request
import pickle
import random
import qrcode
import os
from fpdf import FPDF
from PIL import Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from twilio.rest import Client
import string
from dotenv import load_dotenv

load_dotenv()

# Access the variables like:
gmail_user = os.getenv('GMAIL_USER')
gmail_password = os.getenv('GMAIL_PASSWORD')
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')

app = Flask(__name__)

class Train:
    def __init__(self, trainno, trainname, startingpoint, destination, nofafseat, nofasseat, noffsseat, nofacseat, nofssseat):
        self.trainno = trainno
        self.trainname = trainname
        self.startingpoint = startingpoint
        self.destination = destination
        self.nofafseat = nofafseat
        self.nofasseat = nofasseat
        self.noffsseat = noffsseat
        self.nofacseat = nofacseat
        self.nofssseat = nofssseat

    def display(self):
        print(f"TRAIN NUMBER: {self.trainno}")
        print(f"TRAIN NAME: {self.trainname}")
        print(f"NO OF A/C FIRST CLASS SEATS: {self.nofafseat}")
        print(f"NO OF A/C SECOND CLASS SEATS: {self.nofasseat}")
        print(f"NO OF FIRST CLASS SLEEPER SEATS: {self.noffsseat}")
        print(f"NO OF A/C CHAIR CLASS SEATS: {self.nofacseat}")
        print(f"NO OF SECOND CLASS SLEEPER SEATS: {self.nofssseat}")
        print(f"STARTING POINT: {self.startingpoint}")
        print(f"DESTINATION: {self.destination}")
        input("PRESS ANY KEY TO CONTINUE ")

class Tickets:
    def __init__(self):
        self.resno = None  # Initialize reservation number counter
        self.toaf = 0
        self.nofaf = 0
        self.toas = 0
        self.nofas = 0
        self.tofs = 0
        self.noffs = 0
        self.toac = 0
        self.nofac = 0
        self.toss = 0
        self.nofss = 0
        self.age = 0
        self.status = ""
        self.name = ""
        self.email = ""
        self.phone = ""
        try:
            with open("Train1.dat", "rb") as file:
                self.trains = pickle.load(file)
        except (FileNotFoundError, EOFError):
            self.trains = []

        try:
            with open("Ticket1.dat", "rb") as file:
                self.tickets = pickle.load(file)
        except (FileNotFoundError, EOFError):
            self.tickets = []

    def generate_reservation_number(self):
        digits_part = f"{random.randint(0, 999999):06d}"  # 6-digit random number
        letters_part = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.resno = digits_part + letters_part  # Assign directly as a concatenated string
        return self.resno

    def generate_receipt(self, train):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Reservation Receipt", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Reservation Number: {self.resno}", ln=True)
        pdf.cell(200, 10, txt=f"Name: {self.name}", ln=True)
        pdf.cell(200, 10, txt=f"Age: {self.age}", ln=True)
        pdf.cell(200, 10, txt=f"Status: {self.status}", ln=True)
        pdf.cell(200, 10, txt=f"Train Number: {train.trainno}", ln=True)
        pdf.cell(200, 10, txt=f"Train Name: {train.trainname}", ln=True)
        pdf.cell(200, 10, txt=f"Starting Point: {train.startingpoint}", ln=True)
        pdf.cell(200, 10, txt=f"Destination: {train.destination}", ln=True)

        qr_data = f"Reservation Number: {self.resno}\nName: {self.name}\nAge: {self.age}\nStatus: {self.status}\nTrain Number: {train.trainno}\nTrain Name: {train.trainname}\nStarting Point: {train.startingpoint}\nDestination: {train.destination}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img_path = f"qr_{self.resno}.png"
        img.save(img_path)

        img = Image.open(img_path).convert('RGB')
        img.save(img_path)

        pdf.image(img_path, x=10, y=100, w=50)
        pdf_output = f"Reservation_{self.resno}.pdf"
        pdf.output(pdf_output)
        print(f"Receipt generated: {pdf_output}")
        return pdf_output

    def send_email(self, pdf_path):
        sender_email = gmail_user
        receiver_email = self.email
        password = gmail_password

        subject = "Reservation Receipt"
        body = "Please find your reservation receipt attached."

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Attach PDF file
        filename = os.path.basename(pdf_path)
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )
        message.attach(part)

        text = message.as_string()

        # Send email
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)
            print("Email sent successfully")
        except Exception as e:
            print(f"Error sending email: {e}")
        finally:
            server.quit()

    def send_sms(self, train):
        account_sid = twilio_account_sid
        auth_token = twilio_auth_token
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=f"Reservation Confirmed: {self.status}\nReservation No: {self.resno}\nName: {self.name}\nTrain: {train.trainname}\nFrom: {train.startingpoint}\nTo: {train.destination}",
            from_=twilio_phone_number,
            to=self.phone
        )
        print(f"SMS sent: {message.sid}")

    def display(self):
        try:
            with open("Ticket1.dat", "rb") as file:
                tickets = pickle.load(file)
        except (FileNotFoundError, EOFError):
            print("ERROR IN THE FILE")
            return

        n = input("ENTER THE RESERVATION NO: ")
        found = False

        for ticket in tickets:
            if ticket.resno == n:
                found = True
                print(f"NAME: {ticket.name}")
                print(f"AGE: {ticket.age}")
                print(f"PRESENT STATUS: {ticket.status}")
                print(f"RESERVATION NUMBER: {ticket.resno}")
                break

        if not found:
            a = input("UNRECOGNIZED RESERVATION NO !!! WANNA RETRY? (Y/N): ")
            if a.lower() == 'y':
                self.display()

    def reservation(self):
        self.resno = self.generate_reservation_number()

        tno = int(input("ENTER THE TRAIN NO: "))
        found = False

        try:
            with open("Train1.dat", "rb") as file:
                trains = pickle.load(file)
        except (FileNotFoundError, EOFError):
            print("ERROR IN THE FILE")
            return

        for train in trains:
            if train.trainno == tno:
                found = True
                selected_train = train
                self.nofaf = train.nofafseat
                self.nofas = train.nofasseat
                self.noffs = train.noffsseat
                self.nofac = train.nofacseat
                self.nofss = train.nofssseat
                break

        if not found:
            print("INVALID TRAIN NO !!!")
            return

        tickets = []
        try:
            with open("Ticket1.dat", "rb") as file:
                tickets = pickle.load(file)
        except (FileNotFoundError, EOFError):
            pass  # No previous tickets exist

        self.name = input("ENTER THE PASSENGER'S NAME: ")
        self.age = int(input("ENTER THE PASSENGER'S AGE: "))
        self.email = input("ENTER THE PASSENGER'S EMAIL: ")
        self.phone = input("ENTER THE PASSENGER'S PHONE: ")

        print("1. A/C FIRST CLASS")
        print("2. A/C SECOND CLASS")
        print("3. FIRST CLASS SLEEPER")
        print("4. A/C CHAIR CLASS")
        print("5. SECOND CLASS SLEEPER")
        choice = int(input("ENTER YOUR CHOICE: "))

        if choice == 1 and self.nofaf > 0:
            self.status = "A/C FIRST CLASS"
            self.nofaf -= 1
        elif choice == 2 and self.nofas > 0:
            self.status = "A/C SECOND CLASS"
            self.nofas -= 1
        elif choice == 3 and self.noffs > 0:
            self.status = "FIRST CLASS SLEEPER"
            self.noffs -= 1
        elif choice == 4 and self.nofac > 0:
            self.status = "A/C CHAIR CLASS"
            self.nofac -= 1
        elif choice == 5 and self.nofss > 0:
            self.status = "SECOND CLASS SLEEPER"
            self.nofss -= 1
        else:
            print("SEATS NOT AVAILABLE!")
            return

        tickets.append(self)

        with open("Ticket1.dat", "wb") as file:
            pickle.dump(tickets, file)

        for i, train in enumerate(trains):
            if train.trainno == tno:
                trains[i] = selected_train

        with open("Train1.dat", "wb") as file:
            pickle.dump(trains, file)

        print(f"RESERVATION SUCCESSFUL. YOUR RESERVATION NUMBER IS {self.resno}")

        # Generate receipt and send notifications
        pdf_path = self.generate_receipt(selected_train)
        self.send_email(pdf_path)
        self.send_sms(selected_train)

# Initialize the Tickets object
tickets = Tickets()

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        trainno = int(request.form['trainno'])
        name = request.form['name']
        age = int(request.form['age'])
        email = request.form['email']
        phone = request.form['phone']
        status = request.form['status']
        
        # Create reservation
        ticket = Tickets()
        ticket.name = name
        ticket.age = age
        ticket.email = email
        ticket.phone = phone
        
        found = False
        for train in ticket.trains:
            if train.trainno == trainno:
                found = True
                selected_train = train
                if status == "A/C FIRST CLASS" and train.nofafseat > 0:
                    ticket.status = "A/C FIRST CLASS"
                    train.nofafseat -= 1
                elif status == "A/C SECOND CLASS" and train.nofasseat > 0:
                    ticket.status = "A/C SECOND CLASS"
                    train.nofasseat -= 1
                elif status == "FIRST CLASS SLEEPER" and train.noffsseat > 0:
                    ticket.status = "FIRST CLASS SLEEPER"
                    train.noffsseat -= 1
                elif status == "A/C CHAIR CLASS" and train.nofacseat > 0:
                    ticket.status = "A/C CHAIR CLASS"
                    train.nofacseat -= 1
                elif status == "SECOND CLASS SLEEPER" and train.nofssseat > 0:
                    ticket.status = "SECOND CLASS SLEEPER"
                    train.nofssseat -= 1
                else:
                    return "SEATS NOT AVAILABLE!"
                
                ticket.resno = ticket.generate_reservation_number()
                ticket.tickets.append(ticket)

                with open("Ticket1.dat", "wb") as file:
                    pickle.dump(ticket.tickets, file)

                with open("Train1.dat", "wb") as file:
                    pickle.dump(ticket.trains, file)

                pdf_path = ticket.generate_receipt(selected_train)
                ticket.send_email(pdf_path)
                ticket.send_sms(selected_train)

                return f"RESERVATION SUCCESSFUL. YOUR RESERVATION NUMBER IS {ticket.resno}"

        if not found:
            return "INVALID TRAIN NUMBER!"

    return render_template('reserve.html')

if __name__ == '__main__':
    app.run(debug=True)