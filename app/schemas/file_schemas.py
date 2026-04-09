from pydantic import BaseModel
from datetime import datetime

class FileReturnResponse(BaseModel):

    id : int
    file_type_name : str
    file_url : str
    added_by : str
    added_for : str
    created_at : datetime


    model_config = {
        "from_attributes": True
    }