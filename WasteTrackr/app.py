import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from models import db, WasteLoad, Organization

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the PostgreSQL database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Configure file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def prepare_chart_data(waste_loads):
    """Prepare data for charts"""
    try:
        # Count by waste type
        waste_type_counts = {}
        material_category_counts = {}
        destination_counts = {}
        weight_by_type = {}
        weight_by_destination = {}
        
        for load in waste_loads:
            # Waste type counts
            waste_type_counts[load.waste_type] = waste_type_counts.get(load.waste_type, 0) + 1
            
            # Material category counts
            material_category_counts[load.material_category] = material_category_counts.get(load.material_category, 0) + 1
            
            # Destination counts
            destination_counts[load.destination] = destination_counts.get(load.destination, 0) + 1
            
            # Weight by waste type
            weight_by_type[load.waste_type] = weight_by_type.get(load.waste_type, 0) + load.waste_weight
            
            # Weight by destination
            weight_by_destination[load.destination] = weight_by_destination.get(load.destination, 0) + load.waste_weight
        
        return {
            'waste_type_counts': waste_type_counts,
            'material_category_counts': material_category_counts,
            'destination_counts': destination_counts,
            'weight_by_type': weight_by_type,
            'weight_by_destination': weight_by_destination
        }
    except Exception as e:
        logging.error(f"Error preparing chart data: {e}")
        return {}

def create_tables():
    """Create database tables if they don't exist"""
    try:
        with app.app_context():
            db.create_all()
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")

def save_waste_load(data):
    """Save waste load data to database"""
    try:
        # Parse datetime string
        datetime_obj = datetime.strptime(data['datetime'], '%Y-%m-%dT%H:%M')
        
        waste_load = WasteLoad()
        waste_load.vehicle_number = data['vehicle_number']
        waste_load.datetime = datetime_obj
        waste_load.waste_weight = float(data['waste_weight'])
        waste_load.waste_type = data['waste_type']
        waste_load.material_category = data['material_category']
        waste_load.destination = data['destination']
        waste_load.panchayath = data.get('panchayath', '')
        
        db.session.add(waste_load)
        db.session.commit()
        return True
    except Exception as e:
        logging.error(f"Error saving to database: {e}")
        db.session.rollback()
        return False

@app.route('/')
def index():
    """Main page with waste logging form"""
    organization = Organization.get_current()
    return render_template('index.html', organization=organization)

@app.route('/organization')
def organization_info():
    """Organization setup page"""
    organization = Organization.get_current()
    return render_template('organization.html', organization=organization)

