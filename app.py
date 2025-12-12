from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from extentions import db
from models import User, FOOD_ITEMS, UserOrder, OrderInfo, PaymentInfo, SupportTicket, FavoriteItem
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import desc, func, distinct, text 
import logging
import os
import requests 
import json 
from functools import wraps 
import time 


# 0. Логгер орнату

logging.basicConfig(level=logging.DEBUG)


# 1. Flask 

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'suret_kuipiya_soz_osha_miz_super_secret'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['DEBUG'] = True


db.init_app(app)
with app.app_context():
    try:
        
        db.create_all() 
        logging.info("Дерекқор кестелері жасалды")
        
        if User.query.count() > 0:
            first_user = User.query.order_by(User.id.asc()).first()
            if first_user and not first_user.is_admin:
                 first_user.is_admin = True
                 db.session.commit()
                 logging.info(f"Қолданушы ID {first_user.id} Әкімші болып тағайындалды.")

    except OperationalError as e:
        logging.error(f"Дерекқор қатесі: {e}")
    except Exception as e:
        logging.error(f"Басқа DB қатесі: {e}")


# 3. Flask-Login

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Кіру үшін алдымен тіркелу керек.'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logging.error(f"User loading error: {e}")
        return None


# 4. admin

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Бұл бет тек Әкімшілер үшін.", 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# 5. ДЕРЕКҚОРДЫ ТАЗАЛАУ РОУТЫ 

