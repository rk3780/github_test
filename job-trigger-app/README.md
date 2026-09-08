# Databricks Job Trigger App

A React-based web application for triggering and monitoring Databricks jobs through a clean UI.

## Folder Structure

```
job-trigger-app/
├── app.py                          # Flask backend application
├── app.yaml                        # Databricks App configuration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── templates/                      # HTML templates
│   └── index.html                  # Main HTML template
├── static/                         # Static assets
│   ├── css/
│   │   └── styles.css              # Application styles
│   └── js/
│       ├── App.js                  # Main React application
│       └── components/             # React components
│           ├── JobSelector.js      # Job selection dropdown
│           ├── TriggerButton.js    # Job trigger button
│           ├── RunStatus.js        # Run status display
│           └── ErrorDisplay.js     # Error message display
```

## Components

### Backend (Flask)

* **app.py** - Main Flask application with API endpoints:
  - `GET /` - Serves the React frontend
  - `GET /api/jobs` - Lists all workspace jobs
  - `POST /api/jobs/<job_id>/run` - Triggers a job run
  - `GET /api/runs/<run_id>` - Gets job run status

### Frontend (React)

* **App.js** - Main application component with state management
* **JobSelector.js** - Dropdown component for selecting jobs
* **TriggerButton.js** - Button component for triggering jobs
* **RunStatus.js** - Component displaying run status with badges
* **ErrorDisplay.js** - Component for displaying error messages

## Features

* List all Databricks jobs in the workspace
* Select and trigger any job with one click
* Real-time status updates with auto-polling
* Color-coded status badges (Success, Running, Pending, Error)
* Direct links to job run pages
* Clean, responsive UI with Databricks branding

## API Integration

The app uses the Databricks SDK for Python:
* `w.jobs.list()` - Get all jobs
* `w.jobs.run_now(job_id)` - Trigger a job
* `w.jobs.get_run(run_id)` - Get run status

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