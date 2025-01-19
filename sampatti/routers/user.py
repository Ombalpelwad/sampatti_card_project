import os
import tempfile
from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import requests
from .. import schemas, models
from ..database import get_db
from sqlalchemy.orm import Session
from ..controllers import userControllers
from ..controllers import employment_contract_gen
from datetime import datetime, timedelta
from ..controllers import whatsapp_message, talk_to_agent_excel_file
import whisper
from ..controllers import utility_functions, salary_report_gen


router = APIRouter(
    prefix="/user",
    tags=['users']
)


model = whisper.load_model("base")
current_date = datetime.now().date()
first_day_of_current_month = datetime.now().replace(day=1)
last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
previous_month = last_day_of_previous_month.strftime("%B")
current_year = datetime.now().year


@router.get("/download_salary_slip")
def download_worker_salary_slip(workerNumber : int, month : str, year : int, db : Session = Depends(get_db)):
    return userControllers.download_worker_salary_slip(workerNumber, month, year, db)

@router.post("/employer/create")
def create_employer(request : schemas.Employer, db : Session = Depends(get_db)):
    return userControllers.create_employer(request, db)

@router.post('/domestic_worker/create')
def create_domestic_worker(request : schemas.Domestic_Worker, db: Session = Depends(get_db)):
    return userControllers.create_domestic_worker(request, db)

@router.post('/domestic_worker/create/account_number')
def create_worker_account_number(request : schemas.Domestic_Worker, db: Session = Depends(get_db)):
    return userControllers.create_worker_account_number(request,db)

@router.post('/assign_vendor_id')
def assign_vendor_id(workerNumber : int, vendorId : str, db : Session = Depends(get_db)):
    return userControllers.assign_vendor_id(workerNumber, vendorId, db)

@router.post('/create_relation')
def create_relation(request : schemas.Worker_Employer, db : Session = Depends(get_db)):
    return userControllers.create_relation(request, db)

@router.delete('/delete_relation')
def delete_relation(workerNumber : int, employerNumber : int, db : Session = Depends(get_db)):
    return userControllers.delete_relation(workerNumber, employerNumber,db)

@router.get("/check_existence")
def check_existence(employerNumber : int, workerNumber : int, db : Session = Depends(get_db)):
    return userControllers.check_existence(employerNumber, workerNumber,db)

@router.get("/check_name_matching")
def check_names(pan_name : str, vpa_name : str):
    return userControllers.check_names(pan_name, vpa_name)

@router.get("/check_worker")
def check_worker(workerNumber : int, db : Session = Depends(get_db)):
    return userControllers.check_worker(workerNumber, db)

@router.get("/get_number")
def number_regex(numberString : str):
    return userControllers.number_regex(numberString)

@router.get("/extract_salary")
def extract_salary(salary_amount : str):
    return userControllers.extract_salary(salary_amount)

@router.post('/talk_to_agent/create')
def create_talk_to_agent_employer(request : schemas.talkToAgent, db : Session = Depends(get_db)):
    return userControllers.create_talk_to_agent_employer(request, db)

@router.post('/explain_worker/create')
def explain_worker(employerNumber : int, workerNumber : int , db : Session = Depends(get_db)):
    return userControllers.explain_worker(db, workerNumber, employerNumber)

@router.post('/message_log/create')
def create_message_log(request : schemas.Message_log_Schema, db : Session = Depends(get_db)):
    return userControllers.create_message_log(request, db)

@router.put('/domestic_worker/update')
def update_worker(oldNumber : int, newNumber: int, db : Session = Depends(get_db)):
    return userControllers.update_worker(oldNumber,newNumber, db)

@router.post("/salary")
def insert_salary(request : schemas.Salary, db : Session = Depends(get_db)):
    return userControllers.insert_salary(request, db)

@router.post("/send_worker_salary_slips")
def send_worker_salary_slips(db : Session = Depends(get_db)):
    return userControllers.send_worker_salary_slips(db)

@router.put("/update_salary")
def update_worker_salary(employer_id : str, worker_id : str, salary : int, db : Session = Depends(get_db)):
    return userControllers.update_worker_salary(employer_id, worker_id, salary, db)

@router.post("/contract")
def contract_generation(request : schemas.Contract, db : Session = Depends(get_db)):

    employment_contract_gen.create_employment_record_pdf(request, db)
    field = db.query(models.worker_employer).filter(models.worker_employer.c.worker_number == request.workerNumber, models.worker_employer.c.employer_number == request.employerNumber).first()

    static_pdf_path = os.path.join(os.getcwd(), 'contracts', f"{field.id}_ER.pdf")

    return FileResponse(static_pdf_path, media_type='application/pdf', filename=f"{request.workerNumber}_ER_{request.employerNumber}.pdf")


