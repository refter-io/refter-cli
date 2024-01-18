from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class RelationType(str, Enum):
    one_to_one = "one-to-one"
    many_to_many = "many-to-many"
    many_to_one = "many-to-one"
    one_to_many = "one-to-many"


class TableConfig(BaseModel):
    disabled: Optional[bool] = False
    deprecated: Optional[bool] = False
    group: Optional[str] = None
    owner: Optional[str] = None


class ValidateError(BaseModel):
    field: str
    column: Optional[str] = None
    message: str
    type: str


class RelationConfig(BaseModel):
    model: str
    column: str
    type: RelationType


class ColumnConfig(BaseModel):
    disabled: Optional[bool] = False
    relations: Optional[List[RelationConfig]] = None
