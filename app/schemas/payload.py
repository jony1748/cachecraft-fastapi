from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PayloadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    list_1: list[str] = Field(min_length=1, max_length=1000)
    list_2: list[str] = Field(min_length=1, max_length=1000)

    @field_validator("list_1", "list_2")
    @classmethod
    def validate_items(cls, values: list[str]) -> list[str]:
        if any(not value for value in values):
            raise ValueError("List items cannot be blank.")
        if any(len(value) > 10000 for value in values):
            raise ValueError("List items cannot exceed 10000 characters.")
        return values

    @model_validator(mode="after")
    def equal_lengths(self):
        if len(self.list_1) != len(self.list_2):
            raise ValueError("Both lists must have the same number of items.")
        return self


class PayloadCreated(BaseModel):
    id: str
    reused: bool


class PayloadRead(BaseModel):
    output: str


class ErrorResponse(BaseModel):
    error: str
    message: str
