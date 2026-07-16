"""CV generation domain schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """Planned profile for offline CV generation."""

    slug: str
    full_name: str
    locale: str = "en"
    role_family: str = Field(description="e.g. backend, data, design")
    university: str | None = None
    seniority: str = "mid"


class ExperienceEntry(BaseModel):
    title: str
    company: str
    location: str | None = None
    start: str
    end: str | None = None
    bullets: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    degree: str
    institution: str
    year: str
    details: str | None = None


class ProjectEntry(BaseModel):
    name: str
    description: str = ""


class CVContent(BaseModel):
    slug: str
    full_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    headline: str | None = None
    summary: str | None = None
    locale: str = "en"
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class GeneratedCV(BaseModel):
    slug: str
    full_name: str
    email: str
    pdf_path: str
    photo_path: str | None = None
    skills: list[str] = Field(default_factory=list)


class ManifestEntry(BaseModel):
    slug: str
    full_name: str
    email: str
    file: str
    skills: list[str] = Field(default_factory=list)
    locale: str = "en"
    photo: str | None = None
