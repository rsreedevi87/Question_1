from pydantic import BaseModel

class User(BaseModel):
    first_name: str
    password: str
    email: str
    phone: str
