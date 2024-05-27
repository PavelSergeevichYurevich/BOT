from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    username:str
    password:str
    telegram_id: int| None = None
    
class UserCheckSchema(BaseModel):
    username:str
    password:str

class UserSearchSchema(BaseModel):
    telegram_id: int | None = None
    username: str | None = None
    search_string: str
    
class TrackOutSchema(BaseModel):
    telegram_id: int | None = None
    username: str | None = None