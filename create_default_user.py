from app import create_app, db
from app.models.User import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create all tables if they don't exist
    db.create_all()
    print("All tables created")

    # Check if user with id=1 exists
    user = User.query.get(1)
    if not user:
        # Create default user
        hashed_password = generate_password_hash('password123')  # Change this password
        default_user = User(
            id=1,  # Explicitly set id=1
            first_name='Default',
            last_name='User',
            email='default@example.com',
            password=hashed_password,
            role='admin'
        )
        db.session.add(default_user)
        db.session.commit()
        print("Default user created with id=1")
    else:
        print("Default user already exists")
