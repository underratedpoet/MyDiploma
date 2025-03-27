from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/references")
async def home(request: Request):
    return templates.TemplateResponse("references.html", {"request": request})