@app.route('/organization', methods=['POST'])
def save_organization():
    """Save organization information"""
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Organization name is required.', 'error')
            return redirect(url_for('organization_info'))
        
        # Handle logo upload
        logo_filename = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                logo_filename = filename
        
        # Get or create organization record
        organization = Organization.get_current()
        if organization:
            organization.name = name
            organization.description = description
            if logo_filename:
                # Delete old logo file if exists
                if organization.logo_filename:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], organization.logo_filename)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                organization.logo_filename = logo_filename
        else:
            organization = Organization()
            organization.name = name
            organization.description = description
            organization.logo_filename = logo_filename
            db.session.add(organization)
        
        db.session.commit()
        flash('Organization information saved successfully!', 'success')
        
    except Exception as e:
        logging.error(f"Error saving organization: {e}")
        db.session.rollback()
        flash('Error saving organization information. Please try again.', 'error')
    
    return redirect(url_for('organization_info'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/submit', methods=['POST'])
def submit_waste_log():
    """Handle form submission for waste logging"""
    try:
        # Get form data
        vehicle_number = request.form.get('vehicle_number', '').strip()
        datetime_str = request.form.get('datetime', '').strip()
        waste_weight = request.form.get('waste_weight', '').strip()
        waste_type = request.form.get('waste_type', '').strip()
        material_category = request.form.get('material_category', '').strip()
        destination = request.form.get('destination', '').strip()
        panchayath = request.form.get('panchayath', '').strip()
        
        # Validate required fields
        if not all([vehicle_number, datetime_str, waste_weight, waste_type, material_category, destination]):
            flash('All fields are required. Please fill in all information.', 'error')
            return redirect(url_for('index'))
        
        # Validate weight is a positive number
        try:
            weight_float = float(waste_weight)
            if weight_float <= 0:
                raise ValueError("Weight must be positive")
        except ValueError:
            flash('Waste weight must be a valid positive number.', 'error')
            return redirect(url_for('index'))
        
        # Prepare data for CSV
        waste_data = {
            'vehicle_number': vehicle_number,
            'datetime': datetime_str,
            'waste_weight': waste_weight,
            'waste_type': waste_type,
            'material_category': material_category,
            'destination': destination,
            'panchayath': panchayath
        }
        
        # Save to database
        if save_waste_load(waste_data):
            flash('Waste load logged successfully!', 'success')
            logging.info(f"Waste load logged: Vehicle {vehicle_number}")
        else:
            flash('Error saving waste load. Please try again.', 'error')
            
    except Exception as e:
        logging.error(f"Error processing form submission: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/report')
def report():
    """Display all logged waste entries with optional filtering"""
    try:
        organization = Organization.get_current()
        
        # Get filter parameters
        filters = {}
        
        vehicle_number = request.args.get('vehicle_number')
        if vehicle_number:
            filters['vehicle_number'] = vehicle_number
            
        date_from = request.args.get('date_from')
        if date_from:
            try:
                filters['date_from'] = datetime.strptime(date_from, '%Y-%m-%d')
            except ValueError:
                pass
                
        date_to = request.args.get('date_to')
        if date_to:
            try:
                filters['date_to'] = datetime.strptime(date_to, '%Y-%m-%d')
            except ValueError:
                pass
                
        weight_min = request.args.get('weight_min')
        if weight_min:
            try:
                filters['weight_min'] = float(weight_min)
            except ValueError:
                pass
                
        weight_max = request.args.get('weight_max')
        if weight_max:
            try:
                filters['weight_max'] = float(weight_max)
            except ValueError:
                pass
                
        waste_type = request.args.get('waste_type')
        if waste_type:
            filters['waste_type'] = waste_type
            
        material_category = request.args.get('material_category')
        if material_category:
            filters['material_category'] = material_category
            
        destination = request.args.get('destination')
        if destination:
            filters['destination'] = destination
            
        panchayath = request.args.get('panchayath')
        if panchayath:
            filters['panchayath'] = panchayath
        
        # Get filtered or all data
        if filters:
            waste_loads = WasteLoad.search_and_filter(filters)
        else:
            waste_loads = WasteLoad.get_all_ordered()
        
        stats = WasteLoad.get_summary_stats()
        
        # Convert to format expected by template
        waste_logs = []
        for load in waste_loads:
            waste_logs.append({
                'Vehicle Number': load.vehicle_number,
                'Date & Time': load.datetime.strftime('%Y-%m-%dT%H:%M'),
                'Waste Weight (kg)': str(load.waste_weight),
                'Waste Type': load.waste_type,
                'Material Category': load.material_category,
                'Destination': load.destination,
                'Panchayath': load.panchayath or ''
            })
        
        # Prepare chart data
        chart_data = prepare_chart_data(waste_loads)
        
        # Get unique values for filter dropdowns
        all_loads = WasteLoad.get_all_ordered()
        filter_options = {
            'waste_types': list(set([load.waste_type for load in all_loads])),
            'material_categories': list(set([load.material_category for load in all_loads])),
            'destinations': list(set([load.destination for load in all_loads])),
            'panchayaths': list(set([load.panchayath for load in all_loads if load.panchayath]))
        }
            
        return render_template('report.html', 
                             waste_logs=waste_logs, 
                             stats=stats, 
                             organization=organization,
                             chart_data=chart_data,
                             filter_options=filter_options,
                             current_filters=request.args)
        
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        flash('Error loading report data.', 'error')
        return render_template('report.html', 
                             waste_logs=[], 
                             stats={}, 
                             organization=Organization.get_current(),
                             chart_data={},
                             filter_options={},
                             current_filters={})

@app.route('/api/waste-loads', methods=['GET'])
def api_get_waste_loads():
    """API endpoint to get all waste loads"""
    try:
        waste_loads = WasteLoad.get_all_ordered()
        return jsonify([load.to_dict() for load in waste_loads])
    except Exception as e:
        logging.error(f"Error fetching waste loads: {e}")
        return jsonify({'error': 'Failed to fetch waste loads'}), 500

@app.route('/api/waste-loads', methods=['POST'])
def api_create_waste_load():
    """API endpoint to create a new waste load"""
    try:
        data = request.get_json()
        
        if save_waste_load(data):
            return jsonify({'success': True, 'message': 'Waste load saved successfully'})
        else:
            return jsonify({'error': 'Failed to save waste load'}), 500
            
    except Exception as e:
        logging.error(f"Error creating waste load via API: {e}")
        return jsonify({'error': 'Invalid request data'}), 400

@app.route('/export/csv')
def export_csv():
    """Export waste loads as CSV"""
    try:
        import csv
        import io
        from flask import make_response
        
        waste_loads = WasteLoad.get_all_ordered()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Vehicle Number', 'Date & Time', 'Waste Weight (kg)', 
                        'Waste Type', 'Material Category', 'Destination', 'Created At'])
        
        # Write data
        for load in waste_loads:
            writer.writerow([
                load.vehicle_number,
                load.datetime.strftime('%Y-%m-%d %H:%M'),
                load.waste_weight,
                load.waste_type,
                load.material_category,
                load.destination,
                load.created_at.strftime('%Y-%m-%d %H:%M') if load.created_at else ''
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=waste_loads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logging.error(f"Error exporting CSV: {e}")
        flash('Error exporting data.', 'error')
        return redirect(url_for('report'))

# Initialize database on startup
create_tables()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
