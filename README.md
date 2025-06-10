# MRF Waste Logger

A comprehensive digital record-keeping and reporting system for Material Recovery Facilities (MRF) to track waste loads, manage organization information, and generate detailed reports with visualizations.

## Features

### Core Functionality
- **Waste Load Logging**: Log incoming waste loads with vehicle details, weight, type, material category, and destination
- **Organization Management**: Setup organization information with logo upload and branding
- **Interactive Reports**: View data with charts and statistics, export to CSV
- **Database Storage**: PostgreSQL database for reliable data persistence
- **Offline Support**: localStorage backup with automatic sync when online
- **Responsive Design**: Bootstrap-based UI that works on desktop and mobile

### Technical Features
- **REST API**: JSON endpoints for external integrations
- **File Upload**: Secure logo upload with validation
- **Data Visualization**: Chart.js integration for pie charts, bar charts, and doughnut charts
- **Form Validation**: Client-side and server-side validation
- **Real-time Statistics**: Live calculation of totals, weights, and counts

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database (automatically configured in Replit)

### Installation

1. **Clone or run in Replit**
   ```bash
   # The application is ready to run in Replit
   # All dependencies are automatically managed
   ```

2. **Database Setup**
   - PostgreSQL database is automatically created in Replit
   - Tables are created automatically on first run

3. **Start the Application**
   ```bash
   # In Replit, click the "Run" button or use:
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

4. **Access the Application**
   - Open the web view in Replit
   - Navigate to the organization setup page first to configure your facility

## Usage Guide

### Initial Setup
1. **Organization Configuration**
   - Go to "Organization" in the navigation menu
   - Enter your facility name and description
   - Upload your organization logo
   - Save the configuration

2. **Start Logging Waste Loads**
   - Use the main form to log incoming waste
   - All fields are required for complete records
   - Date and time are auto-filled but can be adjusted

3. **View Reports and Analytics**
   - Access the "View Reports" page for comprehensive analytics
   - Export data as CSV for external analysis
   - Interactive charts show waste distribution and trends

### Data Fields

#### Waste Load Entry
- **Vehicle Number**: License plate or identification
- **Date & Time**: Timestamp of waste arrival
- **Waste Weight**: Weight in kilograms
- **Waste Type**: Mixed, Dry, or Wet
- **Material Category**: Plastic, Glass, Rubber, MLP
- **Destination**: Recycler, Landfill, or Cement Factory

#### Organization Information
- **Name**: Full facility name
- **Description**: Mission and operational details
- **Logo**: Organization branding image

## API Documentation

### Endpoints

#### Get All Waste Loads
```http
GET /api/waste-loads
Content-Type: application/json
```

#### Create Waste Load
```http
POST /api/waste-loads
Content-Type: application/json

{
  "vehicle_number": "KA-00-AA-0000",
  "datetime": "2024-01-15T14:30",
  "waste_weight": "1500.5",
  "waste_type": "Mixed",
  "material_category": "Plastic",
  "destination": "Recycler"
}
```

#### Export Data
```http
GET /export/csv
```

## File Structure

```
├── app.py              # Main Flask application
├── models.py           # Database models
├── main.py             # Application entry point
├── templates/          # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── index.html      # Waste logging form
│   ├── report.html     # Reports and analytics
│   └── organization.html # Organization setup
├── static/
│   ├── css/
│   │   └── custom.css  # Custom styles
│   ├── js/
│   │   └── app.js      # Client-side functionality
│   └── uploads/        # Organization logo storage
└── README.md           # This file
```

## Database Schema

### waste_loads Table
- `id`: Primary key
- `vehicle_number`: Vehicle identification
- `datetime`: Waste arrival timestamp
- `waste_weight`: Weight in kg
- `waste_type`: Type classification
- `material_category`: Material type
- `destination`: Processing destination
- `created_at`: Record creation time

### organization Table
- `id`: Primary key
- `name`: Organization name
- `description`: About information
- `logo_filename`: Logo file reference
- `created_at`: Creation timestamp
- `updated_at`: Last modification time

## Customization

### Adding New Waste Types
Edit the dropdown options in `templates/index.html`:
```html
<option value="NewType">New Type</option>
```

### Styling Changes
Modify `static/css/custom.css` for visual customizations while maintaining Bootstrap compatibility.

### Chart Modifications
Update chart configurations in `templates/report.html` to change colors, types, or data presentation.

## Security Features

- Input validation and sanitization
- Secure file upload with type restrictions
- SQL injection prevention through ORM
- XSS protection in templates

## Deployment

### Local Development
```bash
python main.py
# Access at http://localhost:5000
```

### Production Deployment
- Configure environment variables for database connection
- Set proper secret keys for security
- Use production WSGI server (already configured with Gunicorn)

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running and DATABASE_URL is set
2. **File Uploads**: Check upload directory permissions
3. **Charts Not Loading**: Verify Chart.js CDN connectivity

### Logs
Check application logs for detailed error information:
```bash
# Logs are displayed in the Replit console
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper testing
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Verify database connectivity
- Ensure all required fields are properly filled

---

**Built for Material Recovery Facilities to streamline waste tracking and reporting operations.**