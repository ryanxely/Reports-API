from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from typing import List

from api.models import *
from api.utilities import *

router = APIRouter()

@router.get("/")
def root():
    return {"ok": True, "message": "Welcome to the Report API"}

# -------------------------------------------
# Login Operations
# -------------------------------------------
@router.post("/auth/login")
async def login(credentials: Credentials):
    credentials = credentials.dict()
    p, v = tuple(credentials.values())
    users = load_data("users")
    user = next((u for k, u in users.items() if u.get(p) == v), {})
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non existant")
    sessions = load_data("sessions")
    if sessions.get(user.get("api_key"), {}).get("approved"):
        old_session_info = logout(sessions.get(user.get("api_key"))).get("session_info")
        result = await login(Credentials(**old_session_info.get("credentials")))
        return {"ok": True, "api_key": result.get("api_key"), "message": "Your previous session has been reinitialised. Please grant us the new verification code we sent you", "email": user.get("email")}
    session = {"credentials": credentials, "user_id": user.get("id"), "code": generate_verification_code(), "approved": False, "start_time": "", "api_key": user.get("api_key")} 
    sessions[user.get("api_key")] = session
    save_data(sessions, "sessions")
    send_verification_code(user.get("email"), session.get("code"))
    return {"ok": True, "api_key": user.get("api_key"), "message": "We sent you a verification code on your email address", "email": user.get("email")}


@router.post("/auth/login/verify")
async def verify_login(code: str, session: dict = Depends(verify_authentication)):
    api_key = session.get("api_key")
    sessions = load_data("sessions")
    if sessions.get(api_key).get("approved"):
        old_session_info = logout(sessions.get(api_key)).get("session_info")
        result = await login(Credentials(**old_session_info.get("credentials")))
        return {"ok": True, "api_key": result.get("api_key"), "message": "Your previous session has been reinitialised. Please grant us the new verification code we sent you"}
    elif not sessions.get(api_key).get("code"):
        raise HTTPException(status_code=401, detail="Code de verification expiré. Veuillez demander un nouveau code")
    elif sessions.get(api_key).get("code") != code:
        raise HTTPException(status_code=401, detail="Code de verification incorrect")
    else:
        sessions[api_key]["approved"] = True
        sessions[api_key]["start_time"] = now()
        save_data(sessions, "sessions")
        return {"ok": True, "message": "Successfully Authenticated"}
    
@router.get("/auth/logout")
def logout(session: dict = Depends(verify_authentication)):
    sessions = load_data("sessions")
    session_info = sessions.pop(session.get("api_key"))
    save_data(sessions, "sessions")

    users = load_data("users")
    users[str(session_info.get("user_id"))]["api_key"] = generate_api_key()
    save_data(users, "users")

    return {"ok": True, "message": "Vous avez été déconnecté avec succès", "session_info": session_info}

# -------------------------------------------
# CRUD Operations on Users
# -------------------------------------------

@router.post("/users/add")
async def add_user(user_in: UserIn, authorized: bool = Depends(only_admin)):
    tracker = load_data("tracker")
    tracker["last_user_id"] += 1
    save_data(tracker, "tracker")

    users = load_data("users")
    user_in = user_in.dict()
    user_in["fullname"] = user_in["fullname"] or user_in["username"]
    new_user = {"id": tracker["last_user_id"]} | user_in.dict() | {"api_key": generate_api_key(), "created_at": now(), "last_edit_at": ""} 
    users[str(new_user.get("id"))] = new_user
    save_data(users, "users")

    return {"ok": True, "message": "User added successfully", "user": new_user}

@router.get("/users")
def get_users(authorized: bool = Depends(only_admin)):
    users = load_data("users")
    return {"ok": True, "users": users}

@router.get("/profile", response_model=dict)
def get_user_profile(session: dict = Depends(verify_authentication_approval)):
    users = load_data("users")
    user_profile = users.get(str(session.get("user_id")))
    return {"ok": True, "user": user_profile}

@router.patch("/profile/edit")
async def edit_profile(username: Optional[str] = Form(""), fullname: Optional[str] = Form(""), phone: Optional[str] = Form(""), profile_image: UploadFile = File(None), session: dict = Depends(verify_authentication_approval)):
    """Edit user profile information"""
    users = load_data("users")
    user_id = str(session.get("user_id"))
    user = users.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields only if provided
    if username:
        # Check if username is already taken by another user
        if any(u.get("username") == username and k != user_id for k, u in users.items()):
            raise HTTPException(status_code=400, detail="Username already taken")
        user["username"] = username
    
    if fullname:
        user["fullname"] = fullname
    
    if phone:
        user["phone"] = phone

    if profile_image:
        user["profile_image"] = await save_profile_image(profile_image, user_id)
    
    user["last_edit_at"] = now()
    users[user_id] = user
    save_data(users, "users")
    
    return {"ok": True, "message": "Profile updated successfully", "user": user}


