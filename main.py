from db.session import DBHandler

if __name__ == '__main__':
    db = DBHandler()
    db.connect()
    if db.Session:
        session = db.Session()
