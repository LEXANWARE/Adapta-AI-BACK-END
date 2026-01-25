from pydantic import BaseModel, Field

class KeyElement(BaseModel):
    element_name: str = Field(..., description="Name of the Key Element")

class VacancyKeyThemes(BaseModel):
    key_tools: list[KeyElement] = Field(..., description="Key Frameworks of Vacancy")
    key_skills: list[KeyElement] = Field(..., description="Key Skills besides the knowledge of Frameworks of Vacancy")
    key_phrases: list[KeyElement] = Field(..., description="Key Phrases of Vacancy")

