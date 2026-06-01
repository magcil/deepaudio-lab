from pydantic import BaseModel, Field


class DeployRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="Name for the deployment bundle zip file.")