# -------------------------------------------
# CRUD Operations on Reports
# -------------------------------------------
# Test 
@router.post("/post/add")
async def add_post(text: str = Form(""), files: List[UploadFile] = File([])):
    tracker = load_data("tracker")
    new_post_id = tracker.get("last_post_id")+1
    tracker["last_post_id"] = new_post_id
    save_data(tracker, "tracker")

    posts = load_data("posts")
    
    files_info = []
    for f in files:
        filename = f.filename
        files_info.append(await save_file(f, f"database/files/posts/{new_post_id}/{filename}"))

    new_post = {"id": new_post_id, "content": {"text": text, "files": files_info}, "day": now("date"), "time": now("time")}
    posts.append(new_post)

    save_data(posts, "posts")
    return {"ok": True, "message": "Post added successfully", "post": new_post}



@router.post("/reports/add")
async def add_report(title: str = Form(...), text: Optional[str] = Form(""), date: str = Form(""), extra_fields: Optional[str] = Form(""), files: Optional[List[UploadFile]] = File([]), session: dict = Depends(verify_authentication_approval)):
    print("\n>> Adding report...\n>> Received data:", title, text, files, sep=" - ")
    tracker = load_data("tracker")
    new_record_id = tracker.get("last_record_id")+1
    tracker["last_record_id"] = new_record_id
    save_data(tracker, "tracker")
    
    user_id = session.get("user_id")
    
    # Load user's reports
    reports = load_data("reports", user_id)

    try:
        current_day = datetime.strptime(date, "%d-%m-%Y").strftime("%d-%m-%Y")
    except Exception:
        try:
            current_day = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
        except Exception:
            current_day = now("date")
    
    # Initialize user reports structure if empty
    if not reports:
        reports = {"items": {}, "user_id": user_id}
    
    day_report = reports.get("items", {}).get(current_day, {"records": [], "day": current_day, "validated": False, "validated_by": -1})
    
    files_info = []
    for f in files:
        filename = f.filename
        files_info.append(await save_file(f, f"database/files/reports/{new_record_id}/{filename}"))

    # Parse extra_fields from JSON string
    parsed_extra_fields = []
    if extra_fields:
        try:
            import json
            extra_data = json.loads(extra_fields)
            if isinstance(extra_data, list):
                parsed_extra_fields = extra_data
            elif isinstance(extra_data, dict):
                parsed_extra_fields = [{"key": k, "value": v} for k, v in extra_data.items()]
        except json.JSONDecodeError:
            pass

    report_content = {"text": text, "files": files_info, "extra_fields": parsed_extra_fields}
    new_report = {"id": new_record_id, "title": title, "content": report_content, "user_id": user_id, "day": current_day, "created_at": now("time"), "last_edit_at": ""}
    day_report["records"].append(new_report)
    reports["items"][current_day] = day_report
    
    # Save to user-specific file
    save_data(reports, "reports", user_id)
    return {"ok": True, "message": "Report added successfully", "report": new_report}

@router.get("/reports")
def get_reports(session: dict = Depends(verify_authentication_approval)):
    # validate_reports()
    user_id = session.get("user_id")
    api_key = session.get("api_key")
    
    if is_admin(api_key):
        # Admins get all reports from all users
        from pathlib import Path
        all_reports = {}
        reports_dir = Path("database/reports")
        
        # Iterate through all user report files
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.json"):
                try:
                    user_file_id = report_file.stem
                    user_reports = load_data("reports", user_file_id)
                    if user_reports:
                        all_reports[user_file_id] = user_reports
                except Exception:
                    pass
        
        return {"ok": True, "reports": all_reports}
    
    # Regular users only get their own reports
    user_reports = load_data("reports", user_id)
    return {"ok": True, "reports": user_reports if user_reports else {}}

@router.get("/reports/single")
def get_single_report(id: int, session: dict = Depends(verify_authentication_approval)):
    """Get a single report by ID."""
    # validate_reports()
    user_id = session.get("user_id")
    api_key = session.get("api_key")
    
    # Admins can view any report
    if is_admin(api_key):
        # Search through all user report files
        from pathlib import Path
        reports_dir = Path("database/reports")
        
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.json"):
                try:
                    user_file_id = report_file.stem
                    user_reports = load_data("reports", user_file_id)
                    for day_report in user_reports.get("items", {}).values():
                        for record in day_report.get("records", []):
                            if record.get("id") == id:
                                return {"ok": True, "report": record}
                except Exception:
                    pass
    else:
        # Regular users can only view their own reports
        user_reports = load_data("reports", user_id)
        for day_report in user_reports.get("items", {}).values():
            for record in day_report.get("records", []):
                if record.get("id") == id:
                    return {"ok": True, "report": record}
    
    raise HTTPException(status_code=404, detail="Report not found")

