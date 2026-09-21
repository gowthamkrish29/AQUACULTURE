from app import app, db, User, Stock

def seed():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password123', role='admin'))
            print("Admin created.")
        if not User.query.filter_by(username='labor1').first():
            db.session.add(User(username='labor1', password='password123', role='labor'))
            print("Labor created.")
        if Stock.query.count() == 0:
            db.session.add_all([
                Stock(species='Tilapia', quantity=1000, price_per_unit=5.0),
                Stock(species='Catfish', quantity=500, price_per_unit=7.5)
            ])
            print("Stock added.")
        db.session.commit()
        print("Success.")

if __name__ == '__main__':
    seed()