@app.route('/db_reset')
def db_reset():
    db.session.rollback() 
    with app.app_context():
        try:
            db.drop_all()
            db.create_all()
            db.session.commit()
            flash("Дерекқор толығымен тазартылды. Енді бірінші қолданушыны тіркеңіз, ол Әкімші болады.", 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Дерекқорды тазарту қатесі: {e}")
            flash(f"Дерекқорды тазарту кезінде қате шықты. Серверді қайта іске қосып, /db_reset қайталаңыз.", 'error')
        
    return redirect(url_for('signup'))


# 6. ТІКЕЛЕЙ ӘКІМШІ КІРУ РОУТЫ

@app.route('/admin_login')
def admin_login():
    try:
        admin_user = User.query.filter_by(is_admin=True).first()
        
        if not admin_user:
            admin_user = User(username='admin_boss', email='admin@site.com', is_admin=True)
            admin_user.set_password('admin123') 
            db.session.add(admin_user)
            db.session.commit()
            flash("Жаңа Әкімші аккаунты автоматты түрде жасалды (boss/admin123).", 'info')
        
        login_user(admin_user)
        flash("Сәтті кірдіңіз! Сіз Әкімші Панеліндесіз.", 'success')
        return redirect(url_for('admin_dashboard'))

    except SQLAlchemyError as e:
        db.session.rollback() 
        logging.error(f"Admin login database error: {e}")
        flash("Әкімші аккаунтын жасау/іздеу кезінде дерекқор қатесі шықты. /db_reset қолданып көріңіз.", 'error')
        return redirect(url_for('login'))
    except Exception as e:
        logging.error(f"Admin login general error: {e}")
        flash("Кіру кезінде белгісіз қате шықты. Серверді тексеріңіз.", 'error')
        return redirect(url_for('login'))



# 7. Маршруттар


@app.route('/')
@app.route('/index')
def index():
    categories = {}
    favorite_item_ids = []


    if current_user.is_authenticated:
        favorite_item_ids = [fav.food_item_id for fav in current_user.favorite_items.all()]

    for item in FOOD_ITEMS:
        item['is_favorite'] = item['id'] in favorite_item_ids 
        categories.setdefault(item['category'], []).append(item)
    return render_template('index.html', categories=categories)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    db.session.rollback()
    
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            if User.query.filter((User.username==username)|(User.email==email)).first():
                flash("Қолданушы аты немесе email бұрын тіркелген")
                return redirect(url_for('signup'))
            
            user = User(username=username, email=email)
            user.set_password(password)
            
            user_count = User.query.count()
            if user_count == 0:
                user.is_admin = True
                flash("Сіз жүйенің алғашқы қолданушысы және Әкімшісі ретінде тіркелдіңіз!", 'success')
            
            db.session.add(user)
            db.session.commit()
            
            flash("Сәтті тіркелдіңіз! Енді кіруіңізге болады.")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Тіркелу кезінде қате: {e}", 'error')
            logging.error(f"Тіркелу қатесі: {e}")
            return redirect(url_for('signup'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    db.session.rollback() 
    
    if current_user.is_authenticated:
        if current_user.is_admin:
             return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')

        user = User.query.filter_by(username=username_or_email).first() \
               or User.query.filter_by(email=username_or_email).first()

        if user is None or not user.check_password(password):
            flash("Қате қолданушы аты немесе құпиясөз")
            return redirect(url_for('login'))

        login_user(user, remember=True)
        flash(f"Қош келдіңіз, {user.username}!")
        
        if user.is_admin:
             return redirect(url_for('admin_dashboard'))
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('cart', None)
    flash("Сіз жүйеден шықтыңыз.")
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
        
    try:
        orders = current_user.orders.order_by(desc(UserOrder.timestamp)).all()
        tickets = current_user.tickets.order_by(desc(SupportTicket.timestamp)).all()
        # Сүйікті тағамдарды алу
        favorite_ids = [fav.food_item_id for fav in current_user.favorite_items.all()]
        favorite_items = [item for item in FOOD_ITEMS if item['id'] in favorite_ids]
    except Exception:
        orders = []
        tickets = []
        favorite_items = []
        
    return render_template('dashboard.html', orders=orders, tickets=tickets, favorite_items=favorite_items)




@app.route('/toggle_favorite/<int:item_id>', methods=['POST'])
@login_required
def toggle_favorite(item_id):
    # 1. Тағамның бар екенін тексеру (FOOD_ITEMS тізімінде)
    item_exists = any(item['id'] == item_id for item in FOOD_ITEMS)
    if not item_exists:
        flash("Тағам табылмады.", 'error')
        return redirect(url_for('index'))
        
    try:
        db.session.rollback()
        
        
        favorite = FavoriteItem.query.filter_by(
            user_id=current_user.id,
            food_item_id=item_id
        ).first()

        if favorite:
            
            db.session.delete(favorite)
            flash(f"Тағам сүйіктілер тізімінен жойылды.", 'info')
        else:
            
            new_favorite = FavoriteItem(
                user_id=current_user.id,
                food_item_id=item_id
            )
            db.session.add(new_favorite)
            flash(f"Тағам сүйіктілер тізіміне қосылды!", 'success')
            
        db.session.commit()
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Favorite toggle error: {e}")
        flash("Сүйікті тағамдарды өзгерту кезінде қате шықты.", 'error')
        
    return redirect(url_for('index'))


# (Admin Dashboard)

def get_top_selling_items():
    """GROUP BY және COUNT арқылы ең көп сатылған тағамдарды есептейді."""
    try:
        db.session.rollback()
        
        top_items = db.session.query(
            OrderInfo.item_name,
            func.sum(OrderInfo.quantity).label('total_quantity')
        ).group_by(OrderInfo.item_name) \
         .order_by(desc('total_quantity')) \
         .limit(5) \
         .all()
         
        
        return [{'name': item.item_name, 'quantity': item.total_quantity} for item in top_items]
    except Exception as e:
        logging.error(f"Top selling query failed: {e}")
        return []

@app.route('/admin')
@login_required
@admin_required 
def admin_dashboard():
    orders = UserOrder.query.order_by(desc(UserOrder.timestamp)).all()
    statuses = ['Жаңа - Қолма-қол', 'Жаңа - Төлем күтуде', 'Төленді', 'Дайындалуда', 'Жеткізілуде', 'Аяқталды', 'Бас тартылды']
    
    tickets = SupportTicket.query.filter_by(status='Жаңа').order_by(desc(SupportTicket.timestamp)).all()
    ticket_statuses = ['Жаңа', 'Қаралуда', 'Жауап күтуде', 'Жабық']
    
    # (GROUP BY)
    top_selling = get_top_selling_items()

    
    backup_info = {
        'status': 'Қажетті сценарийлер бар',
        'details': [
            "1. Резервтік көшірме сценарийі (`backup.py`) іске асырылған (DB-ны қауіпсіз жерге көшіру).",
            "2. Толық (Full) және Дифференциалды (Differential) бэкап түрлері қарастырылған.",
            "3. Бэкапты сақтау орны: Бұлттық қойма (Cloud Storage) немесе жергілікті сервер."
        ]
    }

    return render_template(
        'admin_dashboard.html', 
        orders=orders, 
        statuses=statuses, 
        tickets=tickets, 
        ticket_statuses=ticket_statuses,
        top_selling=top_selling, 
        backup_info=backup_info
    )

@app.route('/admin/update_order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_order(order_id):
    new_status = request.form.get('status')
    order = UserOrder.query.get(order_id)
    
    if order:
        db.session.rollback() 
        order.order_status = new_status
        db.session.commit()
        flash(f"Тапсырыс №{order_id} статусы '{new_status}' болып өзгертілді.", 'success')
    else:
        flash(f"Тапсырыс №{order_id} табылмады.", 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_ticket/<int:ticket_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_ticket(ticket_id):
    new_status = request.form.get('status')
    ticket = SupportTicket.query.get(ticket_id)
    
    if ticket:
        db.session.rollback()
        ticket.status = new_status
        db.session.commit()
        flash(f"Билет №{ticket_id} статусы '{new_status}' болып өзгертілді.", 'success')
    else:
        flash(f"Билет №{ticket_id} табылмады.", 'error')
        
    return redirect(url_for('admin_dashboard'))



# Себет 

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []

    try:
        item_id = request.form.get('item_id', type=int)
        quantity = request.form.get('quantity', type=int, default=1)
    except Exception:
        flash("Қате деректер енгізілді.")
        return redirect(url_for('index'))

    selected_item = next((item for item in FOOD_ITEMS if item['id'] == item_id), None)

    if selected_item:
        item_dict = {
            'id': selected_item['id'],
            'name': selected_item['name'],
            'price': selected_item['price'],
            'quantity': quantity
        }
        for item in session['cart']:
            if item['id'] == item_id:
                item['quantity'] += quantity
                break
        else:
            session['cart'].append(item_dict)
            
        session.modified = True
        flash(f"{selected_item['name']} ({quantity} дана) себетке қосылды.")
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 'cart' in session:
        initial_length = len(session['cart'])
        
        session['cart'] = [item for item in session['cart'] if item['id'] != item_id]
        
        if len(session['cart']) < initial_length:
            flash("Тауар себеттен сәтті жойылды.", 'success')
        else:
            flash("Жойылатын тауар табылмады.", 'error')
            
        session.modified = True
        
    return redirect(url_for('checkout'))


# Checkout 
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
        
    if 'cart' not in session or not session['cart']:
        flash("Себет бос, тапсырыс бере алмайсыз.", 'error')
        return redirect(url_for('index'))

    cart_items = session['cart']
    
    initial_price = sum(float(item['price'])*int(item['quantity']) for item in cart_items)
    SERVICE_FEE_PERCENTAGE = 0.06
    service_fee = initial_price * SERVICE_FEE_PERCENTAGE
    total_price = initial_price + service_fee 
    
    if request.method == 'POST':
        delivery_address = request.form.get('delivery_address')
        payment_method = request.form.get('payment_method')
        
        if not delivery_address or len(delivery_address.strip()) < 5:
            flash("Жеткізу мекенжайын толық енгізіңіз.", 'error')
            return redirect(url_for('checkout'))
        
        if payment_method not in ['Картамен', 'Қолма-қол']:
            flash("Төлем әдісін таңдаңыз.", 'error')
            return redirect(url_for('checkout'))

        try:
            db.session.rollback() 
            new_order = UserOrder(
                user_id=current_user.id,
                total_price=total_price,
                delivery_address=delivery_address,
                payment_method=payment_method,
                order_status='Жаңа - Төлем күтуде' if payment_method == 'Картамен' else 'Жаңа - Қолма-қол'
            )
            db.session.add(new_order)
            db.session.flush()

            for item in cart_items:
                order_info = OrderInfo(
                    item_name=item['name'],
                    item_price=item['price'],
                    quantity=item['quantity'],
                    order_id=new_order.id
                )
                db.session.add(order_info)

            db.session.commit()
            logging.info(f"DB-ға сәтті сақталды. Order ID: {new_order.id}")

            session.pop('cart', None) 
            flash(f"Тапсырыс қабылданды! Жалпы сома: {int(total_price)} ₸.", 'success')

            if payment_method == 'Картамен':
                return redirect(url_for('payment', order_id=new_order.id)) 
            else:
                return redirect(url_for('order_accepted', order_id=new_order.id))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Order saving error: {e}", exc_info=True) 
            flash("Тапсырыс беру кезінде қате шықты. Қайталап көріңіз.", 'error')
            return redirect(url_for('checkout'))
    
    return render_template(
        'checkout.html', 
        cart_items=cart_items, 
        total_price=total_price,
        initial_price=initial_price, 
        service_fee=service_fee 
    )


# Төлем 
@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
@login_required
def payment(order_id):
    order = UserOrder.query.get_or_404(order_id)

    if order.order_status in ['Төленді', 'Жаңа - Қолма-қол']:
        flash(f"Тапсырыс №{order_id} қазірдің өзінде өңделуде/төленген.", 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        card_number = request.form.get('card_number')
        card_holder = request.form.get('card_holder')
        bank_name = request.form.get('bank_name')

        if not card_number or len(card_number) < 16 or not card_holder:
            flash("Карта деректерін дұрыс енгізіңіз.", 'error')
            return render_template('payment.html', order=order)

        try:
            db.session.rollback() 
            
            new_payment = PaymentInfo(
                order_id=order_id,
                card_ending=card_number[-4:], 
                card_holder=card_holder,
                bank_name=bank_name
            )
            db.session.add(new_payment)

            order.order_status = 'Төленді'
            db.session.commit()
            
            logging.info(f"Тапсырыс {order_id} сәтті төленді. Банк: {bank_name}")
            flash(f"Төлем сәтті өтті. Тапсырыс №{order_id} қабылданды!", 'success')
            
            return redirect(url_for('order_accepted', order_id=order_id)) 

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Payment saving error: {e}")
            flash("Төлем деректерін сақтау кезінде қате шықты. Қайталап көріңіз.", 'error')
            return render_template('payment.html', order=order)
        
    return render_template('payment.html', order=order)


@app.route('/order_accepted/<int:order_id>')
@login_required
def order_accepted(order_id):
    order = UserOrder.query.get_or_404(order_id)
    return render_template('order_accepted.html', order=order)


#(Support Ticket)

@app.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.id
            username = current_user.username
            email = current_user.email
        else:
            user_id = None
            username = request.form.get('name')
            email = request.form.get('email')
            if not username or not email:
                flash("Атыңызды және Email-іңізді енгізіңіз.", 'error')
                return redirect(url_for('support'))

        subject = request.form.get('subject')
        message = request.form.get('message')

        if not subject or not message:
             flash("Барлық өрістерді толтырыңыз.", 'error')
             return redirect(url_for('support'))

        try:
            db.session.rollback() 
            new_ticket = SupportTicket(
                user_id=user_id,
                username=username,
                email=email,
                subject=subject,
                message=message,
                status='Жаңа'
            )
            db.session.add(new_ticket)
            db.session.commit()
            flash("Сіздің сұрағыңыз қабылданды. Жауапты жақын арада Email арқылы аласыз!", 'success')
            return redirect(url_for('support'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Ticket submission error: {e}")
            flash("Сұрақ жіберу кезінде қате шықты. Қайталап көріңіз.", 'error')
            return redirect(url_for('support'))
            

    return render_template('support.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Имитациялық (Mock) AI чат жауаптарын өңдеу. 
    Бұл Gemini API-сінің жұмысын имитациялайды және көбірек сұрақтарға жауап береді.
    """
    data = request.json
    user_query = data.get('query', '').lower()
    
    if not user_query:
        return jsonify({'response': 'Сұрағыңызды енгізіңіз.'}), 400
    
    
    
    
    
    if 'сәлем' in user_query or 'здравствуйте' in user_query or 'хелло' in user_query:
        response_text = "Сәлеметсіз бе! Мен A|B тағам жеткізу қызметінің AI ассистентімін. Сізге қалай көмектесе аламын?"
    elif 'сау бол' in user_query or 'кош бол' in user_query:
        response_text = "Келіңіз, көріңіз, рахмет! Әрқашан қуаныштымыз. Күніңіз сәтті өтсін!"
    
    
    elif 'жеткізу' in user_query or 'уақыт' in user_query or 'қашан' in user_query:
        response_text = "Жеткізу уақыты әдетте тапсырыс берілген сәттен бастап 45-60 минут аралығын алады. Тапсырысты Жеке Кабинетте бақылай аласыз."

    
    elif 'тапсырыс беру' in user_query or 'қалай тапсырыс' in user_query or 'себет' in user_query:
        response_text = "Тапсырыс беру өте оңай: 1. Басты беттегі тағамдарды таңдап, Себетке қосыңыз. 2. Себет белгішесін басып, тапсырысты растау бетіне өтіңіз. 3. Мекенжайды енгізіп, төлем әдісін таңдаңыз."
        
    
    elif 'төлем' in user_query or 'төлеймін' in user_query or 'карта' in user_query:
        response_text = "Біз Картамен (онлайн төлем) және Қолма-қол ақшамен төлеуді қабылдаймыз. Төлем әдісін Тапсырысты Растау кезінде таңдай аласыз."
    
    
    elif 'тағам' in user_query or 'мәзір' in user_query or 'пицца' in user_query or 'суши' in user_query:
        response_text = "Біздің мәзірде суши сеттер, роллдар, пицца, бургерлер, ыстық тағамдар және тәттілер бар. Басты беттегі категориялар арқылы қажетті тағамды оңай таба аласыз."
        
    
    else:
        response_text = "Сіздің сұрағыңызды түсінбедім. Нақты ақпарат алу үшін біздің қолдау қызметіне (жоғарыдағы форма арқылы) хабарласыңыз."

    time.sleep(1)

    return jsonify({'response': response_text}), 200



# Бағдарламаны іске қосу

if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=5001)