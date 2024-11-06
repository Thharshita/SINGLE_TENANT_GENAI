from pydantic import BaseModel
from datetime import datetime


class Name_link(BaseModel):
    element_id:str="https://www.centralbankofindia.co.in/en"
    internal_link:str

class main_link(BaseModel):
    element_id:str="https://www.centralbankofindia.co.in/en"
    

class User(BaseModel):
    Name:str
    email:str
    password:str
    

class Token_Data(BaseModel):
    UUID:str

class Admin(BaseModel):
    Name:str
    email:str
    password:str
