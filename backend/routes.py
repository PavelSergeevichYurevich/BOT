import os
from fastapi import Request, Response, status
from fastapi.responses import FileResponse
from pytube import Search, YouTube
import requests
from fastapi import APIRouter
from classes import Connect
from schemas import UserCheckSchema, UserCreateSchema, UserSearchSchema, TrackOutSchema
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

music_parser_router = APIRouter()
templates = Jinja2Templates(directory="templates")

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
        if (user[1] == checking_user.username) and (user[2] == checking_user.password):
            username = user[1]
            return RedirectResponse(url=f"/search_page/{username}", status_code=status.HTTP_302_FOUND)
    else:
        return 'Такого пользователя нет. Зарегистрируйтесь.'

@music_parser_router.post('/register')
def register(request: Request, user: UserCreateSchema, response: Response):
        connect = Connect('database.db')
        if (not user.telegram_id):
            if not connect.get_user_username(username=user.username):
                connect.insert(username = user.username, password = user.password, telegram_id = user.telegram_id)
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
                    connect.insert(username = user.username, password = user.password, telegram_id = user.telegram_id)
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
        
