
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import autopep8  # Auto-fix for Python code
import shutil  # File handling
import ast  # Import AST to check and modify Python syntax
import subprocess  # Allows running external code safely

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load OpenAI API key
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load PostgreSQL credentials
DB_NAME = os.getenv("POSTGRES_DB", "codecraftr")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# Database connection function
def get_db_connection():
    try:
        if not DB_PASSWORD:
            raise ValueError("POSTGRES_PASSWORD is missing!")
        
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# Request model for code analysis
class CodeRequest(BaseModel):
    language: str
    content: str
    auto_fix: bool = False  

# AI Code Analysis & Auto-Fix Endpoint
@app.post("/analyze/")
def analyze_code(request: CodeRequest):
    conn = get_db_connection()
    try:
        # Use OpenAI API to analyze the code
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"Analyze the following {request.language} code and suggest improvements."},
                {"role": "user", "content": request.content}
            ],
            max_tokens=200
        )

        analysis = response.choices[0].message.content.strip()

        # **Enhanced Auto-Fix for Python**
        fixed_code = request.content  # Default: return same code
        if request.auto_fix and request.language.lower() == "python":
            try:
                # Step 1: Check for syntax errors using AST
                ast.parse(request.content)  # If this fails, we need to fix the code
            except SyntaxError as e:
                # Step 2: Apply autopep8 for minor fixes
                fixed_code = autopep8.fix_code(request.content)
                
                # Step 3: If autopep8 doesn’t fix it, use OpenAI to suggest a corrected version
                fix_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Fix syntax errors in this Python code."},
                        {"role": "user", "content": request.content}
                    ],
                    max_tokens=200
                )
                fixed_code = fix_response.choices[0].message.content.strip()

        cur = conn.cursor()
        cur.execute("INSERT INTO code_analysis (language, content, analysis, created_at) VALUES (%s, %s, %s, %s)",
                    (request.language, request.content, analysis, datetime.now()))
        conn.commit()
        cur.close()
        conn.close()

        return {"analysis": analysis, "fixed_code": fixed_code}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Retrieve analysis history
@app.get("/history/")
def get_analysis_history():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, language, content, analysis, fixed_code, created_at FROM code_analysis ORDER BY created_at DESC")
        records = cur.fetchall()
        cur.close()
        conn.close()

        history = [
            {"id": r[0], "language": r[1], "content": r[2], "analysis": r[3], "fixed_code": r[4], "created_at": r[5]}
            for r in records
        ]
        return {"history": history}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# File Upload Endpoint
@app.post("/upload/")
def upload_file(file: UploadFile = File(...)):
    try:
        file_location = f"uploaded_files/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"message": "File uploaded successfully", "file_path": file_location}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

# Request model for chatbot
class ChatRequest(BaseModel):
    message: str

# AI Chatbot Endpoint
@app.post("/chatbot/")
def chatbot(request: ChatRequest):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for coding questions."},
                {"role": "user", "content": request.message}
            ],
            max_tokens=200
        )
        
        reply = response.choices[0].message.content.strip()
        return {"response": reply}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

# ------------------ New Run Code Endpoint ------------------
class RunCodeRequest(BaseModel):
    language: str
    content: str

@app.post("/run/")
def run_code(request: RunCodeRequest):
    language = request.language.lower()
    file_name = ""
    run_command = ""
    
    if language == "python":
        file_name = "temp.py"
        # Use "python" on Windows, "python3" on others
        python_command = "python3" if os.name != "nt" else "python"
        run_command = f"{python_command} {file_name}"
    elif language == "javascript":
        file_name = "temp.js"
        run_command = f"node {file_name}"
    elif language == "cpp":
        file_name = "temp.cpp"
        # Compile with g++ then run the executable
        run_command = f"g++ {file_name} -o temp.out && ./temp.out"
    elif language == "java":
        file_name = "Temp.java"
        run_command = "javac Temp.java && java Temp"
    elif language == "go":
        file_name = "temp.go"
        run_command = f"go run {file_name}"
    elif language == "bash":
        file_name = "temp.sh"
        run_command = f"bash {file_name}"
    else:
        return {"error": "Unsupported language."}

    try:
        # Write the provided code to a temporary file
        with open(file_name, "w") as f:
            f.write(request.content)

        # Execute the code using the constructed command
        result = subprocess.run(run_command, shell=True, capture_output=True, text=True, timeout=5)
        return {"output": result.stdout or result.stderr}

    except Exception as e:
        return {"output": f"Error: {str(e)}"}
# ------------------ End of Run Code Endpoint ------------------

# Home route
@app.get("/")
def home():
    return {"message": "CodeCraftr API is running!"}
