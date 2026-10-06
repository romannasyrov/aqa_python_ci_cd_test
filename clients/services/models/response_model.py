from pydantic import BaseModel, ConfigDict, Field


class CreatePostResponse(BaseModel):
    id: int = Field(gt=0)
    title: str
    body: str
    user_id: int = Field(alias="userId", gt=0)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )