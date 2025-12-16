from datetime import datetime
from pathlib import Path
from fastapi import Header, HTTPException, UploadFile
import secrets, shutil

def load_data(object_category, user_id=None):
    """Load data from JSON file. For reports, loads user-specific file if user_id provided."""
    if object_category == "reports" and user_id is not None:
        # Load user-specific report file
        data_file = f"database/reports/{user_id}.json"
    else:
        data_file = f"database/{object_category}.json"
    
    if not Path(data_file).exists():
        if object_category != "reports":
            if files := sorted(Path("database").glob(f"{object_category}_*.json"), reverse=True):
                data_file = str(files[0])
            else:
                return {}
        else:
            return {}
        
    import json
    with open(data_file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data, object_category="reports", user_id=None):
    """Save data to JSON file. For reports, saves to user-specific file if user_id provided."""
    import json
    
    if object_category == "reports" and user_id is not None:
        # Save to user-specific report file
        data_file = f"database/reports/{user_id}.json"
    else:
        data_file = f"database/{object_category}.json"
    
    Path(data_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def save_file(f: UploadFile, path: str):
    config = load_data("config")
    config["last_file_id"] = config["last_file_id"] + 1
    new_file_id = config["last_file_id"]
    
    folder = Path(path).parent
    ext = f.filename.split(".")[-1]
    new_path = Path(folder).joinpath(f"{new_file_id}.{ext}")
    new_path = new_path.as_posix()

    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(new_path, "wb") as out_file:
        out_file.write(await f.read())
    
    save_data(config, "config")
    return {"id": new_file_id, "name": f.filename, "type": f.content_type, "path": str(new_path)}

async def save_profile_image(profile_image: UploadFile, user_id: int):    
    folder = "database/files/users/"
    ext = profile_image.filename.split(".")[-1]
    new_path = Path(folder).joinpath(f"{user_id}.{ext}")
    new_path = new_path.as_posix()

    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(new_path, "wb") as out_file:
        out_file.write(await profile_image.read())
    
    save_data(config, "config")
    return {"name": profile_image.filename, "type": profile_image.content_type, "path": str(new_path)}

async def delete_files(files, target_files):
    undeleted_files_list = []
    for f in files:
        if f.get("id") in target_files:
            if Path(f.get("path")).exists():
                Path(f.get("path")).unlink()
        else:
            undeleted_files_list.append(f)
    return undeleted_files_list

async def delete_dir(path):
    if Path(path).exists():
        shutil.rmtree(path)
        return {"ok": True, "message": "Directory successfully deleted"}
    else:
        return {"ok": False, "message": "Directory not found"}

def verify_api_key(x_api_key: str = Header(...)):
    if user := next(
        (
            u
            for k, u in load_data("users").items()
            if u["api_key"] == x_api_key
        ),
        {},
    ):
        return user
    else:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
def verify_authentication(x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    if session := load_data("sessions").get(x_api_key):
        return session
    else:
        raise HTTPException(status_code=401, detail="User not authenticated")

def verify_authentication_approval(x_api_key: str = Header(...)):
    verify_authentication(x_api_key)
    session = load_data("sessions").get(x_api_key)
    if not session["approved"]:
        raise HTTPException(status_code=401, detail="Authentication not yet verified. Please verify your authentication code.")
    return session

def is_admin(x_api_key: str = Header(...)):
    session = verify_authentication_approval(x_api_key)
    user = load_data("users")[str(session.get("user_id"))]
    return user.get("role") == "Administrator"

def only_admin(x_api_key: str = Header(...)):
    if not is_admin(x_api_key):
        raise HTTPException(status_code=401, detail="Vous n'etes pas autorisé à éffectuer cette opération")

def generate_api_key():
    return secrets.token_hex(24).upper()

def generate_verification_code():
    from numpy import random
    return "".join([str(a) for a in random.randint(9, size=5)])

def now(type: str = "datetime", d_format: str = "%d-%m-%Y %H:%M:%S"):
    # Default : datetime
    if type == "date":
        d_format = "%d-%m-%Y"
    elif type == "time":
        d_format = "%H:%M:%S"
    return datetime.now().strftime(d_format)

from datetime import datetime

def validate_reports():
    user_ids = [int(uid) for uid in load_data("users").keys()]
    for user_id in user_ids:
        user_reports = load_data("reports", user_id=user_id)
        today = datetime.now().date()

        for day_str, report in user_reports.get("items", {}).items():

            try:
                report_date = datetime.strptime(day_str, "%d-%m-%Y").date()
            except ValueError:
                continue

            if (today - report_date).days >= 30 and not report.get("validated"):
                report["validated"] = True
                report["validated_by"] = 0

        save_data(user_reports, "reports", user_id=user_id)


    

# -------------------------------------------------
# Automatic mails
# -------------------------------------------------
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
config = load_data("config")
def send_verification_code(recipient_email, code):
    # SMTP server details
    smtp_server, port, sender_email, password = config.get("smtp_server"), config.get("tls_port"), config.get("admin_email"), config.get("admin_email_password")
    # Establish connection
    server = smtplib.SMTP(smtp_server, port)
    # server.connect()
    server.starttls() # Enable encryption
    server.login(sender_email, password)
    # Create email content
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Validation Code"
    # Add plain text and HTML content
    html_content = f"""\
    <html>
    <body>
        <h1>Validation Code</h1>
        <p>This is your verification code: <b>{code}</b>. Don't share it to anyone.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    # Send the email
    server.sendmail(sender_email, recipient_email, msg.as_string())
    # Close the connection
    server.quit()