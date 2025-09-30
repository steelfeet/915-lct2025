from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import declarative_base

engine = create_engine('postgresql://postgres:mdk12l91@localhost/coins_v3')
Base = declarative_base()

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind = engine)
session = Session()



"""
███    ███    ██████    ███     ██     ██   ████████    ██████    ███████    
██ █  █ ██   ██    ██   ██ ██   ██             ██      ██    ██   ██    ██   
██  ██  ██   ██    ██   ██  ██  ██     ██      ██      ██    ██   ███████    
██      ██   ██    ██   ██   ██ ██     ██      ██      ██    ██   ██  ██     
██      ██    ██████    ██     ███     ██      ██       ██████    ██    ██   
"""

# исходные данные: статьи, новости, посты
class Monitor_Previews(Base):
    __tablename__ = "monitor_previews"
    id = Column(Integer, primary_key=True)
    donor = Column(String(255), unique=False, nullable=True) # домен донора
    donor_url = Column(String(512), unique=False, nullable=True) # полная ссылка на донора
    donor_type = Column(String(255), unique=False, nullable=True) # auction, forum, catalog, article 
    
    status = Column(Integer) 
    """
    0 - новость скачана
    1 - проверено вручную
    2 - не подходящие
    """

    time = Column(Integer) # Unix timestamp, дата новости
    parse_time = Column(Integer) # Unix timestamp, дата парсинга
    title = Column(Text)
    description = Column(Text)
    full_html = Column(Text) # необработанные данные о сущности, желательно json


# виды обработки данных текста
class Monitor_Processing_Types(Base):
    __tablename__ = "monitor_processing_types"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    desc = Column(Text)


# распарсенный текст новости
class Monitor_Paragraphs(Base):
    __tablename__ = "monitor_paragraphs"
    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey(Monitor_Previews.id)) # данные, к которой относится изображение
    clear_text = Column(Text) # распарсенный текст, без разметки
    

# статусы обработки параграфов
class Monitor_Paragraphs_Statuses(Base):
    __tablename__ = "monitor_paragraphs_statuses"
    id = Column(Integer, primary_key=True)
    paragraph_id = Column(Integer, ForeignKey(Monitor_Paragraphs.id)) # данные, к которой относится изображение
    processing_version = Column(Integer, ForeignKey(Monitor_Processing_Types.id))  # версия обработки


# отдельные токены параграфа
class Monitor_Paragraph_Words(Base):
    __tablename__ = "monitor_paragraph_words"
    id = Column(Integer, primary_key=True)
    paragraph_id = Column(Integer, ForeignKey(Monitor_Paragraphs.id)) 
    processing_version = Column(Integer, ForeignKey(Monitor_Processing_Types.id))  # версия обработки

    text = Column(Text) 

    ner_type = Column(Text)
    ner_subtype = Column(Text)











class Monitor_Images(Base):
    __tablename__ = "monitor_images"
    id = Column(Integer, primary_key=True)
    monitor_id = Column(Integer, ForeignKey(Monitor_Previews.id)) # данные, к которой относится изображение
    
    is_main = Column(Integer) # 1 - главное изображение новости
    is_geo_good = Column(Integer) # 1 - подходит для определения координат

    image_src = Column(String(512), unique=False, nullable=True) # полная ссылка на донора
    image_path = Column(String(512), unique=False, nullable=True) # куда сохранен локально (без DONORS_IMAGES_DIR)
    image_alt = Column(String(1024), unique=False, nullable=True) # alt


# виды обработки данных текста
class Monitor_Image_Processing_Types(Base):
    __tablename__ = "monitor_image_processing_types"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    desc = Column(Text)


# key-value статусы обработки параграфов
class Monitor_Image_Statuses(Base):
    __tablename__ = "monitor_image_statuses"
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey(Monitor_Images.id)) # данные, к которой относится изображение
    processing_version = Column(Integer, ForeignKey(Monitor_Image_Processing_Types.id))  # версия обработки

    key = Column(Text)    
    value = Column(Text)    


# обьекты, обнаруженные на изображении
class Monitor_Objects(Base):
    __tablename__ = "monitor_objects"
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey(Monitor_Images.id)) # изображение, к которому относится объект

    # версия используемой модели
    version = Column(Integer)
    # 7 - IDEA-Research/grounding-dino-base; 0600_Detect_Objects_1

    score = Column(Float)
    label = Column(Text)
    # координаты, по которым находится объект
    left = Column(Integer)
    right = Column(Integer)
    top = Column(Integer)
    bottom = Column(Integer)


# обьекты, обнаруженные на изображении
class Monitor_Objects_Classified(Base):
    __tablename__ = "monitor_objects_classified"
    id = Column(Integer, primary_key=True)
    objects_id = Column(Integer, ForeignKey(Monitor_Objects.id)) # изображение, к которому относится объект

    # версия используемой модели
    version = Column(Integer)
    # 1 - BioCLIP

    score = Column(Float)
    name_en = Column(Text)
    name_ru = Column(Text)



"""

 ██████    ███████    ██████     ██████     ██   ███     ██   ████████   
██         ██        ██    ██   ██               ██ ██   ██      ██      
██   ██    █████     ██    ██    █████      ██   ██  ██  ██      ██      
██    ██   ██        ██    ██        ██     ██   ██   ██ ██      ██      
██████     ███████    ██████    ██████      ██   ██     ███      ██     

"""

# именованные сущности
class Osint_Geo_Ner(Base):
    __tablename__ = "osint_geo_ner"
    id = Column(Integer, primary_key=True)
    paragraph_id = Column(Integer, ForeignKey(Monitor_Paragraphs.id)) 
    word_position = Column(Integer) # номер слова в параграфе 
    version = Column(Integer) # версия обработки
    # 3 - ручное выделение
    
    ner_type = Column(Text)
    ner_subtype = Column(Text)
