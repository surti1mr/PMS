# Event Management System

A Flask-based web application for managing events, participants, and event managers with role-based access control.

## Features

- **Multi-role Authentication**: Admin, Event Manager, and Participant roles
- **Event Management**: Create, edit, and manage events
- **Event Registration**: Participants can register for events
- **User Dashboards**: Role-specific dashboards with statistics
- **RESTful API**: JSON API for integration with frontend applications
- **Session Management**: Secure session-based authentication
- **Database Integration**: MySQL database with SQLAlchemy ORM

## Project Structure

```
Project/
├── app.py                 # Main Flask application
├── models.py              # Database models (Admin, EventManager, Participant, Event, Registration)
├── auth.py                # Authentication utilities
├── api.py                 # REST API endpoints
├── config.py              # Configuration (uses environment variables)
├── database_schema.sql    # Database structure/schema file (MySQL)
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard_admin.html
│   ├── dashboard_event_manager.html
│   ├── dashboard_participant.html
│   └── ...
└── static/                # CSS and static files
    └── style.css
```

## Prerequisites

- Python 3.8 or higher
- MySQL database
- pip (Python package manager)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Create a Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your database credentials:
   ```
   SECRET_KEY=your-secret-key-here-change-this-in-production
   DB_HOST=your-db-host
   DB_PORT=3306
   DB_NAME=your-db-name
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   ```

3. If you don't have a `config.py` file, copy from the example:
   ```bash
   cp config.py.example config.py
   ```

### 5. Initialize the Database

You have two options to set up the database:

**Option A: Using the provided schema file (Recommended)**

1. Create your MySQL database:
   ```bash
   mysql -u your-db-user -p
   CREATE DATABASE your-db-name;
   EXIT;
   ```

2. Run the schema file to create all tables and default admin user:
   ```bash
   mysql -u your-db-user -p your-db-name < database_schema.sql
   ```

**Option B: Automatic table creation**

The application will automatically create tables on first run if they don't exist (using SQLAlchemy models).

**Note:** If using Option A, a default admin user is created automatically. See "Initial Setup & User Creation" section below.

### 6. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### 7. Initial Setup & User Creation

After setting up the database, follow these steps to get started:

**Step 1: Login as Default Admin**

If you used the database schema file (Option A), a default admin user is already created:

- **Email:** `admin@comedyorg.com`
- **Password:** `admin123`

⚠️ **Important:** Change this password after first login for security!

1. Navigate to `http://localhost:5000`
2. Click on "Login"
3. Enter the admin credentials above
4. You'll be redirected to the Admin Dashboard

**Step 2: Create Event Managers**

Once logged in as admin:

1. From the Admin Dashboard, navigate to "Event Managers" section
2. Click "Add New Event Manager"
3. Fill in the required details:
   - First Name, Last Name
   - Email (must be unique)
   - Phone Number (optional)
   - Password
4. Click "Create Event Manager"
5. The new event manager can now login and create events

**Step 3: Create Participants (Optional)**

Participants can be created in two ways:

**Option A: By Event Manager (Recommended)**
- Event Managers can create participant accounts from their dashboard
- Navigate to "Participants" section → "Add New Participant"

**Option B: Self-Registration**
- Participants can sign up themselves by clicking "Sign Up" on the login page
- They will need to provide their details and create an account

**Step 4: Create Events**

1. Login as an Event Manager (created in Step 2)
2. From the Event Manager Dashboard, click "Create Event"
3. Fill in event details:
   - Event Name, Description
   - Event Date and Time
   - Location
   - Total Spots Available
   - Registration Deadline
   - Event Type and Status
4. Click "Create Event"
5. Participants can now register for this event

**Step 5: Manage Registrations**

- Event Managers can view all registrations for their events
- They can approve, reject, or manage participant registrations
- Participants will see their registration status in their dashboard

**User Creation Workflow Summary:**
```
Admin (default) → Creates Event Managers → Event Managers create Events
                                                      ↓
                                    Participants register for Events
                                                      ↓
                                    Event Managers manage Registrations
```

## API Endpoints

### Authentication
- `POST /api/login` - User authentication
- `POST /api/logout` - User logout
- `GET /api/profile` - Get user profile

### Events
- `GET /api/events` - List all events
- `GET /api/events/<id>` - Get specific event details
- `POST /api/register/<event_id>` - Register for an event
- `GET /api/my-registrations` - Get user's registered events

### Health Check
- `GET /api/health` - Application health status

## User Roles

### Admin
- Manage all users (admins, event managers, participants)
- View system-wide statistics
- Full access to all features

### Event Manager
- Create and manage events
- View event registrations
- Manage assigned events

### Participant
- Browse events
- Register for events
- View registered events
- Manage profile

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- SQL injection protection via SQLAlchemy
- Environment variable configuration for sensitive data
- Role-based access control

## Dependencies

- **Flask** (2.3.3) - Web framework
- **Flask-SQLAlchemy** (3.1.1) - Database ORM
- **SQLAlchemy** (2.0.23) - SQL toolkit
- **PyMySQL** (1.1.0) - MySQL database connector
- **Werkzeug** (2.3.7) - WSGI utilities (password hashing)
- **python-dotenv** (1.0.0) - Environment variable management
- **requests** (2.32.5) - HTTP library

## Development

### Running Tests

Test files are available in the project:
- `test_connection.py` - Database connection test
- `test_login_final.py` - Login functionality test
- `test_api.py` - API endpoint tests

### Project Configuration

The application uses environment variables for configuration. Make sure to:
- Never commit `.env` file to version control
- Use `config.py.example` as a template
- Keep `SECRET_KEY` secure and change it in production

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Support

For issues and questions, please open an issue on the GitHub repository.

