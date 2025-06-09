from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Organization(db.Model):
    __tablename__ = 'organization'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    logo_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Organization {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'logo_filename': self.logo_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_current(cls):
        """Get the current organization (assumes single organization setup)"""
        return cls.query.first()

class WasteLoad(db.Model):
    __tablename__ = 'waste_loads'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False, index=True)
    datetime = db.Column(db.DateTime, nullable=False, index=True)
    waste_weight = db.Column(db.Float, nullable=False)
    waste_type = db.Column(db.String(20), nullable=False)
    material_category = db.Column(db.String(50), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    panchayath = db.Column(db.String(100), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f'<WasteLoad {self.vehicle_number} - {self.waste_weight}kg>'
    
    def to_dict(self):
        """Convert model instance to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'vehicle_number': self.vehicle_number,
            'datetime': self.datetime.strftime('%Y-%m-%dT%H:%M'),
            'waste_weight': self.waste_weight,
            'waste_type': self.waste_type,
            'material_category': self.material_category,
            'destination': self.destination,
            'panchayath': self.panchayath,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_summary_stats(cls):
        """Get summary statistics for all waste loads"""
        from sqlalchemy import func
        
        total_loads = db.session.query(func.count(cls.id)).scalar() or 0
        total_weight = db.session.query(func.sum(cls.waste_weight)).scalar() or 0.0
        unique_vehicles = db.session.query(func.count(func.distinct(cls.vehicle_number))).scalar() or 0
        unique_waste_types = db.session.query(func.count(func.distinct(cls.waste_type))).scalar() or 0
        
        return {
            'total_loads': total_loads,
            'total_weight': float(total_weight),
            'unique_vehicles': unique_vehicles,
            'unique_waste_types': unique_waste_types
        }
    
    @classmethod
    def get_all_ordered(cls):
        """Get all waste loads ordered by datetime descending"""
        return cls.query.order_by(cls.datetime.desc()).all()
    
    @classmethod
    def search_and_filter(cls, filters):
        """Search and filter waste loads based on criteria"""
        query = cls.query
        
        # Vehicle number search
        if filters.get('vehicle_number'):
            query = query.filter(cls.vehicle_number.ilike(f"%{filters['vehicle_number']}%"))
        
        # Date range filtering
        if filters.get('date_from'):
            query = query.filter(cls.datetime >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(cls.datetime <= filters['date_to'])
        
        # Weight range filtering
        if filters.get('weight_min'):
            query = query.filter(cls.waste_weight >= filters['weight_min'])
        if filters.get('weight_max'):
            query = query.filter(cls.waste_weight <= filters['weight_max'])
        
        # Category filters
        if filters.get('waste_type'):
            query = query.filter(cls.waste_type == filters['waste_type'])
        if filters.get('material_category'):
            query = query.filter(cls.material_category == filters['material_category'])
        if filters.get('destination'):
            query = query.filter(cls.destination == filters['destination'])
        if filters.get('panchayath'):
            query = query.filter(cls.panchayath.ilike(f"%{filters['panchayath']}%"))
        
        return query.order_by(cls.datetime.desc()).all()