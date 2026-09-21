from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Database configuration
db_path = os.path.join(os.path.dirname(__file__), 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'aqua-secret-key-123'

db = SQLAlchemy(app)

# MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, labor, customer
    aqua_credits = db.Column(db.Integer, default=0)
    is_clocked_in = db.Column(db.Boolean, default=False)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    health_status = db.Column(db.String(50), default='Healthy')
    price_per_unit = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class FeedStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0.0) # in kg
    unit_price = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class MedicineStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class Harvest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0.0) # in kg
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(200))

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    performed_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='Pending')
    priority = db.Column(db.String(20), default='Normal')
    steps = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    clock_in = db.Column(db.DateTime, default=datetime.utcnow)
    clock_out = db.Column(db.DateTime)
    date = db.Column(db.String(10))

class WaterQuality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pond_name = db.Column(db.String(50), nullable=False)
    ph = db.Column(db.Float)
    temperature = db.Column(db.Float)
    oxygen = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ROUTES
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username'), password=data.get('password')).first()
    if user:
        return jsonify({
            "status": "success", 
            "user": {
                "id": user.id, 
                "username": user.username, 
                "role": user.role,
                "is_clocked_in": user.is_clocked_in,
                "credits": user.aqua_credits
            }
        })
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({"status": "error", "message": "Username already exists"}), 400
    
    new_user = User(
        username=data.get('username'),
        password=data.get('password'),
        role=data.get('role', 'customer')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "success", "user": {"id": new_user.id, "username": new_user.username, "role": new_user.role}})

@app.route('/api/admin/overview', methods=['GET'])
def admin_overview():
    total_stock = db.session.query(db.func.sum(Stock.quantity)).scalar() or 0
    labor_count = User.query.filter_by(role='labor').count()
    pending_tasks = Task.query.filter_by(status='Pending').count()
    return jsonify({"total_stock": total_stock, "labor_count": labor_count, "pending_tasks": pending_tasks})

