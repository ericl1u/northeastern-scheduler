from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

from app import app

db = SQLAlchemy(app)
engine = db.engine
Session = sessionmaker(bind=engine)
