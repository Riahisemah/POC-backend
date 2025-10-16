from app import db
from datetime import datetime

class Match(db.Model):
    __tablename__ = "matches"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.id"), nullable=False)
    score = db.Column(db.Float)
    status = db.Column(db.Enum("pending", "accepted", "rejected", name="match_status"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("Profile", back_populates="matches")
    opportunity = db.relationship("Opportunity", back_populates="matches")

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "opportunity_id": self.opportunity_id,
            "score": self.score,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