@app.route('/api/admin/tasks', methods=['POST'])
def assign_task():
    data = request.json
    new_task = Task(
        description=data.get('description'), 
        assigned_to=int(data.get('assigned_to')),
        priority=data.get('priority', 'Normal'),
        steps=data.get('steps', '')
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/admin/labor', methods=['GET'])
def get_labor_list():
    labors = User.query.filter_by(role='labor').all()
    return jsonify([{"id": u.id, "username": u.username} for u in labors])

@app.route('/api/admin/stock', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_stock():
    if request.method == 'POST':
        data = request.json
        new_stock = Stock(species=data.get('species'), quantity=data.get('quantity'), price_per_unit=data.get('price_per_unit'))
        db.session.add(new_stock)
        db.session.commit()
        return jsonify({"status": "success"})
    
    stocks = Stock.query.all()
    return jsonify([{"id": s.id, "species": s.species, "quantity": s.quantity, "price": s.price_per_unit} for s in stocks])

@app.route('/api/admin/stock/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_stock(id):
    stock = Stock.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(stock)
        db.session.commit()
        return jsonify({"status": "success", "message": "Stock deleted"})
    
    if request.method == 'PUT':
        data = request.json
        stock.species = data.get('species', stock.species)
        stock.quantity = data.get('quantity', stock.quantity)
        stock.price_per_unit = data.get('price', stock.price_per_unit)
        db.session.commit()
        return jsonify({"status": "success", "message": "Stock updated"})

# FEED MANAGEMENT
@app.route('/api/admin/feed', methods=['GET', 'POST'])
def manage_feed():
    if request.method == 'POST':
        data = request.json
        new_feed = FeedStock(name=data.get('name'), quantity=data.get('quantity'), unit_price=data.get('unit_price'))
        db.session.add(new_feed)
        db.session.commit()
        return jsonify({"status": "success", "id": new_feed.id})
    feeds = FeedStock.query.all()
    return jsonify([{"id": f.id, "name": f.name, "quantity": f.quantity, "unit_price": f.unit_price} for f in feeds])

@app.route('/api/admin/feed/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_feed(id):
    feed = FeedStock.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(feed)
        db.session.commit()
        return jsonify({"status": "success"})
    if request.method == 'PUT':
        data = request.json
        feed.name = data.get('name', feed.name)
        feed.quantity = data.get('quantity', feed.quantity)
        feed.unit_price = data.get('unit_price', feed.unit_price)
        db.session.commit()
        return jsonify({"status": "success"})

# MEDICINE MANAGEMENT
@app.route('/api/admin/medicine', methods=['GET', 'POST'])
def manage_medicine():
    if request.method == 'POST':
        data = request.json
        new_med = MedicineStock(name=data.get('name'), quantity=data.get('quantity'), unit_price=data.get('unit_price'))
        db.session.add(new_med)
        db.session.commit()
        return jsonify({"status": "success", "id": new_med.id})
    meds = MedicineStock.query.all()
    return jsonify([{"id": m.id, "name": m.name, "quantity": m.quantity, "unit_price": m.unit_price} for m in meds])

@app.route('/api/admin/medicine/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_medicine(id):
    med = MedicineStock.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(med)
        db.session.commit()
        return jsonify({"status": "success"})
    if request.method == 'PUT':
        data = request.json
        med.name = data.get('name', med.name)
        med.quantity = data.get('quantity', med.quantity)
        med.unit_price = data.get('unit_price', med.unit_price)
        db.session.commit()
        return jsonify({"status": "success"})

# HARVEST MANAGEMENT
@app.route('/api/admin/harvest', methods=['GET', 'POST'])
def manage_harvest():
    if request.method == 'POST':
        data = request.json
        new_h = Harvest(species=data.get('species'), quantity=data.get('quantity'), notes=data.get('notes'))
        db.session.add(new_h)
        db.session.commit()
        return jsonify({"status": "success", "id": new_h.id})
    harvests = Harvest.query.all()
    return jsonify([{"id": h.id, "species": h.species, "quantity": h.quantity, "notes": h.notes, "date": h.date.strftime('%Y-%m-%d')} for h in harvests])

@app.route('/api/admin/harvest/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_harvest(id):
    h = Harvest.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(h)
        db.session.commit()
        return jsonify({"status": "success"})
    if request.method == 'PUT':
        data = request.json
        h.species = data.get('species', h.species)
        h.quantity = data.get('quantity', h.quantity)
        h.notes = data.get('notes', h.notes)
        db.session.commit()
        return jsonify({"status": "success"})

@app.route('/api/labor/tasks/<int:user_id>', methods=['GET'])
def get_labor_tasks(user_id):
    tasks = Task.query.filter_by(assigned_to=user_id).all()
    return jsonify([{
        "id": t.id, 
        "description": t.description, 
        "status": t.status,
        "priority": t.priority,
        "steps": t.steps
    } for t in tasks])

@app.route('/api/labor/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        if task.status != 'Completed':
            task.status = 'Completed'
            user = User.query.get(task.assigned_to)
            if user:
                user.aqua_credits += 10 # Reward credits
            db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

@app.route('/api/labor/activity', methods=['POST'])
def log_activity():
    data = request.json
    new_log = ActivityLog(
        activity_type=data.get('type'),
        details=data.get('details'),
        performed_by=data.get('user_id')
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/admin/notifications', methods=['GET'])
def get_notifications():
    # Fetch recent completed tasks or activity logs
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(20).all()
    notifications = []
    for log in logs:
        user = User.query.get(log.performed_by)
        notifications.append({
            "id": log.id,
            "message": f"Labor {user.username if user else 'Unknown'} logged activity: {log.activity_type} - {log.details}",
            "type": "activity",
            "time": log.timestamp.strftime('%H:%M')
        })
    return jsonify(notifications)

@app.route('/api/customer/stock', methods=['GET'])
def get_shop_stock():
    stocks = Stock.query.filter(Stock.quantity > 0).all()
    return jsonify([{"id": s.id, "species": s.species, "quantity": s.quantity, "price": s.price_per_unit} for s in stocks])

@app.route('/api/customer/buy', methods=['POST'])
def purchase():
    data = request.json
    stock = Stock.query.get(data.get('stock_id'))
    user = User.query.get(data.get('user_id'))
    
    if not stock or not user:
        return jsonify({"status": "error", "message": "Invalid stock or user"}), 400
        
    if stock.quantity >= data.get('quantity'):
        qty = data.get('quantity')
        total_price = qty * stock.price_per_unit
        
        stock.quantity -= qty
        tx = Transaction(customer_id=user.id, stock_id=stock.id, quantity=qty, total_price=total_price)
        
        # Award AquaCredits (1 credit for every 10 Rupees spent)
        reward_credits = int(total_price / 10)
        user.aqua_credits += reward_credits
        
        db.session.add(tx)
        db.session.commit()
        return jsonify({"status": "success", "total": total_price, "credits_earned": reward_credits})
    return jsonify({"status": "error", "message": "Insufficient stock"}), 400

@app.route('/api/customer/orders/<int:user_id>', methods=['GET'])
def get_customer_orders(user_id):
    orders = Transaction.query.filter_by(customer_id=user_id).order_by(Transaction.timestamp.desc()).all()
    results = []
    for o in orders:
        stock = Stock.query.get(o.stock_id)
        results.append({
            "id": o.id,
            "species": stock.species if stock else "Unknown Fish",
            "quantity": o.quantity,
            "total_price": o.total_price,
            "date": o.timestamp.strftime('%Y-%m-%d %H:%M')
        })
    return jsonify(results)

@app.route('/api/admin/expenses', methods=['GET', 'POST'])
def manage_expenses():
    if request.method == 'POST':
        data = request.json
        new_expense = Expense(
            category=data.get('category'),
            amount=data.get('amount'),
            description=data.get('description')
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify({"status": "success", "id": new_expense.id})
    
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return jsonify([{
        "id": e.id,
        "category": e.category,
        "amount": e.amount,
        "description": e.description,
        "date": e.date.strftime('%Y-%m-%d %H:%M')
    } for e in expenses])

@app.route('/api/admin/expenses/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(expense)
        db.session.commit()
        return jsonify({"status": "success", "message": "Expense deleted"})
    
    if request.method == 'PUT':
        data = request.json
        expense.category = data.get('category', expense.category)
        expense.amount = data.get('amount', expense.amount)
        expense.description = data.get('description', expense.description)
        db.session.commit()
        return jsonify({"status": "success", "message": "Expense updated"})

@app.route('/api/labor/attendance/toggle', methods=['POST'])
def toggle_attendance():
    data = request.json
    user = User.query.get(data.get('user_id'))
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    if not user.is_clocked_in:
        # Clocking in
        new_att = Attendance(user_id=user.id, date=today)
        user.is_clocked_in = True
        db.session.add(new_att)
        db.session.commit()
        return jsonify({"status": "success", "is_clocked_in": True})
    else:
        # Clocking out
        att = Attendance.query.filter_by(user_id=user.id, clock_out=None).order_by(Attendance.clock_in.desc()).first()
        if att:
            att.clock_out = datetime.utcnow()
        user.is_clocked_in = False
        db.session.commit()
        return jsonify({"status": "success", "is_clocked_in": False})

@app.route('/api/environmental/latest', methods=['GET'])
def get_environmental_data():
    # Return dummy live data
    return jsonify([
        {"pond_name": "Pond 1", "ph": 7.2, "temp": 28.5, "oxygen": 6.8},
        {"pond_name": "Pond 2", "ph": 7.1, "temp": 29.1, "oxygen": 6.5},
        {"pond_name": "Pond 3", "ph": 6.9, "temp": 27.8, "oxygen": 7.2}
    ])

@app.route('/api/labor/stats/<int:user_id>', methods=['GET'])
def get_labor_stats(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error"}), 404
    
    tasks_done = Task.query.filter_by(assigned_to=user_id, status='Completed').count()
    return jsonify({
        "credits": user.aqua_credits,
        "tasks_done": tasks_done,
        "is_clocked_in": user.is_clocked_in
    })

@app.route('/')
def home():
    return jsonify({"message": "AquaFarm MS API is running"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
