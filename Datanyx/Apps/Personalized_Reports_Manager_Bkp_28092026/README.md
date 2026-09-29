# Scheduled Reports Manager

A React-based web application for managing scheduled reports and generated reports in Databricks.

## Folder Structure

```
job-trigger-app/
├── app.py                          # Flask backend application
├── app.yaml                        # Databricks App configuration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── templates/                      # HTML templates
│   └── index.html                  # Main HTML template
└── static/                         # Static assets
    ├── css/
    │   └── styles.css              # Application styles
    └── js/
        └── App.js                  # Main React application
```

## Components

### Backend (Flask)

* **app.py** - Main Flask application with API endpoints:
  - `GET /` - Serves the React frontend
  - `GET /api/scheduled-reports` - Lists scheduled reports with search and pagination
  - `POST /api/scheduled-reports/<id>/pause` - Toggle pause status of a scheduled report
  - `POST /api/scheduled-reports/<id>/generate` - Generate a report from schedule
  - `DELETE /api/scheduled-reports/<id>` - Delete a scheduled report
  - `GET /api/generated-reports` - Lists generated reports with search and pagination
  - `GET /api/generated-reports/<id>/download` - Download a generated report
  - `DELETE /api/generated-reports/<id>` - Delete a generated report

### Frontend (React)

* **App.js** - Main application component with:
  - Tab navigation between scheduled and generated reports
  - Search and pagination controls
  - Report management actions (pause, generate, delete, download)
  - Responsive data tables

## Features

* **Scheduled Reports Management**:
  - View all scheduled reports with details
  - Search across report categories, titles, and schedule names
  - Pause/resume report schedules
  - Generate reports on-demand
  - Edit and delete scheduled reports
  - Pagination support

* **Generated Reports Management**:
  - View all generated reports
  - Search and filter generated reports
  - Download reports as text files
  - Delete generated reports
  - Pagination support

* **UI Features**:
  - Clean, responsive tabbed interface
  - Real-time search filtering
  - Configurable entries per page (10, 15, 25, 50)
  - Date/time formatting
  - Inline actions for each report

## API Integration

The app uses:
* **Databricks SDK** - For SQL warehouse access and statement execution
* **Unity Catalog Tables**:
  - `workspace.default.scheduled_reports` - Stores scheduled report configurations
  - `workspace.default.reports` - Stores generated report records

## Deployment

To deploy this app:

```bash
databricks apps deploy job-trigger-app --source-code-path /Workspace/Users/rishi.khandelwal@fractal.ai/job-trigger-app
```

Or use the "Deploy" button in the Databricks App UI.

## Technology Stack

* **Backend**: Flask + Databricks SDK
* **Frontend**: React 18 (loaded via CDN)
* **Styling**: Custom CSS with Databricks design system colors
* **Build**: No build process required (uses Babel standalone for JSX)