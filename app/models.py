"""Pydantic models for the resume seed and persisted content."""

from __future__ import annotations

from typing import Literal

from pydantic import AnyUrl, BaseModel, Field


class ContactLink(BaseModel):
    label: str
    url: AnyUrl


class Profile(BaseModel):
    id: str
    name: str
    headline: str
    summary: str
    contact_links: list[ContactLink] = Field(default_factory=list)
    location: str | None = None
    visible: bool = True


class ExperienceAchievement(BaseModel):
    id: str
    text: str
    display_order: int = 0
    visible: bool = True


class Experience(BaseModel):
    id: str
    employer: str
    title: str
    start_date: str
    end_date: str | None = None
    current: bool = False
    location: str | None = None
    description: str | None = None
    achievements: list[ExperienceAchievement] = Field(default_factory=list)
    display_order: int = 0
    visible: bool = True


class Skill(BaseModel):
    id: str
    name: str
    normalized_key: str | None = None
    proficiency: str | None = None
    emphasis: str | None = None
    display_order: int = 0
    visible: bool = True


class SkillGroup(BaseModel):
    id: str
    name: str
    skills: list[Skill] = Field(default_factory=list)
    display_order: int = 0
    visible: bool = True


class Project(BaseModel):
    id: str
    title: str
    summary: str
    contribution: str | None = None
    outcome: str | None = None
    technologies: list[str] = Field(default_factory=list)
    links: list[ContactLink] = Field(default_factory=list)
    display_order: int = 0
    visible: bool = True


class Education(BaseModel):
    id: str
    institution: str
    credential: str
    start_date: str | None = None
    end_date: str | None = None
    details: str | None = None
    display_order: int = 0
    visible: bool = True


class Certification(BaseModel):
    id: str
    name: str
    issuer: str
    issue_date: str | None = None
    expiration_date: str | None = None
    verification_url: AnyUrl | None = None
    display_order: int = 0
    visible: bool = True


class ResumeSeed(BaseModel):
    content_status: Literal["placeholder", "production"]
    profile: Profile
    experience: list[Experience] = Field(default_factory=list)
    skill_groups: list[SkillGroup] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
