from pydantic import BaseModel
from pydantic import ConfigDict
from app.core.case import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
