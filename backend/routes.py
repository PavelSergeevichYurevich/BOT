from datetime import datetime, timedelta, timezone
import os
from typing import Annotated
from fastapi import HTTPException, Request, Response, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from pytube import Search, YouTube
import requests
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter
from backend.token_classes import TokenData
from classes import Connect
from schemas import UserCheckSchema, UserCreateSchema, UserSearchSchema, TrackOutSchema
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

SECRET_KEY = "60dad50dcf49cdb04ff89b51a6c5b3abcb6eeba1a628b96b1f57c06a838d3383"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
music_parser_router = APIRouter()
templates = Jinja2Templates(directory="templates")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    connect = Connect('database.db')
    user = connect.get_user_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@music_parser_router.get('/')
def index(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@music_parser_router.get('/login')
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name='login.html')

@music_parser_router.get('/register')
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name='register.html')

@music_parser_router.get('/search_page/{username}')
def main_page(request: Request, username: str):
    context:dict = {'username': username}
    return templates.TemplateResponse("search_page.html", {"request": request, "context": context})

@music_parser_router.get('/tracks/{username}')
def get_tracks_web(request: Request, username: str):
    connect = Connect('database.db')
    user_id = connect.get_user_username(username)[0]
    tracks = connect.get_tracks(user_id)
    context:dict = {'username': username, 'search_requests': tracks}
    return templates.TemplateResponse("search_page.html", {"request": request, "context": context})
    

@music_parser_router.post('/tracks/')
def get_tracks(request: Request, user:TrackOutSchema):
    connect = Connect('database.db')
    if user.telegram_id:
        user_id = connect.get_user_telegram_id(user.telegram_id)[0]
        tracks = connect.get_tracks(user_id)
        return tracks
    if user.username:
        username = user.username
        return RedirectResponse(url=f"/tracks/{username}", status_code=status.HTTP_302_FOUND)
        
@music_parser_router.post("/check/")
def check_us(request:Request, checking_user: UserCheckSchema):
    connect = Connect('database.db')
    users:list = connect.get_all()
    for user in users:
        if (user[1] == checking_user.username) and verify_password(checking_user.password, user[2]):
            username = user[1]
            return RedirectResponse(url=f"/search_page/{username}", status_code=status.HTTP_302_FOUND)
    else:
        return 'Такого пользователя нет. Зарегистрируйтесь.'

@music_parser_router.post('/register')
def register(request: Request, user: UserCreateSchema, response: Response):
        connect = Connect('database.db')
        if (not user.telegram_id):
            if not connect.get_user_username(username=user.username):
                password = get_password_hash(user.password)
                connect.insert(username = user.username, password = password, telegram_id = user.telegram_id)
                response.status_code = status.HTTP_201_CREATED
                return RedirectResponse(url=f"/search_page/{user.username}", status_code=status.HTTP_302_FOUND)
            else:
                response.status_code = status.HTTP_401_UNAUTHORIZED
                return response
        else:
            if connect.get_user_telegram_id(user.telegram_id):
                response.status_code = status.HTTP_401_UNAUTHORIZED
                return response
            else:
                if connect.get_user_username(username=user.username):
                    connect.update_user(username = user.username, telegram_id = user.telegram_id)
                    response.status_code = status.HTTP_202_ACCEPTED
                    return response
                else:
                    password = get_password_hash(user.password)
                    connect.insert(username = user.username, password = password, telegram_id = user.telegram_id)
                    response.status_code = status.HTTP_201_CREATED
                    return response
                

@music_parser_router.post('/download')
def download(request: Request, search_info: UserSearchSchema):
    connect = Connect('database.db') 
    search = search_info.search_string
    if search_info.telegram_id:
        user = connect.get_user_telegram_id(search_info.telegram_id)
    elif search_info.username:
        user = connect.get_user_username(search_info.username)
    try:
        if requests.head(search).status_code == 200:
            url = search
    except:
        s = Search(search)
        if len(s.results) > 0:
            url = 'https://www.youtube.com/watch?v=' + s.results[0].video_id
    yt = YouTube(url)
    name_music = yt.title
    connect.insert_search(user[0], user[1], url, name_music)
    video = yt.streams.filter(only_audio=True).first() 
    output_path = f'media/{user[1]}'
    if os.path.isdir(output_path):
        pass
    else:
        os.makedirs(output_path)
    downloaded_file = video.download(output_path=output_path) 
    base, ext = os.path.splitext(downloaded_file) 
    new_file = base + '.mp3' 
    os.rename(downloaded_file, new_file)
    return FileResponse(path=new_file, media_type="audio", filename=new_file)
        
