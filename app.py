from flask import Flask, request, render_template, jsonify, send_from_directory
import json
from datetime import datetime
import pandas as pd
import plotly
import plotly.express as px
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='templates')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True

# Ensure the upload and static folders exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logger.info(f"Upload folder created at: {UPLOAD_FOLDER}")
logger.info(f"Static folder created at: {STATIC_FOLDER}")
logger.info(f"Template folder: {app.template_folder}")

def parse_timestamp(create_time):
    """Parse timestamp from various possible formats."""
    logger.debug(f"Attempting to parse timestamp: {create_time} (type: {type(create_time)})")

    if create_time is None:
        logger.debug("Timestamp is None")
        return None

    # If it's already a datetime object
    if isinstance(create_time, datetime):
        return create_time

    # Handle numeric timestamps (including future dates)
    if isinstance(create_time, (int, float)) or (isinstance(create_time, str) and create_time.replace('.', '').isdigit()):
        try:
            # Convert string to float if needed
            if isinstance(create_time, str):
                create_time = float(create_time)

            # Create datetime object directly from timestamp
            dt = datetime.fromtimestamp(create_time)
            logger.debug(f"Successfully parsed timestamp {create_time} as seconds: {dt}")
            return dt
        except (ValueError, OSError, OverflowError) as e:
            logger.debug(f"Error parsing timestamp as seconds: {e}")
            try:
                # Try as milliseconds if seconds failed
                dt = datetime.fromtimestamp(create_time / 1000)
                logger.debug(f"Successfully parsed timestamp {create_time} as milliseconds: {dt}")
                return dt
            except (ValueError, OSError, OverflowError) as e:
                logger.debug(f"Error parsing timestamp as milliseconds: {e}")

    # Handle string formats
    if isinstance(create_time, str):
        # Try ISO format
        try:
            return datetime.fromisoformat(create_time.replace('Z', '+00:00'))
        except ValueError:
            pass

        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y/%m/%d %H:%M:%S'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(create_time, fmt)
            except ValueError:
                continue

    logger.warning(f"Failed to parse timestamp: {create_time}")
    return None

def count_messages(conversation):
    """Count the number of messages in a conversation."""
    count = 0
    if isinstance(conversation, dict) and 'mapping' in conversation:
        for node in conversation['mapping'].values():
            if isinstance(node, dict) and 'message' in node and isinstance(node['message'], dict):
                if node['message'].get('content', {}).get('parts'):
                    count += 1
    return count

def get_last_response(conversation):
    """Extract the last assistant response from the conversation."""
    if not isinstance(conversation, dict) or 'mapping' not in conversation:
        return None

    last_response = None
    latest_timestamp = 0

    for node in conversation['mapping'].values():
        if isinstance(node, dict) and 'message' in node:
            message = node['message']
            if isinstance(message, dict):
                # Check if it's an assistant message
                if message.get('author', {}).get('role') == 'assistant':
                    # Get the message timestamp
                    timestamp = message.get('create_time', 0) or 0
                    if timestamp > latest_timestamp:
                        content = message.get('content', {}).get('parts', [''])[0]
                        if content:
                            last_response = content
                            latest_timestamp = timestamp

    # Truncate long responses
    if last_response and len(last_response) > 100:
        last_response = last_response[:97] + '...'

    return last_response

def process_chat_history(data):
    logger.info("Processing chat history...")
    logger.debug(f"Received data structure: {type(data)}")

    message_counts = {}
    conversations_data = []

    if not isinstance(data, list):
        raise ValueError("Expected a list of conversations")

    # Process each conversation
    for idx, conversation in enumerate(data):
        logger.debug(f"Processing conversation {idx + 1}/{len(data)}")
        if not isinstance(conversation, dict):
            logger.warning(f"Skipping invalid conversation format: {type(conversation)}")
            continue

        # Get conversation create time
        create_time = conversation.get('create_time')
        if create_time:
            parsed_date = parse_timestamp(create_time)
            if parsed_date:
                # Get message count for this conversation
                msg_count = count_messages(conversation)

                # Add to daily stats using the conversation's date
                date = parsed_date.strftime('%Y-%m-%d')
                message_counts[date] = message_counts.get(date, 0) + msg_count

                # Extract conversation metadata for the table
                conv_data = {
                    'title': conversation.get('title', 'Untitled'),
                    'create_time': create_time,
                    'message_count': msg_count,
                    'last_response': get_last_response(conversation)
                }
                conversations_data.append(conv_data)

    if not message_counts:
        raise ValueError("No valid conversations found in the data.")

    logger.debug(f"Final message counts: {message_counts}")

    # Sort conversations by create_time in descending order (newest first)
    conversations_data.sort(key=lambda x: x['create_time'], reverse=True)

    # Create DataFrame and sort by date
    df = pd.DataFrame(list(message_counts.items()), columns=['date', 'count'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Create the plot with gradient colors
    fig = px.line(df, x='date', y='count',
                  title='ChatGPT Usage Over Time',
                  labels={'date': 'Date', 'count': 'Number of Messages'})

    # Customize the layout with pink/purple theme
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=40, t=40, b=40),
        title_font_color='#4a154b',
        xaxis=dict(
            gridcolor='#f8e6ff',
            showgrid=True,
            showline=True,
            linecolor='#e6b3ff',
            linewidth=1,
            tickfont=dict(color='#4a154b')
        ),
        yaxis=dict(
            gridcolor='#f8e6ff',
            showgrid=True,
            showline=True,
            linecolor='#e6b3ff',
            linewidth=1,
            tickfont=dict(color='#4a154b')
        )
    )

    # Update line color to gradient
    fig.update_traces(
        line_color='#8a2be2',
        line_width=2,
        fill='tonexty',
        fillcolor='rgba(255, 105, 180, 0.1)'  # Light pink with transparency
    )

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    logger.info("Chat history processing complete")

    return {
        'total_messages': sum(message_counts.values()),
        'daily_stats': message_counts,
        'usage_graph': graph_json,
        'conversations': conversations_data
    }

@app.route('/')
def index():
    logger.info("Serving index page...")
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return str(e), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info("Handling file upload...")
    if 'file' not in request.files:
        logger.warning("No file part in request")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("No selected file")
        return jsonify({'error': 'No selected file'}), 400

    if file:
        try:
            logger.info(f"Processing file: {file.filename}")
            data = json.load(file)
            stats = process_chat_history(data)
            logger.info("File processing complete")
            return jsonify(stats)
        except ValueError as e:
            logger.error(f"Error processing file: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 400
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {str(e)}")
            return jsonify({'error': 'Invalid JSON file format'}), 400
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True)
