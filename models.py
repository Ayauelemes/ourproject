from extentions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship 
from sqlalchemy import func, UniqueConstraint, event, PrimaryKeyConstraint 

# 🛑 МӘЗІР ТІЗІМІ: Енді бұл тізім models.py-да тұрады және app.py-да қолданылады.
FOOD_ITEMS = [
    { "id": 1, "name": "Сет 1", "description": "Классикалық суши сеті.", "price": 9500, "image_url": "images/set1.jpeg", "category": "Сеттер" }, 
    { "id": 2, "name": "Сет 2", "description": "Жапондық ең танымал роллдар.", "price": 10500, "image_url": "images/set2.jpeg", "category": "Сеттер" },
    { "id": 3, "name": "Сет 3", "description": "Жаңа әртүрлі сет.", "price": 11900, "image_url": "images/set3.jpeg", "category": "Сеттер" },
    { "id": 4, "name": "Сет 4", "description": "Ерекше дәмді сет.", "price": 9900, "image_url": "images/set4.jpeg", "category": "Сеттер" },
    { "id": 5, "name": "Сет 5", "description": "Үлкен компанияға арналған.", "price": 8900, "image_url": "images/set5.jpeg", "category": "Сеттер" },
    { "id": 6, "name": "Сет 6", "description": "Тойымды сет", "price": 8600, "image_url": "images/set6.jpeg", "category": "Сеттер" },
    { "id": 7, "name": "Сет 7", "description": "Қытырлақ роллдар жиынтығы.", "price": 10900, "image_url": "images/set7.jpeg", "category": "Сеттер" },
    { "id": 8, "name": "Сет 8", "description": "Крем ірімшігі бар сет.", "price": 12900, "image_url": "images/set8.jpeg", "category": "Сеттер" },
    
    { "id": 9, "name": "Филадельфия ролл", "description": "", "price": 3600, "image_url": "images/roll1.jpeg", "category": "Роллдар" },
    { "id": 10, "name": "Канада", "description": "", "price": 3400, "image_url": "images/roll2.jpeg", "category": "Роллдар" },
    { "id": 11, "name": "Калифорния", "description": "", "price": 2400, "image_url": "images/roll3.jpeg", "category": "Роллдар" },
    { "id": 12, "name": "Пісірілген ролл", "description": "", "price": 2900, "image_url": "images/roll4.jpeg", "category": "Роллдар" },
    { "id": 13, "name": "Қуырылған ролл", "description": "", "price": 2800, "image_url": "images/roll5.jpeg", "category": "Роллдар" },
    { "id": 14, "name": "Сакура", "description": "", "price": 3200, "image_url": "images/roll6.jpeg", "category": "Роллдар" },
    { "id": 15, "name": "Қызыл Айдахар", "description": "", "price": 3900, "image_url": "images/roll7.jpeg", "category": "Роллдар" },
    { "id": 16, "name": "Пісірілген Канада", "description": "", "price": 3500, "image_url": "images/roll8.jpeg", "category": "Роллдар" },
    
    { "id": 17, "name": "Пепперони", "description": "", "price": 3300, "image_url": "images/pizza1.jpeg", "category": "Пицца" },
    { "id": 18, "name": "Маргарита", "description": "", "price": 2900, "image_url": "images/pizza2.jpeg", "category": "Пицца" },
    { "id": 19, "name": "Төрт маусым", "description": "", "price": 3600, "image_url": "images/pizza3.jpeg", "category": "Пицца" },
    { "id": 20, "name": "Ірімшікті пицца", "description": "", "price": 3200, "image_url": "images/pizza4.jpeg", "category": "Пицца" },
    { "id": 21, "name": "Қаймақ соусындағы тауық еті", "description": "", "price": 3300, "image_url": "images/pizza5.jpeg", "category": "Пицца" },
    { "id": 22, "name": "Саңырауқұлақ қосылған тауық еті", "description": "", "price": 3300, "image_url": "images/pizza6.jpeg", "category": "Пицца" },
    
    { "id": 23, "name": "Классикалық рамен", "description": "", "price": 2700, "image_url": "images/ramen1.jpeg", "category": "Рамен" },
    { "id": 24, "name": "Ірімшікті рамен", "description": "", "price": 3300, "image_url": "images/ramen2.jpeg", "category": "Рамен" },
    { "id": 25, "name": "Ысталған ет қосылған рамен", "description": "", "price": 3400, "image_url": "images/ramen3.jpeg", "category": "Рамен" },
    
    { "id": 26, "name": "Сиыр етінен жасалған бургер", "description": "", "price": 1600, "image_url": "images/burger1.jpeg", "category": "Бургерлер" },
    { "id": 27, "name": "Тауық етінен жасалған бургер", "description": "", "price": 1400, "image_url": "images/burger2.jpeg", "category": "Бургерлер" },
    { "id": 28, "name": "Ірімшікті сиыр еті бургері", "description": "", "price": 1800, "image_url": "images/burger3.jpeg", "category": "Бургерлер" },
    { "id": 29, "name": "Ірімшікті тауық бургері", "description": "", "price": 1600, "image_url": "images/burger4.jpeg", "category": "Бургерлер" },
    { "id": 30, "name": "Микс бургер 2 еселенген", "description": "", "price": 2000, "image_url": "images/burger5.jpeg", "category": "Бургерлер" },
    { "id": 31, "name": "2 еселенген микс чизбургер", "description": "", "price": 2200, "image_url": "images/burger6.jpeg", "category": "Бургерлер" },
    
    { "id": 32, "name": "Кетчуп", "description": "", "price": 300, "image_url": "images/sous1.jpeg", "category": "Соустар" },
    { "id": 33, "name": "Ірімшікті соус", "description": "", "price": 300, "image_url": "images/sous2.jpeg", "category": "Соустар" },
    { "id": 34, "name": "Майонез", "description": "", "price": 300, "image_url": "images/sous3.jpeg", "category": "Соустар" },
    { "id": 35, "name": "Барбекю", "description": "", "price": 300, "image_url": "images/sous4.jpeg", "category": "Соустар" },
    { "id": 36, "name": "Саңырауқұлақ соусы", "description": "", "price": 300, "image_url": "images/sous5.jpeg", "category": "Соустар" },
    
    { "id": 37, "name": "Тайша тауық еті", "description": "", "price": 3000, "image_url": "images/meat1.jpeg", "category": "Ыстық тамақтар" },
    { "id": 38, "name": "Тайша асшаяндар", "description": "", "price": 3700, "image_url": "images/meat2.jpeg", "category": "Ыстық тамақтар" },
    { "id": 39, "name": "Қуырылған күріш", "description": "", "price": 2700, "image_url": "images/meat3.jpeg", "category": "Ыстық тамақтар" },
    { "id": 40, "name": "Тауық еті және саңырауқұлақ қосылған феттучини", "description": "", "price": 3500, "image_url": "images/meat4.jpeg", "category": "Ыстық тамақтар" },
    { "id": 41, "name": "Тауық сорпасы", "description": "", "price": 2000, "image_url": "images/meat5.jpeg", "category": "Ыстық тамақтар" },
    { "id": 42, "name": "Бефстроганов", "description": "", "price": 3500, "image_url": "images/meat6.jpeg", "category": "Ыстық тамақтар" },
    { "id": 43, "name": "Қаймақ соусындағы тауық төс еті және саңырауқұлақ", "description": "", "price": 3000, "image_url": "images/meat7.jpeg", "category": "Ыстық тамақтар" },
    { "id": 44, "name": "Фитнес түскі ас", "description": "", "price": 2900, "image_url": "images/meat8.jpeg", "category": "Ыстық тамақтар" },
    
    { "id": 45, "name": "Цезарь салаты", "description": "", "price": 3100, "image_url": "images/salad1.jpeg", "category": "Салаттар" },
    { "id": 46, "name": "Малибу салаты", "description": "", "price": 2500, "image_url": "images/salad2.jpeg", "category": "Салаттар" },
    { "id": 47, "name": "Қытырлақ баклажан және тауық еті қосылған салат", "description": "", "price": 3000, "image_url": "images/salad3.jpeg", "category": "Салаттар" },
    { "id": 48, "name": "Грек салаты", "description": "", "price": 2700, "image_url": "images/salad4.jpeg", "category": "Салаттар" },
    { "id": 49, "name": "Үй салаты", "description": "", "price": 2100, "image_url": "images/salad5.jpeg", "category": "Салаттар" },
    
    { "id": 50, "name": "Норвегиялық таңғы ас", "description": "", "price": 3500, "image_url": "images/break1.jpeg", "category": "Таңғы астар" },
    { "id": 51, "name": "Түрік таңғы асы", "description": "", "price": 3100, "image_url": "images/break2.jpeg", "category": "Таңғы астар" },
    { "id": 52, "name": "Ауылдық таңғы ас", "description": "", "price": 3200, "image_url": "images/break3.jpeg", "category": "Таңғы астар" },
    { "id": 53, "name": "Жарма ботқасы", "description": "", "price": 900, "image_url": "images/break4.jpeg", "category": "Таңғы астар" },
    { "id": 54, "name": "Қуырылған жұмыртқа", "description": "", "price": 700, "image_url": "images/break5.jpeg", "category": "Таңғы астар" },
    
    { "id": 55, "name": "Сүтті фисташка коктейлі", "description": "", "price": 1990, "image_url": "images/drink1.jpeg", "category": "Сусындар" },
    { "id": 56, "name": "Орео печеньесі қосылған сүтті коктейль", "description": "", "price": 1990, "image_url": "images/drink2.jpeg", "category": "Сусындар" },
    { "id": 57, "name": "Классикалық сүтті коктейль", "description": "", "price": 1700, "image_url": "images/drink3.jpeg", "category": "Сусындар" },
    { "id": 58, "name": "Шоколадты сүтті коктейль", "description": "", "price": 1990, "image_url": "images/drink4.jpeg", "category": "Сусындар" },
    { "id": 59, "name": "Coca-Cola", "description": "", "price": 700, "image_url": "images/drink5.jpeg", "category": "Сусындар" },
    { "id": 60, "name": "Coca-Cola Zero", "description": "", "price": 700, "image_url": "images/drink6.jpeg", "category": "Сусындар" },
    { "id": 61, "name": "Sprite", "description": "", "price": 700, "image_url": "images/drink7.jpeg", "category": "Сусындар" },
    { "id": 62, "name": "Құлпынай мен Қауын дәмі бар Fuse Tea", "description": "", "price": 800, "image_url": "images/drink8.jpeg", "category": "Сусындар" },
    { "id": 63, "name": "Шабдалы дәмі бар Fuse Tea", "description": "", "price": 800, "image_url": "images/drink9.jpeg", "category": "Сусындар" },
    
    { "id": 64, "name": "Сүтті қыз торты (кіші)","description":"", "price": 6800, "image_url": "images/cakes1.jpeg", "category": "Тәттілер" },
    { "id": 65, "name": "Сникерс торты (кіші)","description":"", "price": 6800, "image_url": "images/cakes2.jpeg", "category": "Тәттілер" },
    { "id": 66, "name": "Шпинатты торт (кіші)","description":"", "price": 6800, "image_url": "images/cakes3.jpeg", "category": "Тәттілер" },
    { "id": 67, "name": "Наполеон торты","description":"", "price": 7800, "image_url": "images/cakes4.jpeg", "category": "Тәттілер" },
    { "id": 68, "name": "Баноффи Пай","description":"", "price": 4000, "image_url": "images/cakes5.jpeg", "category": "Тәттілер" },
    { "id": 69, "name": "Жидек-сүзбелі (таңқурай) десерт","description":"", "price": 4500, "image_url": "images/cakes6.jpeg", "category": "Тәттілер" },
]


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    orders = relationship('UserOrder', backref='customer', lazy='dynamic') 
    # 🛑 Many:Many қатынасы үшін байланыс
    favorite_items = relationship('FavoriteItem', backref='user', lazy='dynamic', cascade="all, delete-orphan")


    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# 🛑 ЖАҢА АРАЛЫҚ КЕСТЕ: Many:Many (User ↔ FoodItem)
