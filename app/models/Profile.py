from app import db
from datetime import datetime

class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150))
    experience_years = db.Column(db.Integer)
    sector = db.Column(db.String(100))
    skills = db.Column(db.JSON)
    availability = db.Column(db.Enum("available", "busy", "unknown", name="availability"))
    location = db.Column(db.String(150))
    data = db.Column(db.JSON)  # Store full profile data as JSON
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", back_populates="profiles")
    matches = db.relationship("Match", back_populates="profile", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "experience_years": self.experience_years,
            "sector": self.sector,
            "skills": self.skills,
            "availability": self.availability,
            "location": self.location,
            "data": self.data,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
