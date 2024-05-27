from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from routes import music_parser_router

app = FastAPI(title='My Music Parser')
app.include_router(music_parser_router)
app.mount("/static", StaticFiles(directory=Path(__file__).parent.absolute() / "static"), name="static")


    
HOST = '127.0.0.1'
if __name__ == '__main__':
    print('Starting server')
    uvicorn.run('main:app', port=8000, host=HOST, reload=True)
    print('Server stopped')