@router.delete("/delete_demo_contract")
def delete_demo_contract(workerNumber : int, employerNumber : int, db: Session = Depends(get_db)):

    field = db.query(models.worker_employer).filter(models.worker_employer.c.worker_number == workerNumber, models.worker_employer.c.employer_number == employerNumber).first()

    static_pdf_path = os.path.join(os.getcwd(), 'contracts', f"{field.id}_ER.pdf")
    if(static_pdf_path):
        os.remove(static_pdf_path)
        return {
            "MESSAGE" : "File deleted Successfully."
        }

    else:
        return {
            "MESSAGE" : "No such file exist."
        }
    
    
@router.post("/generate_contract")
def generate_mediaId(workerNumber: int, employerNumber: int, db : Session = Depends(get_db)):

    field = db.query(models.worker_employer).filter(models.worker_employer.c.worker_number == workerNumber, models.worker_employer.c.employer_number == employerNumber).first()

    path = f"{field.id}_ER.pdf"
    folder = 'contracts'
    return whatsapp_message.generate_mediaId(path, folder)


@router.get("/send_employer_invoice")
def send_employer_invoice(employerNumber : int, orderId : str, db : Session = Depends(get_db)):
    return userControllers.send_employer_invoice(employerNumber, orderId, db)
    
@router.get('/salary_payment_reminder')
def salary_payment_reminder(db : Session = Depends(get_db)):
    return userControllers.salary_payment_reminder(db)

@router.get("/send_greetings")
def send_greetings_message(db : Session = Depends(get_db)):
    return userControllers.send_greetings(db)

@router.get('/generate_talk_to_agent_sheet')
def generate_sheet():
    return talk_to_agent_excel_file.upload_data_to_google_sheets()

@router.get('/copy_employer_message')
def copy_employer_message(db : Session = Depends(get_db)):
    return userControllers.copy_employer_message(db)

@router.post("/salary_details")
def create_salary_details(employerNumber : int, orderId : str, db : Session = Depends(get_db)):
    return userControllers.update_salary_details(employerNumber, orderId, db)

@router.post("/cash_advance_entry/create")
def create_cash_advance_entry(employerNumber : int, employer_id : str, worker_id : str, crrCashAdvance : int, Repayment_Monthly : int, Repayment_Start_Month : str, Repayment_Start_Year : int, Bonus : int, Attendance : int, db : Session = Depends(get_db)):
    return userControllers.create_cash_advance_entry(employerNumber, employer_id, worker_id, crrCashAdvance, Repayment_Monthly, Repayment_Start_Month, Repayment_Start_Year, Bonus, Attendance, db)


@router.post("/cash_advance_record/create")
def cash_advance_record(employerNumber : int, workerNumber : int, cashAdvance : int, bonus : int, db : Session = Depends(get_db)):
    return userControllers.cash_advance_record(employerNumber, workerNumber, cashAdvance, bonus, db)


@router.get("/existing_advance_entry")
def check_existing_cash_advance_entry(employerNumber : int, workerNumber : int, db : Session = Depends(get_db)):
    return userControllers.check_existing_cash_advance_entry(employerNumber, workerNumber, db)

@router.get("/extract_date")
def extract_date(date_str : str):
    return utility_functions.extract_date(date_str)

@router.post("/send_audio_message")
def send_audio_message(employer_id : str, worker_id : str, user_language : str, employerNumber : int, db : Session = Depends(get_db)):
    return userControllers.send_audio_message(employer_id, worker_id, user_language, employerNumber, db)

@router.get("/get_all_workers")
def find_all_workers(employerNumber : int, db : Session = Depends(get_db)):
    return userControllers.find_all_workers(employerNumber, db)

@router.post('/process_audio')
async def process_audio(file_url: str, employerNumber : int, workerName :str, db : Session = Depends(get_db)):
    return await userControllers.process_audio(file_url, employerNumber, workerName, db)

@router.post('/extract_name')
async def extract_name(file_url: str, employerNumber : int):
    return await userControllers.extract_name(file_url, employerNumber,)

@router.get("/get_next_question")
def get_next_question(workerId : str, questionId : int, answer : str, surveyId : int, db : Session = Depends(get_db)):
    return utility_functions.get_next_question(workerId, questionId, answer, surveyId, db)

@router.get("/get_translated_text")
async def get_transalated_text(file_url: str):
    return await userControllers.get_transalated_text(file_url)

@router.get("/send_question_audio")
def send_question_audio(employerNumber : int, question_id : int, user_language : str, db : Session = Depends(get_db)):
    return userControllers.send_question_audio(employerNumber, question_id, user_language, db)


@router.get("/send_audio")
def send_audio( sample_output: str, language: str, employerNumber: int):

    output_directory = "audio_files"
    return utility_functions.send_audio(output_directory, sample_output, language, employerNumber)

@router.get("/send_ogg")
def send_ogg(employerNumber : int):
    return utility_functions.send_ogg(employerNumber)