@router.patch("/reports/edit")
async def edit_report(id: int = Form(...), date: str = Form(...), title: Optional[str] = Form(""), text: Optional[str] = Form(""), extra_fields: Optional[str] = Form(""), files_to_delete: Optional[List[int]] = None, files: Optional[List[UploadFile]] = File([]), session: dict = Depends(verify_authentication_approval)):
    print("\n>> Editing report...\n>> Received data:", id, title, text, files, sep=" - ")
    if files_to_delete is None:
        files_to_delete = []
    user_id = session.get("user_id")
    reports = load_data("reports", user_id)

    if not reports:
        return {"ok": True, "message": "You have no reports"}

    user_reports = reports
    target_report = user_reports.get("items").get(date, {})
    if not target_report:
        return {"ok": False, "message": f"You sent no reports on the {date}"}
    
    if target_report.get("validated"):
        return {"ok": False, "message": "You can't edit this reports anymore"}

    records = target_report.get("records")
    record_index = next((i for i,u in enumerate(records) if u.get("id") == id), -1)
    if record_index == -1:
        raise HTTPException(status_code=401, detail="Invalid report index !")
    

    new_files_info = await delete_files(records[record_index]["content"]["files"], set(files_to_delete))

    for f in files:
        filename = f.filename
        new_files_info.append(await save_file(f, f"database/files/reports/{id}/{filename}"))

    # Parse extra_fields from JSON string if provided
    parsed_extra_fields = records[record_index]["content"].get("extra_fields", [])
    if extra_fields:
        try:
            import json
            extra_data = json.loads(extra_fields)
            if isinstance(extra_data, list):
                parsed_extra_fields = extra_data
            elif isinstance(extra_data, dict):
                parsed_extra_fields = [{"key": k, "value": v} for k, v in extra_data.items()]
        except json.JSONDecodeError:
            pass

    target_report["records"][record_index]["title"] = title or records[record_index]["title"]
    target_report["records"][record_index]["last_edit_at"] = now("time")
    target_report["records"][record_index]["content"]["text"] = text or records[record_index]["content"]["text"]
    target_report["records"][record_index]["content"]["files"] = new_files_info
    target_report["records"][record_index]["content"]["extra_fields"] = parsed_extra_fields

    user_reports["items"][date].update(target_report)

    print("===============After edit, Reports Content===============", user_reports)

    save_data(user_reports, "reports", user_id)
    return {"ok": True, "message": "Record edited successfully", "report": target_report["records"][record_index]}

@router.delete("/reports/delete/{day:path}/{id:path}")
async def delete_report(id: int, day: str, session: dict = Depends(verify_authentication_approval)):
    print("Deleting ", day, "/", id)
    user_id = session.get("user_id")
    reports = load_data("reports", user_id)

    if not reports:
        return {"ok": True, "message": "You have no reports"}
    
    records = reports["items"][day]["records"]
    record_index = next((i for i, u in enumerate(records) if u.get("id") == id), -1)
    
    if record_index == -1:
        raise HTTPException(status_code=401, detail="Invalid report index !")
    print("ndex: ", record_index)

    print("===================================================")
    print("Reports:", reports["items"][day]["records"])
    deleted_record = reports["items"][day]["records"].pop(record_index)
    print("===================================================")
    print("Deleted Record:", deleted_record)
    if deleted_record.get("content").get("files"):
        res = await delete_dir(f"database/files/reports/{id}")
        if not res.get("ok"):
            raise HTTPException(status_code=401, detail = "An error occured while attempting to delete report")
    
    save_data(reports, "reports", user_id)
    return {"ok": True, "message": "Record deleted successfully", "report": deleted_record}

@router.get("/files/{path:path}")
async def get_protected_file(path: str, session: dict = Depends(verify_authentication_approval)):
    full_path = Path("database/files").joinpath(path)

    if ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not Path(full_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(full_path)


# -------------------------------------------
# Admin Operations
# -------------------------------------------

@router.post("/admin/database/reset")
async def reset_database(authorized: bool = Depends(only_admin)):
    """Reset all database files to empty state. Admin only."""
    try:
        import json
        from datetime import datetime
        from pathlib import Path
        
        # Initialize empty data structures
        tracker = load_data("tracker")
        n_tracker = {
            "last_user_id": 0,
            "last_post_id": 0,
            "last_record_id": 0,
            "last_file_id": 0,
        }
        tracker.update(n_tracker)
        # users = {}
        sessions = {}
        posts = []
        
        # Save all reset data
        save_data(tracker, "tracker")
        # save_data(users, "users")
        save_data(sessions, "sessions")
        save_data(posts, "posts")
        
        # Clear all per-user report files
        reports_dir = Path("database/reports")
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.json"):
                try:
                    report_file.unlink()
                except Exception:
                    pass
        
        # Clear file directories
        await delete_dir("database/files/posts")
        await delete_dir("database/files/reports")

        
        return {
            "ok": True,
            "message": "Database has been successfully reset to initial state",
            "timestamp": now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting database: {str(e)}")