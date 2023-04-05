from sqlalchemy import CHAR, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Bangumi(Base):
    __tablename__ = "bangumi"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    subtitle_group = Column(Text, nullable=False)
    keyword = Column(Text, nullable=False)
    update_time = Column(CHAR(5), nullable=False)
    cover = Column(Text, nullable=False)
    status = Column(Integer, nullable=False)


class Download(Base):
    __tablename__ = "download"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    episode = Column(Integer, nullable=False)
    download = Column(Text, nullable=False)
    status = Column(Integer, nullable=False)


class Filter(Base):
    __tablename__ = "filter"

    id = Column(Integer, primary_key=True)
    bangumi_name = Column(Text, nullable=False, unique=True)
    subtitle = Column(Text)
    include = Column(Text)
    exclude = Column(Text)
    regex = Column(Text)


class Followed(Base):
    __tablename__ = "followed"

    id = Column(Integer, primary_key=True)
    bangumi_name = Column(Text, nullable=False, unique=True)
    episode = Column(Integer)
    status = Column(Integer)
    updated_time = Column(Integer)


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True)
    bangumi_name = Column(Text, nullable=False, unique=True)
    episode = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    updated_time = Column(Integer, nullable=False)


class Subtitle(Base):
    __tablename__ = "subtitle"

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
