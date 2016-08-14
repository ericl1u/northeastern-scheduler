import logging
from logging.handlers import RotatingFileHandler

from app import app

file_handler = RotatingFileHandler('NortheasternSchedule.log', 'a', 10 * 1024 * 1024, 10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.setLevel(logging.WARNING)
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)
app.logger.info('NortheasternSchedule startup')