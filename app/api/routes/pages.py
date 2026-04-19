"""
OPC Marketplace - 完整交互式前端
供需对接 + 揭榜挂帅 + 智能匹配 + 消息系统
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})
