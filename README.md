# DucksFinances - Bookkeeping for Small IT Businesses

DucksFinances is a modern, user-friendly bookkeeping application designed specifically for small IT businesses with 1-5 employees. It simplifies financial management with an intuitive interface and powerful features.

## Features

- **Income & Expense Tracking**: Keep track of all financial transactions
- **Invoicing**: Create and manage professional invoices
- **Financial Reports**: Generate detailed financial reports
- **Multi-currency Support**: Work with multiple currencies
- **Client Management**: Manage client information and history
- **Project Tracking**: Track time and expenses by project
- **Tax Preparation**: Prepare for tax season with organized financial data
- **User Access Control**: Role-based access control for team members
- **Data Export**: Export data in CSV/PDF formats

## Tech Stack

### Backend
- **Framework**: Python 3.9+, Flask
- **Database**: PostgreSQL / SQLite (for development)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **API**: RESTful API
- **Testing**: pytest

### Frontend (Coming Soon)
- **Framework**: React 18, TypeScript
- **UI Library**: Material-UI
- **State Management**: Redux Toolkit
- **Form Handling**: Formik & Yup

### Deployment
- **Containerization**: Docker
- **Web Server**: Nginx
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher (for frontend development)
- PostgreSQL 13 or higher (SQLite for development)
- pip (Python package manager)
- virtualenv (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ducksfinances.git
   cd ducksfinances
   ```

2. **Set up the backend**
   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   # source venv/bin/activate

   # Install dependencies
   cd backend
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Initialize the database
   flask db upgrade
   ```

3. **Set up the frontend (coming soon)**
   ```bash
   cd ../frontend
   npm install
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   flask run
   ```
   The API will be available at `http://localhost:5000`

2. **Start the frontend development server (coming soon)**
   ```bash
   cd frontend
   npm start
   ```
   The application will be available at `http://localhost:3000`

### Running Tests

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests (coming soon)
cd frontend
npm test
```

## API Documentation

API documentation is available at `/api/docs` when running the development server.

## Deployment

### Production

For production deployment, it's recommended to use Docker:

```bash
docker-compose -f docker-compose.prod.yml up --build
```

### Environment Variables

See `.env.example` in both backend and frontend directories for required environment variables.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [React](https://reactjs.org/)
- [Material-UI](https://mui.com/)
- And all other open-source libraries used in this project
