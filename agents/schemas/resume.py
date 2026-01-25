from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import date

# ========== Basics Section ==========
class LocationSchema(BaseModel):
    address: Optional[str] = Field(None, description="Full street address")
    postalCode: Optional[str] = Field(None, description="Postal/ZIP code")
    city: Optional[str] = Field(None, description="City name")
    countryCode: Optional[str] = Field(None, description="Country code (e.g., US, BR)")
    region: Optional[str] = Field(None, description="State/Province/Region")

class ProfileSchema(BaseModel):
    network: Optional[str] = Field(None, description="Social network name")
    username: Optional[str] = Field(None, description="Username/profile ID")
    url: Optional[HttpUrl] = Field(None, description="Profile URL")

class BasicsSchema(BaseModel):
    name: str = Field(..., description="Full name")
    label: Optional[str] = Field(None, description="Professional label/headline")
    image: Optional[str] = Field(None, description="URL to profile image")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    url: Optional[HttpUrl] = Field(None, description="Personal website/portfolio")
    summary: Optional[str] = Field(None, description="Professional summary")
    location: Optional[LocationSchema] = Field(None, description="Location information")
    profiles: Optional[List[ProfileSchema]] = Field(None, description="Social profiles")

# ========== Work Experience ==========
class WorkSchema(BaseModel):
    name: str = Field(..., description="Company/organization name")
    position: str = Field(..., description="Job title")
    url: Optional[HttpUrl] = Field(None, description="Company website")
    startDate: date = Field(..., description="Start date (YYYY-MM-DD)")
    endDate: Optional[date] = Field(None, description="End date (YYYY-MM-DD) or empty for current")
    summary: Optional[str] = Field(None, description="Role description")
    highlights: Optional[List[str]] = Field(None, description="Key achievements")

# ========== Volunteer Experience ==========
class VolunteerSchema(BaseModel):
    organization: str = Field(..., description="Organization name")
    position: str = Field(..., description="Volunteer role")
    url: Optional[HttpUrl] = Field(None, description="Organization website")
    startDate: date = Field(..., description="Start date")
    endDate: Optional[date] = Field(None, description="End date")
    summary: Optional[str] = Field(None, description="Volunteer work description")
    highlights: Optional[List[str]] = Field(None, description="Notable contributions")

# ========== Education ==========
class EducationSchema(BaseModel):
    institution: str = Field(..., description="School/university name")
    url: Optional[HttpUrl] = Field(None, description="Institution website")
    area: Optional[str] = Field(None, description="Field of study")
    studyType: Optional[str] = Field(None, description="Degree type (Bachelor, Master, etc.)")
    startDate: date = Field(..., description="Start date")
    endDate: Optional[date] = Field(None, description="End date")
    score: Optional[str] = Field(None, description="GPA/Score")
    courses: Optional[List[str]] = Field(None, description="Relevant courses")

# ========== Awards ==========
class AwardSchema(BaseModel):
    title: str = Field(..., description="Award name")
    award_date: date = Field(..., description="Award date")
    awarder: Optional[str] = Field(None, description="Awarding organization")
    summary: Optional[str] = Field(None, description="Award description")

# ========== Certificates ==========
class CertificateSchema(BaseModel):
    name: str = Field(..., description="Certificate name")
    certification_date: date = Field(..., description="Issue date")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    url: Optional[HttpUrl] = Field(None, description="Certificate URL")

# ========== Publications ==========
class PublicationSchema(BaseModel):
    name: str = Field(..., description="Publication title")
    publisher: Optional[str] = Field(None, description="Publisher name")
    releaseDate: date = Field(..., description="Release date")
    url: Optional[HttpUrl] = Field(None, description="Publication URL")
    summary: Optional[str] = Field(None, description="Abstract/summary")

# ========== Skills ==========
class SkillSchema(BaseModel):
    name: str = Field(..., description="Skill category/name")
    level: Optional[str] = Field(None, description="Proficiency level")
    keywords: Optional[List[str]] = Field(None, description="Specific technologies/tools")

# ========== Languages ==========
class LanguageSchema(BaseModel):
    language: str = Field(..., description="Language name")
    fluency: Optional[str] = Field(None, description="Fluency level")

# ========== Interests ==========
class InterestSchema(BaseModel):
    name: str = Field(..., description="Interest category")
    keywords: Optional[List[str]] = Field(None, description="Specific interests")

# ========== References ==========
class ReferenceSchema(BaseModel):
    name: str = Field(..., description="Reference name")
    reference: Optional[str] = Field(None, description="Reference statement")

# ========== Projects ==========
class ProjectSchema(BaseModel):
    name: str = Field(..., description="Project name")
    startDate: date = Field(..., description="Start date")
    endDate: Optional[date] = Field(None, description="End date")
    description: Optional[str] = Field(None, description="Project description")
    highlights: Optional[List[str]] = Field(None, description="Key achievements")
    url: Optional[HttpUrl] = Field(None, description="Project URL")

# ========== Main Resume Schema ==========
class ResumeSchema(BaseModel):
    basics: BasicsSchema = Field(..., description="Basic personal information")
    work: Optional[List[WorkSchema]] = Field(None, description="Work experience")
    volunteer: Optional[List[VolunteerSchema]] = Field(None, description="Volunteer experience")
    education: Optional[List[EducationSchema]] = Field(None, description="Education history")
    awards: Optional[List[AwardSchema]] = Field(None, description="Awards received")
    certificates: Optional[List[CertificateSchema]] = Field(None, description="Certifications")
    publications: Optional[List[PublicationSchema]] = Field(None, description="Publications")
    skills: Optional[List[SkillSchema]] = Field(None, description="Skills list")
    languages: Optional[List[LanguageSchema]] = Field(None, description="Language proficiencies")
    interests: Optional[List[InterestSchema]] = Field(None, description="Personal interests")
    references: Optional[List[ReferenceSchema]] = Field(None, description="Professional references")
    projects: Optional[List[ProjectSchema]] = Field(None, description="Projects portfolio")