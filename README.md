# **Image to HTML Tailwind Code Converter**

## **System Overview**

This project is a comprehensive **Image to HTML Tailwind Code Converter** that transforms webpage images into pixel-perfect HTML and Tailwind CSS code. The system consists of a FastAPI backend that handles complex image processing and AI-powered code generation, paired with a responsive React frontend that provides an intuitive user interface.

## **Image-to-HTML-Tailwind Pipeline**

The conversion process follows a sophisticated multi-stage pipeline:

### **1. Image Upload and Preprocessing**
- **Image Reception**: Users upload webpage images through the React frontend
- **File Validation**: Ensures uploaded files are valid image formats (PNG, JPG, JPEG)
- **Image Storage**: Images are stored in organized directory structures (`uploads/{request_id}/images/`)
- **Request Management**: Each conversion gets a unique request ID for tracking and isolation

### **2. Image Segmentation and Analysis**
- **Intelligent Segmentation**: Uses advanced computer vision to detect and segment webpage components
- **Component Detection**: Identifies UI elements like headers, buttons, text blocks, images, and containers
- **Bounding Box Generation**: Creates precise coordinate data for each detected component
- **Hierarchy Mapping**: Establishes parent-child relationships between UI elements

### **3. Component Description Generation**
Two modes are available for analyzing detected components:

**Heuristic Mode:**
- Rule-based analysis for quick processing
- Pattern recognition for common UI elements
- Optimized for speed and efficiency

**AI-Powered Mode:**
- Uses Google Gemini and Claude APIs for detailed analysis
- Generates comprehensive descriptions including:
  - Element types and purposes
  - Color palettes and styling information
  - Content analysis and text extraction
  - Layout and positioning relationships

### **4. Layout and Style Analysis**
- **Coordinate Processing**: Converts bounding box data into relative positioning
- **Color Extraction**: Analyzes dominant colors for each component
- **Typography Detection**: Identifies font styles, sizes, and weights
- **Spacing Calculation**: Determines margins, padding, and alignment relationships
- **Responsive Mapping**: Creates responsive design guidelines for different screen sizes

### **5. Code Generation**
- **HTML Structure Creation**: Generates semantic HTML with proper element hierarchy
- **Tailwind CSS Integration**: Applies Tailwind classes for styling and layout
- **Responsive Design**: Ensures mobile-friendly, responsive layouts
- **Asset Handling**: Manages images and media elements appropriately
- **Code Optimization**: Produces clean, maintainable code without unnecessary comments

### **6. Real-time Streaming (Optional)**
- **Live Updates**: Shows code generation progress in real-time
- **Phase Tracking**: Updates users on current processing stage
- **Streaming Response**: Delivers generated code incrementally for a better user experience

## **Technology Stack**

### **Backend Technologies**
- **FastAPI**: Modern, fast web framework for building APIs with Python
- **Python 3.11**: Core programming language
- **Pydantic**: Data validation and settings management using Python type annotations
- **Motor**: Asynchronous MongoDB driver for Python
- **MongoDB**: NoSQL database for error logging and LLM usage tracking
- **Uvicorn**: ASGI web server implementation for Python

### **AI and Machine Learning**
- **Google Gemini API**: Advanced AI model for image analysis and code generation
- **Anthropic Claude API**: AI model for intelligent text generation and analysis
- **OpenCV**: Computer vision library for image processing
- **Pillow (PIL)**: Python Imaging Library for image manipulation
- **Web-page-Screenshot-Segmentation**: Specialized library for webpage component detection

## **Results**

Original Image: ![Original Image](results/vlc_org.png)

Generated UI: ![Generated UI from Code](results/vlc_gen.png)

## **Installation and Setup**

This provides instructions for setting up the development environment and running the Image-to-Code conversion application.

## **Prerequisites**

Before installing the application, ensure to have the following software and accounts:

- Python 3.11
- Node.js 14.x or higher
- Git
- API keys for:
    - Google Gemini API
    - Anthropic Claude API

## **Repository Setup**

Follow these steps to clone and set up the repository:

```bash
git clone https://github.com/bajajharsha/image-to-HTML-tailwind-code-converter
```

## **Backend Setup**

The backend is built with FastAPI and requires setting up a Python environment with necessary dependencies.

### **Setting up the Python Environment**

1. Create and activate a virtual environment:

```bash
# For Windows
python3.11 -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3.11 -m venv venv
source venv/bin/activate
```

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### **Environment Variables Configuration**

Create a **`.env`** file in the backend directory with the following variables:

```python

GEMINI_URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-03-25:generateContent?key="
UPLOAD_DIR="results"
CLAUDE_MODEL_NAME="claude-3-7-sonnet-20250219"
GEMINI_MODEL_NAME="gemini-2.5-pro-preview-03-25"
MONGO_URI="mongodb://localhost:27017"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"
MONGODB_DB_NAME = "image-to-code"
ERROR_COLLECTION_NAME = "errors"
LLM_USAGE_COLLECTION_NAME = "llm_usage"
GEMINI_STREAM_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key="
HOST = "localhost"

CLAUDE_API_KEY=your_anthropic_claude_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here

```

### **Running the Backend Server**

Start the FastAPI backend server using Uvicorn:

```bash
# From the root directory
uvicorn backend.main:app --reload
```

The backend API will be available at **`http://localhost:8000`**.

## **Frontend Setup**

The frontend is a React application with dependencies such as Tailwind CSS and React Syntax Highlighter.

### **Installing Dependencies**

1. Navigate to the frontend directory:

```bash
cd frontend
```

1. Install the npm dependencies:

```bash
npm install
```

### **Running the Frontend Development Server**

Start the React development server:

```bash
npm start
```

The frontend will be available at **`http://localhost:3000`**.

## **Testing the Application**

To test the complete application:

1. Start the backend server
2. Start the frontend development server
3. Open **`http://localhost:3000`** in a web browser
4. Upload an image and test the code generation functionality

## **Documentation**

For detailed documentation, please refer to the 
[Image to code Documentation](https://daffodil-spoonbill-5c9.notion.site/Image-to-code-Documentation-2444410206628083a6f0df978ded2feb)