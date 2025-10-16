from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    linkedin_url = db.Column(db.String(255))
    cv_file = db.Column(db.String(255))
    role = db.Column(db.Enum("admin", "member", name="user_roles"), default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profiles = db.relationship("Profile", back_populates="user", uselist=False)
    opportunities = db.relationship("Opportunity", back_populates="creator", lazy=True)
    sent_messages = db.relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", lazy=True)
    received_messages = db.relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "cv_file": self.cv_file,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

