from app import db
from datetime import datetime

class LinkedInLead(db.Model):
    __tablename__ = 'linkedin_leads'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False)  # UUID from trigger
    full_name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    position = db.Column(db.String(255), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    profile_url = db.Column(db.String(500), nullable=True)
    followers = db.Column(db.Integer, nullable=True)
    connections = db.Column(db.Integer, nullable=True)
    education = db.Column(db.Text, nullable=True)
    personalized_message = db.Column(db.Text, nullable=True)
    message_length = db.Column(db.Integer, nullable=True)
    generation_date = db.Column(db.DateTime, nullable=True)
    url_image = db.Column(db.String(500), nullable=True)
    total_leads = db.Column(db.Integer, nullable=True)
    job_title = db.Column(db.String(255), nullable=True)
    entreprise = db.Column(db.String(255), nullable=True)
    pages = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'full_name': self.full_name,
            'title': self.title,
            'position': self.position,
            'company': self.company,
            'location': self.location,
            'profile_url': self.profile_url,
            'followers': self.followers,
            'connections': self.connections,
            'education': self.education,
            'personalized_message': self.personalized_message,
            'message_length': self.message_length,
            'generation_date': self.generation_date.isoformat() if self.generation_date else None,
            'url_image': self.url_image,
            'total_leads': self.total_leads,
            'job_title': self.job_title,
            'entreprise': self.entreprise,
            'pages': self.pages,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }
