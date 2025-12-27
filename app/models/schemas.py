from pydantic import BaseModel

class AnswerSchema(BaseModel):
    problem_id: str
    solving: str

    class Config:
        from_attributes=True
