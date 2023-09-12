from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel
import threading
import os
import uvicorn
import json

from engine import *

current_directory = os.getcwd()

app = FastAPI()
scheduler = BackgroundScheduler()
is_work_service_running = False
service_running = False
thread = threading.Thread(target=scrap)

setting = {}
with open(os.path.join(current_directory, "settings", "settings.json")) as file:
    setting = json.load(file)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def work_service():
    print("Running work service...")
    scrap()


def start_service_background():
    thread.start()


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(work_service, "cron", hour=2, minute=0, timezone="CST6CDT")
    is_work_service_running = True
    scheduler.start()


@app.post("/asinupload")
async def upload_file(file: UploadFile = File(...)):
    valid_extensions = ["csv", "xlsx"]
    file_extension = file.filename.split(".")[-1]
    if file_extension not in valid_extensions:
        return JSONResponse(
            {"error": "Invalid file format. Only CSV and XLSX files are allowed."},
            status_code=400,
        )
    file_path = os.path.join("settings", "asins.csv")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return JSONResponse({"success": "true"})


@app.post("/download")
async def download_file(file_request: dict):
    file_name = file_request["filename"]
    file_path = os.path.join(current_directory, "results", file_name)
    return FileResponse(file_path, filename=file_name)


@app.post("/start-scheduling-service")
async def start_work_service():
    global is_work_service_running
    if not is_work_service_running:
        is_work_service_running = True
        scheduler.shutdown()
        scheduler.start()
    return {"message": "Work service started"}


@app.post("/stop-scheduling-service")
async def stop_work_service():
    global is_work_service_running
    if is_work_service_running:
        is_work_service_running = False
        scheduler.shutdown()
    return {"message": "Work service stopped"}


@app.post("/start-scraping")
async def start_service():
    global service_running
    if not service_running:
        service_running = True
        thread.start()
        return {"success": "1", "message": "Service started successfully"}
    else:
        return {"success": "2", "message": "Service is already running"}


@app.post("/stop-scraping")
async def start_service():
    global service_running
    if service_running:
        service_running = False
        thread.join()
        return {"success": "1", "message": "Service stopped successfully"}
    else:
        return {"success": "2", "message": "Service is already stoppped"}


@app.post("/get-file-info")
async def get_file_info():
    asin_files = []
    filter_files = []
    asin_path = os.path.join(current_directory, "results", "asin")
    asin_names = os.listdir(asin_path)
    for asin_name in asin_names:
        asin_files.append(asin_name)

    filter_path = os.path.join(current_directory, "results", "filter")
    filter_names = os.listdir(asin_path)
    for filter_name in filter_names:
        filter_files.append(filter_name)

    return {"asin": asin_files, "filter": filter_files}


@app.post("/get-setting")
async def get_setting():
    return {"data": setting}


@app.post("/save-filter")
async def save_scheduling():
    return {"success": True}


class Schedule(BaseModel):
    hour: int
    minute: int


@app.post("/save-schedule")
def save_filter(data: Schedule):
    hour = data.hour
    minute = data.minute

    setting["schedule"]["hour"] = hour
    setting["schedule"]["minute"] = minute

    with open(
        os.path.join(current_directory, "settings", "settings.json"),
        "w",
    ) as file:
        json.dump(setting, file)

    return {"message": "Data received successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
