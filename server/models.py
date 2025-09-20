from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy

class SerializerMixin:
    def to_dict(self, only=None, rules=None):
        result = {}
        for column in self.__table__.columns:
            if only and column.name not in only:
                continue
            result[column.name] = getattr(self, column.name)
        
        # Handle relationships if not restricted by 'only'
        if not only:
            for relationship in self.__mapper__.relationships:
                if hasattr(self, relationship.key):
                    related_obj = getattr(self, relationship.key)
                    if related_obj is not None:
                        if isinstance(related_obj, list):
                            result[relationship.key] = [obj.to_dict(only=('id', 'name', 'ingredients') if relationship.key == 'pizza' else ('id', 'name', 'address') if relationship.key == 'restaurant' else None) if hasattr(obj, 'to_dict') else str(obj) for obj in related_obj]
                        else:
                            if relationship.key == 'pizza':
                                result[relationship.key] = related_obj.to_dict(only=('id', 'name', 'ingredients'))
                            elif relationship.key == 'restaurant':
                                result[relationship.key] = related_obj.to_dict(only=('id', 'name', 'address'))
                            else:
                                result[relationship.key] = related_obj.to_dict() if hasattr(related_obj, 'to_dict') else str(related_obj)
        return result

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)


class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)

    # add relationship
    restaurant_pizzas = db.relationship('RestaurantPizza', back_populates='restaurant', cascade='all, delete-orphan')
    pizzas = association_proxy('restaurant_pizzas', 'pizza')

    # add serialization rules
    serialize_rules = ('-restaurant_pizzas.restaurant',)

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ingredients = db.Column(db.String)

    # add relationship
    restaurant_pizzas = db.relationship('RestaurantPizza', back_populates='pizza', cascade='all, delete-orphan')
    restaurants = association_proxy('restaurant_pizzas', 'restaurant')

    # add serialization rules
    serialize_rules = ('-restaurant_pizzas.pizza',)

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"


class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id'), nullable=False)

    # add relationships
    restaurant = db.relationship('Restaurant', back_populates='restaurant_pizzas')
    pizza = db.relationship('Pizza', back_populates='restaurant_pizzas')

    # add serialization rules
    serialize_rules = ('-restaurant.restaurant_pizzas', '-pizza.restaurant_pizzas')

    # add validation
    @validates('price')
    def validate_price(self, key, price):
        if not (1 <= price <= 30):
            raise ValueError("Price must be between 1 and 30")
        return price

    def __repr__(self):
        return f"<RestaurantPizza ${self.price}>"
