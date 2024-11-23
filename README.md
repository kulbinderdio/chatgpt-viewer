# ChatGPT History Viewer

**This was written entirely by AI. Used Cline with Sonnet 3.5.
Other than a few simple app usage tests no testing has been undertaken, that includes the Docker files**

A web application for visualizing and analyzing your ChatGPT conversation history. This application allows you to upload your ChatGPT history JSON file and view insights about your usage patterns, including daily activity and conversation statistics.

![image](https://github.com/user-attachments/assets/4b90edf0-08b0-4574-b3d5-6f774b066005)

## Features

- File upload interface for ChatGPT history JSON files
- Interactive timeline visualization of ChatGPT usage
- Daily conversation statistics
- Most active day identification
- Responsive design for desktop and mobile viewing
- Docker support for easy deployment

## Prerequisites

- Python 3.9+ (for local development)
- Docker and Docker Compose (for containerized deployment)

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chatgpt-viewer.git
cd chatgpt-viewer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Docker Deployment

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

2. Access the application at `http://localhost:5000`

## Using the Application

1. Export your ChatGPT history:
   - Go to chat.openai.com
   - Click on your profile
   - Select "Settings"
   - Click on "Data controls"
   - Choose "Export data"
   - Download and extract your data

2. Using the Viewer:
   - Open the application in your browser
   - Drag and drop your ChatGPT history JSON file onto the upload zone
   - Or click "Select File" to choose the file manually
   - View your usage statistics and visualizations

## Project Structure

```
chatgpt-viewer/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── templates/         # HTML templates
│   └── index.html    # Main page template
└── uploads/          # Upload directory (created automatically)
```

## Technical Details

- Built with Flask (Python web framework)
- Frontend using TailwindCSS for styling
- Plotly.js for interactive visualizations
- Docker containerization for deployment
- Pandas for data processing

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
