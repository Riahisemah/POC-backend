from app import db
from datetime import datetime

class Opportunity(db.Model):
    __tablename__ = "opportunities"
    id = db.Column(db.Integer, primary_key=True)
    opportunityId = db.Column(db.String(50), unique=True)
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    company = db.Column(db.String(150))
    location = db.Column(db.String(150))
    type = db.Column(db.String(50))
    required_skills = db.Column(db.JSON)
    preferred_skills = db.Column(db.JSON)
    experience_level = db.Column(db.String(50))
    education_level = db.Column(db.String(50))
    salary_range = db.Column(db.JSON)
    remote_option = db.Column(db.Boolean, default=False)
    industry = db.Column(db.String(100))
    language_requirements = db.Column(db.JSON)
    work_schedule = db.Column(db.String(50))
    keywords = db.Column(db.JSON)
    benefits = db.Column(db.JSON)
    rating = db.Column(db.Float, default=0.0)
    source = db.Column(db.String(50))
    sector = db.Column(db.String(100))
    urgency_level = db.Column(db.String(50))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)

    creator = db.relationship("User", back_populates="opportunities")
    matches = db.relationship("Match", back_populates="opportunity", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "opportunityId": self.opportunityId,
            "title": self.title,
            "description": self.description,
            "company": self.company,
            "location": self.location,
            "type": self.type,
            "requiredSkills": self.required_skills,
            "preferredSkills": self.preferred_skills,
            "experienceLevel": self.experience_level,
            "educationLevel": self.education_level,
            "salaryRange": self.salary_range,
            "remoteOption": self.remote_option,
            "industry": self.industry,
            "languageRequirements": self.language_requirements,
            "workSchedule": self.work_schedule,
            "keywords": self.keywords,
            "benefits": self.benefits,
            "rating": self.rating,
            "source": self.source,
            "sector": self.sector,
            "urgencyLevel": self.urgency_level,
            "createdBy": self.created_by,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "expiryDate": self.expiry_date.isoformat() if self.expiry_date else None,

        }
