from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base
import sys, os

# директория файла
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# директория файла БД
db_path = os.path.join(BASE_DIR, 'geo.db')


engine = create_engine(f"sqlite:///{db_path}")
Base = declarative_base()

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind = engine)
session = Session()

# данные с доноров изображений
class DonorsData(Base):
    __tablename__ = "donors_data"

    id = Column(Integer, primary_key=True)
    donor_domain = Column(String(255), unique=False, nullable=True) # vk.ru, x.com, ok.ru
    image_url = Column(String(1024), unique=False, nullable=True)
    image_filename = Column(String(255), unique=False, nullable=True)
    lat = Column(String(25), unique=False, nullable=True)
    long = Column(String(25), unique=False, nullable=True)
    radius = Column(Integer, nullable=True)
    user_id = Column(String(255), unique=False, nullable=True)
    parse_time = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)

# детектированный объекты
class DetectedObjects(Base):
    __tablename__ = "detected_objects"

    id = Column(Integer, primary_key=True)
    donor_data_id = Column(Integer, ForeignKey(DonorsData.id))
    # тип и версия детектора
    detect_version = Column(String(25), unique=False, nullable=True) # 0.10 (по номеру релизв)
    score = Column(Integer, nullable=True) # 0.10 (по номеру релизв)
    # координаты относительно исходной фотографии
    box_top = Column(Integer, nullable=True)
    box_bottom = Column(Integer, nullable=True)
    box_left = Column(Integer, nullable=True)
    box_right = Column(Integer, nullable=True)




# данные с доноров изображений
class DonorsDataGeo(Base):
    __tablename__ = "donors_data_geo"

    id = Column(Integer, primary_key=True)
    donor_domain = Column(String(255), unique=False, nullable=True) # vk.ru, x.com, ok.ru
    image_url = Column(String(1024), unique=False, nullable=True)
    image_filename = Column(String(255), unique=False, nullable=True)
    lat = Column(String(25), unique=False, nullable=True)
    long = Column(String(25), unique=False, nullable=True)
    radius = Column(Integer, nullable=True)
    user_id = Column(String(255), unique=False, nullable=True)
    parse_time = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)

