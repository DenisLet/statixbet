import os
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import app, db
from app.models import User

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User}

@app.cli.command("create-superuser")
def create_superuser():
    """Create a new superuser using environment variables."""
    username = os.getenv('SUPERUSER_NAME')
    email = os.getenv('SUPERUSER_EMAIL')
    password = os.getenv('SUPERUSER_PASSWORD')

    if not username or not email or not password:
        print("SUPERUSER_NAME, SUPERUSER_EMAIL, and SUPERUSER_PASSWORD must be set in the .flaskenv file.")
        return

    user = User(
        username=username,
        email=email,
        is_admin=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Superuser {username} created successfully.")