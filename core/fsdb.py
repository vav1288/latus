
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm

Base = sqlalchemy.ext.declarative.declarative_base()

class Fsdb(Base):
    """
    File System Database
    """
    __tablename__ = 'hash'

    autoindex = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    abspath = sqlalchemy.Column(sqlalchemy.Text)
    mtime = sqlalchemy.Column(sqlalchemy.Integer)
    size = sqlalchemy.Column(sqlalchemy.Integer)
    sha512val = sqlalchemy.Column(sqlalchemy.Text)
    sha512time = sqlalchemy.Column(sqlalchemy.Float)
    count = sqlalchemy.Column(sqlalchemy.Integer)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime)

if __name__ == "__main__":
    engine = sqlalchemy.create_engine('sqlite:////temp.db') # todo: make a real path somehow
    Base.metadata.create_all(engine)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    fsdb = Fsdb()
    session.add(fsdb)
    session.commit()