# Бұл кесте тек пайдаланушының сүйікті тағамдарының ID-терін сақтайды.
class FavoriteItem(db.Model):
    __tablename__ = 'favorite_items'
    
    # Біріккен бастапқы кілт - екі кілттің қосындысы
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # food_item_id - FoodItem кестесі жоқ болғандықтан, тек ID-ні сақтаймыз
    food_item_id = db.Column(db.Integer, nullable=False) 
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'food_item_id', name='pk_favorite_items'),
    )

    def __repr__(self):
        return f'<FavoriteItem User:{self.user_id} | Food:{self.food_item_id}>'


# 1-ші КЕСТЕ: Тапсырыстың Жалпы Кестесі
class UserOrder(db.Model):
    __tablename__ = 'user_orders'
    id = db.Column(db.Integer, primary_key=True) 
    total_price = db.Column(db.Float, nullable=False) 
    delivery_address = db.Column(db.String(256), nullable=False, default='Көрсетілмеген')
    order_status = db.Column(db.String(50), default='Жаңа', nullable=False) 
    payment_method = db.Column(db.String(50), nullable=False, default='Картамен')
    timestamp = db.Column(db.DateTime, default=func.now()) 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    items = relationship('OrderInfo', backref='user_order', lazy='dynamic', cascade="all, delete-orphan") 
    payment_details = relationship('PaymentInfo', backref='order', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<UserOrder {self.id} | Status: {self.order_status}>'

# 2-ші КЕСТЕ: Тапсырыс Элементтерінің Кестесі
class OrderInfo(db.Model):
    __tablename__ = 'order_info'
    id = db.Column(db.Integer, primary_key=True) 
    item_name = db.Column(db.String(100), nullable=False) 
    item_price = db.Column(db.Float, nullable=False) 
    quantity = db.Column(db.Integer, default=1, nullable=False) 
    
    order_id = db.Column(db.Integer, db.ForeignKey('user_orders.id'), nullable=False) 

    @property
    def subtotal(self):
        return self.item_price * self.quantity

    def __repr__(self):
        return f'<OrderInfo {self.id}: {self.item_name} x {self.quantity}>'

# 3-ші КЕСТЕ: Төлем деректерін сақтау
class PaymentInfo(db.Model):
    __tablename__ = 'payment_info'
    id = db.Column(db.Integer, primary_key=True)
    
    card_ending = db.Column(db.String(4), nullable=False)
    card_holder = db.Column(db.String(100), nullable=False)
    bank_name = db.Column(db.String(50), nullable=True) 
    
    order_id = db.Column(db.Integer, db.ForeignKey('user_orders.id'), unique=True, nullable=False)
    
    __table_args__ = (UniqueConstraint('order_id', name='_order_id_uc'),) 
    
    def __repr__(self):
        return f'<PaymentInfo {self.id} | Ends: ****{self.card_ending}>'

# 4-ші КЕСТЕ: Қолдау билеттері
class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    username = db.Column(db.String(64), nullable=True) 
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Жаңа', nullable=False) 
    timestamp = db.Column(db.DateTime, default=func.now())

    requester = relationship('User', backref='tickets', foreign_keys=[user_id])

    def __repr__(self):
        return f'<Ticket {self.id} | Subject: {self.subject} | Status: {self.status}>'