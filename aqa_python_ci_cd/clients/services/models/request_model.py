from pydantic import BaseModel, ConfigDict, Field


class CreatePostRequest(BaseModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    user_id: int = Field(alias="userId", gt=0)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )
