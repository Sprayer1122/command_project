# Testcase Failure Report Web Application

A modern Flask web application for analyzing and displaying testcase failure reports with a beautiful, responsive UI.

## Features

- **Modern UI**: Beautiful, responsive design with glassmorphism effects
- **Real-time Search**: Search through testcases, commands, and error messages
- **Advanced Filtering**: Filter by tags and failing commands
- **Interactive Table**: Sortable and searchable data table
- **Export Functionality**: Export filtered data to CSV
- **Detailed View**: Modal popup for detailed testcase information
- **Copy to Clipboard**: Quick copy functionality for testcase paths
- **Statistics Dashboard**: Overview of total and filtered testcases

## Project Structure

```
command_wise_failure/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── testcases.txt         # Sample testcase paths
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css     # Modern CSS styles
│   └── js/
│       └── script.js     # Frontend JavaScript
└── templates/
    └── index.html        # Main HTML template
```

## Setup Instructions

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Access the Web Interface**:
   Open your browser and navigate to `http://localhost:5000`

## API Endpoints

- `GET /` - Main web interface
- `GET /api/testcases` - Get sample testcase data (for frontend development)
- `POST /api/analyze` - Run actual analysis on testcases.txt file

## Usage

### Frontend Development Mode
- The application starts in "frontend development mode" with hardcoded sample data
- Use the "Refresh Data" button to reload sample data
- Use the "Run Analysis" button to perform actual analysis on your testcases.txt file

### Production Mode
- Place your actual testcase paths in `testcases.txt`
- Use the "Run Analysis" button to analyze real data
- The application will scan the specified directories and analyze failure logs

## Features in Detail

### Search and Filter
- **Global Search**: Search across all fields (path, command, error, tag)
- **Tag Filter**: Filter by specific error tags
- **Command Filter**: Filter by failing commands
- **Real-time Updates**: Results update as you type

### Data Export
- Export filtered results to CSV format
- Includes all visible columns
- Automatic filename with current date

### Responsive Design
- Works on desktop, tablet, and mobile devices
- Adaptive layout for different screen sizes
- Touch-friendly interface

## Customization

### Adding New Columns
1. Update the `analyze_testcases()` function in `app.py`
2. Modify the HTML table headers in `templates/index.html`
3. Update the JavaScript table rendering in `static/js/script.js`

### Styling Changes
- Modify `static/css/style.css` for visual changes
- Uses CSS Grid and Flexbox for modern layouts
- Includes hover effects and animations

### Backend Logic
- The core analysis logic is in `app.py`
- Functions can be extended for additional analysis features
- Easy to add new API endpoints

## Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Dependencies

- Flask 2.3.3
- Flask-CORS 4.0.0
- Werkzeug 2.3.7

## License

This project is open source and available under the MIT License. 