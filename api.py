from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from functools import wraps
import jwt
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisissecret'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

class OrderedProduct(db.Model):
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    description= db.Column(db.String(64))
    quantity   = db.Column(db.Integer)
    price      = db.Column(db.Integer)
    total_amount = db.Column(db.Integer)
    total_discount = db.Column(db.Integer)
    invoice = db.relationship('Invoice')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(64))
    password = db.Column(db.String(64))
    admin = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    discount = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                    nullable=False)
    invoice_number = db.Column(db.Integer, unique=True)
    total_qty = db.Column(db.Integer)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now)
    subtotal = db.Column(db.Integer)
    total_discount = db.Column(db.Integer)
    total_amount = db.Column(db.Float)

def special_discount(subtotal, total_amount, total_qty=None):
    if subtotal >= 2000000:
        total_amount = int(total_amount * 0.8)

    elif subtotal > 1300000 or subtotal < 2000000:
        # TODO: check ordered_products table different products
        pass

    elif subtotal > 600000 or subtotal < 1300000 :
        # TODO: check ordered_products table different products
        pass

    elif subtotal > 300000 or subtotal < 600000:
        total_amount = int(total_amount * 0.8)

    return total_amount

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/invoices/create', methods=['POST'])
@token_required
def create_invoice(current_user):
    total_amount = 0
    total_discount = 0
    total_qty = 0
    subtotal = 0
    ordered_products = []
    data = request.get_json()

    if len(data['products']) == 0:
        return jsonify({'message': 'Not product list given!'})

    products = data['products']

    for p in products:
        product = Product.query.filter_by(id=p['id']).first()

        if not product:
            return jsonify({'message': 'Not product found!'})

        p['description'] = product.description
        p['price'] = product.price
        p['total_amount'] = product.price * p['quantity']
        p['total_discount'] = int(p['total_amount'] * int(product.discount) / 100)

        subtotal += p['total_amount']
        total_discount += p['total_discount']
        total_amount += subtotal - total_discount
        total_qty += p['quantity']
        ordered_products.append(p)

    total_amount = special_discount(subtotal, total_amount)

    new_invoice = Invoice(user_id=current_user.id,
            subtotal=subtotal,
            ip_address = request.remote_addr,
            invoice_number = int(datetime.now().timestamp()),
            total_discount=total_discount,
            total_amount=total_amount,
            total_qty=total_qty)

    db.session.add(new_invoice)
    db.session.commit()

    invoice = Invoice.query.filter_by(id=new_invoice.id).first()

    for op in ordered_products:
        new_op = OrderedProduct(invoice_id=new_invoice.id,
                product_id=op['id'],
                description=op['description'],
                price=op['price'],
                quantity=op['quantity'],
                total_amount=op['total_amount'],
                total_discount=op['total_discount']
        )

        db.session.add(new_op)
        db.session.commit()

    ops = OrderedProduct.query.filter_by(invoice_id=invoice.id).all()

    product_list = []

    for op in ops:
        product_list.append({
            'description': op.description,
            'price': op.price,
            'quantity': op.quantity,
            'price': op.price,
            'total_amount': op.total_amount,
            'total_discount': op.total_discount
            })

    return jsonify({
        'message': 'Order created!',
        'invoice': {
            'invoice_number': invoice.invoice_number,
            'created_at': invoice.created_at,
            'subtotal': invoice.subtotal,
            'total_discount': invoice.total_discount,
            'total_amount': invoice.total_amount,
            'products': product_list
        }
    })

@app.route('/invoices/check-out/<id>', methods=['GET'])
def check_out_invoice(id):
    invoice = Invoice.query.filter_by(id=id).first()

    if not invoice:
        return jsonify({'message': 'Not invoice found!'})

    invoice.ip_address = request.remote_addr
    invoice.invoice_number = int(datetime.now().timestamp())

    db.session.commit()
    return jsonify({'invoice_number': invoice.invoice_number})

@app.route('/sign-up', methods=['POST'])
def create_user():
    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created!'})

@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({
                            'public_id': user.public_id,
                            'exp': datetime.utcnow() + timedelta(minutes=15)
                            },
                            app.config['SECRET_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

@app.route('/users', methods=['PUT'])
@token_required
def change_to_admin(current_user):

    if not current_user.name == 'admin':
        return jsonify({'message': 'This user is not allow change the role'})

    user = User.query.filter_by(id=current_user.id).first()

    user.admin = True
    db.session.commit()

    return jsonify({'message': 'Role admin assigned!'})

@app.route('/users', methods=['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    users = User.query.all()
    result = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['admin'] = user.admin
        result.append(user_data)

    return jsonify({'users': result})

@app.route('/users/<public_id>', methods=['GET'])
def get_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['admin'] = user.admin

    return jsonify({'user': user_data})

@app.route('/products', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    result = []

    for p in products:
        product_data = {}
        product_data['id'] = p.id
        product_data['name'] = p.name
        product_data['description'] = p.description
        product_data['price'] = p.price
        product_data['discount'] = p.discount
        product_data['created_at'] = p.created_at
        product_data['updated_at'] = p.updated_at
        result.append(product_data)

    return jsonify({'products': result})

@app.route('/products/<id>', methods=['GET'])
@token_required
def get_product(current_user, id):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    product = Product.query.filter_by(id=id).first()

    if not product:
        return jsonify({'message': 'No user found!'})

    product_data = {}
    product_data['public_id'] = product.id
    product_data['name'] = product.name
    product_data['description'] = product.description
    product_data['price'] = product.price
    product_data['discount'] = product.discount
    product_data['created_at'] = product.created_at
    product_data['updated_at'] = product.updated_at

    return jsonify({'product': product_data})

@app.route('/products', methods=['POST'])
@token_required
def create_product(current_user):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()

    new_product = Product(name=data['name'],
                            description=data['description'],
                            price=data['price'],
                            discount=data['discount'])
    db.session.add(new_product)
    db.session.commit()

    return jsonify({'message': 'Product created!'})

@app.route('/products/<id>', methods=['PUT'])
@token_required
def save_product(current_user, id):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    product = Product.query.filter_by(id=id).first()
    data = request.get_json()

    if not product:
        return jsonify({'message': 'No product found!'})

    product.name = data['name']
    product.description = data['description']
    product.price = data['price']
    product.discount = data['discount']
    db.session.commit()

    return jsonify({'message': 'Product saved'})

@app.route('/products/<id>', methods=['DELETE'])
@token_required
def delete_product(current_user, id):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    product = Product.query.filter_by(id=id).first()

    if not product:
        return jsonify({'message': 'No product found'})

    db.session.delete(product)
    db.session.commit()

    return jsonify({'message': 'The product has been deleted'})

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(debug=True, host='0.0.0.0')
    # manager.run()
