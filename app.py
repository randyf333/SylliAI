from flask import Flask, render_template, request, redirect, url_for, flash, session
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from google import genai
import uuid
from flask import send_file
from flask import jsonify
import io
from pypdf import PdfReader
from docx import Document
import pdfplumber


load_dotenv(".env.dev")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")


supabase_url = os.getenv("SUPABASE_URL", "https://wwpdbvewqeoindredumk.supabase.co")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def pdf_extractor(file):
    text = ""
    with fitz.open(file) as pdf:
        for page in pdf:
            text = text + page.get_text()
    return text


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # After successful signup, create a record in the users table
            # This is necessary for row-level security policies to work correctly
            user_id = response.user.id
            supabase.table('users').insert({
                "id": user_id,
                "email": email
            }).execute()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            
            session['user_id'] = response.user.id
            session['email'] = email
            session['access_token'] = response.session.access_token
            session['refresh_token'] = response.session.refresh_token
            
            
            user_data = supabase.table('users').select('*').eq('id', response.user.id).execute()
            
            
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        response = supabase.table('syllabi').select('*').eq('user_id', session['user_id']).execute()
        syllabi = response.data
    except Exception as e:
        flash(f'Error retrieving syllabi: {str(e)}', 'error')
        syllabi = []
    
    return render_template('dashboard.html', syllabi=syllabi)

@app.route('/upload', methods=['GET', 'POST'])
def upload_syllabus():
    if 'user_id' not in session:
        flash('Please log in to upload syllabi', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        upload_type = request.form.get('upload_type')
        course_name = request.form.get('course_name')
        
        if upload_type == 'file':
            
            if 'file' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                
                try:
                    # Check if both tokens exist in session before using them
                    if 'access_token' in session and 'refresh_token' in session:
                        supabase.auth.set_session(session['access_token'], session['refresh_token'])
                    else:
                        flash('Session expired. Please log in again.', 'error')
                        return redirect(url_for('login'))
                    fileExtension = filename.rsplit('.', 1)[1].lower()
                    supabase.table('syllabi').insert({
                        "user_id": session['user_id'],
                        "course_name": course_name,
                        "file_path": file_path,
                        "content_type": f"{fileExtension.upper()} File"
                    }).execute()
                except Exception as e:
                    flash(f'Error uploading syllabus: {str(e)}', 'error')
                    return redirect(url_for('upload_syllabus'))
                
                flash('Syllabus uploaded successfully!', 'success')
                return redirect(url_for('dashboard'))
        else:
            
            content = request.form.get('content')
            
            
            try:
                # Check if both tokens exist in session before using them
                if 'access_token' in session and 'refresh_token' in session:
                    supabase.auth.set_session(session['access_token'], session['refresh_token'])
                else:
                    flash('Session expired. Please log in again.', 'error')
                    return redirect(url_for('login'))
                
                supabase.table('syllabi').insert({
                    "user_id": session['user_id'],
                    "course_name": course_name,
                    "content": content,
                    "content_type": "text"
                }).execute()
            except Exception as e:
                flash(f'Error saving syllabus content: {str(e)}', 'error')
                return redirect(url_for('upload_syllabus'))
            
            flash('Syllabus content saved successfully!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('upload.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Please log in to access settings', 'error')
        return redirect(url_for('login'))
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        user_data = supabase.table('users').select('*').eq('id', session['user_id']).execute()
        user = user_data.data[0] if user_data.data else None
    except Exception as e:
        flash(f'Error retrieving user data: {str(e)}', 'error')
        user = None
    
    if request.method == 'POST':
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', user=user)

def extract_text_from_file(file_path):
    try:    
        if file_path.lower().endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page_number, page in enumerate(pdf.pages):
                    text += page.extract_text() or ''
            return text.strip()   
         
        elif file_path.lower().endswith('.docx'):
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text.strip()    
        
        elif file_path.lower().endswith('.txt'):
            with open(file_path, 'r') as file:
                text = file.read().strip()
            return text
        
        else:
            return "Unsupported file type"
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        flash('Please log in to access chat', 'error')
        return redirect(url_for('login'))
    
    try:
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            data = request.get_json()
            user_message = data.get('message')
            
            # Retrieve all syllabi and documents for the user
            syllabi_response = supabase.table('syllabi').select('*').eq('user_id', session['user_id']).execute()
            
            # Extract content and metadata from syllabi and documents
            context_docs = []
            for syllabus in syllabi_response.data:
                syllabus_content = {
                    'course_name': syllabus.get('course_name', 'Untitled Course'),
                    'content': syllabus.get('content', ''),
                    'type': 'syllabus'
                }
                
                # If it's a file-based syllabus, try to extract content
                if syllabus.get('content_type', '').lower().endswith('file') and syllabus.get('file_path'):
                    extraced_text = extract_text_from_file(syllabus['file_path'])
                    if extraced_text:
                        syllabus_content['content'] = extraced_text
                        
                if syllabus_content['content']:
                    context_docs.append(syllabus_content)
            
            # Create enhanced prompt for Gemini
            prompt = """You are SylliAI, an AI assistant specialized in analyzing course syllabi and related documents.
            Analyze the following content and provide detailed, accurate answers based on the available information.
            If information is not found in the documents, clearly state that.
            
            Available Documents:
            """
            
            # Add context with document structure
            for doc in context_docs:
                prompt += f"\n\nDocument Type: {doc['type']}\nCourse: {doc['course_name']}\nContent:\n{doc['content']}"
            
            # Add specific analysis instructions
            prompt += f"""
            User Question: {user_message}
            Please provide a comprehensive answer based on the available documents:"""
            
            try:
                # Configure Gemini
                # Generate response
                response = client.models.generate_content(model = 'gemini-2.0-flash',contents=prompt)
                
                return jsonify({
                    "response": response.text,
                    "sources": [doc['course_name'] for doc in context_docs]
                })
            
            except Exception as e:
                print(f"Gemini API error: {str(e)}")  # For debugging
                return jsonify({"error": f"Error generating response: {str(e)}"}), 500
            
    except Exception as e:
        print(f"Chat function error: {str(e)}")  # For debugging
        return jsonify({"error": f"Error retrieving chat data: {str(e)}"}), 500
    
    return render_template('chat.html')

@app.route('/syllabus/<syllabus_id>', methods=['GET', 'POST'])
def view_syllabus(syllabus_id):
    if 'user_id' not in session:
        flash('Please log in to view syllabi', 'error')
        return redirect(url_for('login'))
    
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get syllabus data
        syllabus_response = supabase.table('syllabi').select('*').eq('id', syllabus_id).execute()
        if not syllabus_response.data:
            flash('Syllabus not found', 'error')
            return redirect(url_for('dashboard'))
        
        syllabus = syllabus_response.data[0]
        
        # Check if user owns this syllabus
        if syllabus['user_id'] != session['user_id']:
            flash('You do not have permission to view this syllabus', 'error')
            return redirect(url_for('dashboard'))
        
        # Get related documents
        # documents_response = supabase.table('syllabi').select('*').eq('syllabus_id', syllabus_id).execute()
        # documents = documents_response.data
        
        # No additional analysis needed for syllabus content
        
        # Handle question submission
        question_result = None
        question = None
        if request.method == 'POST':
            question = request.form.get('question')
            if question:
                # In a real implementation, this would use an LLM to answer the question
                # For now, we'll simulate this with some basic logic
                answer = "This is a simulated answer to your question."
                warning = None
                
                # Check if the question is covered by the documents
                # This is a simplified check - in reality, you'd use semantic search or an LLM
                question_keywords = question.lower().split()
                content_to_check = ""
                
                if syllabus['content_type'] == 'text' and 'content' in syllabus and syllabus['content']:
                    content_to_check += syllabus['content'].lower()
                
                # Add document content if available
                # for doc in documents:
                #     if doc['content_type'] == 'text' and 'content' in doc and doc['content']:
                #         content_to_check += " " + doc['content'].lower()
                
                # Simple keyword matching to determine if question is covered
                # In a real implementation, this would use more sophisticated NLP techniques
                covered = any(keyword in content_to_check for keyword in question_keywords if len(keyword) > 3)
                
                if not covered:
                    warning = "This question may not be covered by the available documents. The answer might not be accurate."
                
                question_result = {
                    'answer': answer,
                    'warning': warning
                }
        
        return render_template('syllabus_detail.html', syllabus=syllabus, 
                               question_result=question_result, question=question)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/syllabus/<syllabus_id>/chat', methods=['POST'])
def syllabus_chat(syllabus_id):
    if 'user_id' not in session:
        return jsonify({"error": "Please log in to access the chatbot."}), 401

    try:
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            return jsonify({"error": "Session expired. Please log in again."}), 401

        # Get syllabus data
        syllabus_response = supabase.table('syllabi').select('*').eq('id', syllabus_id).execute()
        if not syllabus_response.data:
            return jsonify({"error": "Syllabus not found."}), 404

        syllabus = syllabus_response.data[0]

        # Check if user owns this syllabus
        if syllabus['user_id'] != session['user_id']:
            return jsonify({"error": "You do not have permission to access this syllabus."}), 403

        # Handle chatbot request
        data = request.get_json()
        user_message = data.get('message')

        # Prepare context for the chatbot
        context = f"Syllabus: {syllabus.get('course_name', 'Untitled Course')}\n"
        if syllabus.get('content'):
            context += f"Content:\n{syllabus['content']}\n"
        elif syllabus.get('file_path'):
            extracted_text = extract_text_from_file(syllabus['file_path'])
            context += f"Extracted Content:\n{extracted_text}\n"

        # Generate response using Gemini
        prompt = f"""
        You are SylliAI, an AI assistant specialized in analyzing course syllabi.
        Based on the following syllabus, answer the user's question:

        {context}

        User Question: {user_message}
        """
        try:
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            return jsonify({"response": response.text})
        except Exception as e:
            return jsonify({"error": f"Error generating response: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@app.route('/delete_syllabus/<syllabus_id>')
def delete_syllabus(syllabus_id):
    if 'user_id' not in session:
        flash('Please log in to delete syllabi', 'error')
        return redirect(url_for('login'))
    
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Check if syllabus exists and belongs to user
        syllabus_response = supabase.table('syllabi').select('*').eq('id', syllabus_id).eq('user_id', session['user_id']).execute()
        
        if not syllabus_response.data:
            flash('Syllabus not found or you do not have permission to delete it', 'error')
            return redirect(url_for('dashboard'))
        
        # Delete related documents first
        # supabase.table('documents').delete().eq('syllabus_id', syllabus_id).execute()
        
        # Delete the syllabus
        supabase.table('syllabi').delete().eq('id', syllabus_id).execute()
        
        flash('Syllabus and related documents deleted successfully', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        flash(f'Error deleting syllabus: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/upload_document/<syllabus_id>', methods=['GET', 'POST'])
def upload_document(syllabus_id):
    if 'user_id' not in session:
        flash('Please log in to upload documents', 'error')
        return redirect(url_for('login'))
    
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Check if syllabus exists and belongs to user
        syllabus_response = supabase.table('syllabi').select('*').eq('id', syllabus_id).eq('user_id', session['user_id']).execute()
        
        if not syllabus_response.data:
            flash('Syllabus not found or you do not have permission to add documents to it', 'error')
            return redirect(url_for('dashboard'))
        
        syllabus = syllabus_response.data[0]
        
        if request.method == 'POST':
            upload_type = request.form.get('upload_type')
            document_name = request.form.get('document_name')
            document_type = request.form.get('document_type')
            
            if upload_type == 'file':
                if 'file' not in request.files:
                    flash('No file part', 'error')
                    return redirect(request.url)
                
                file = request.files['file']
                if file.filename == '':
                    flash('No selected file', 'error')
                    return redirect(request.url)
                
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    supabase.table('documents').insert({
                        "user_id": session['user_id'],
                        "syllabus_id": syllabus_id,
                        "name": document_name,
                        "document_type": document_type,
                        "file_path": file_path,
                        "content_type": "file"
                    }).execute()
                    
                    flash('Document uploaded successfully!', 'success')
                    return redirect(url_for('view_syllabus', syllabus_id=syllabus_id))
            else:
                content = request.form.get('content')
                
                supabase.table('documents').insert({
                    "user_id": session['user_id'],
                    "syllabus_id": syllabus_id,
                    "name": document_name,
                    "document_type": document_type,
                    "content": content,
                    "content_type": "text"
                }).execute()
                
                flash('Document content saved successfully!', 'success')
                return redirect(url_for('view_syllabus', syllabus_id=syllabus_id))
        
        return render_template('upload_document.html', syllabus=syllabus)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete_document/<document_id>')
def delete_document(document_id):
    if 'user_id' not in session:
        flash('Please log in to delete documents', 'error')
        return redirect(url_for('login'))
    
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get document to find its syllabus_id
        document_response = supabase.table('documents').select('*').eq('id', document_id).eq('user_id', session['user_id']).execute()
        
        if not document_response.data:
            flash('Document not found or you do not have permission to delete it', 'error')
            return redirect(url_for('dashboard'))
        
        document = document_response.data[0]
        syllabus_id = document['syllabus_id']
        
        # Delete the document
        supabase.table('documents').delete().eq('id', document_id).execute()
        
        flash('Document deleted successfully', 'success')
        return redirect(url_for('view_syllabus', syllabus_id=syllabus_id))
    
    except Exception as e:
        flash(f'Error deleting document: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/view_document/<document_id>')
def view_document(document_id):
    if 'user_id' not in session:
        flash('Please log in to view documents', 'error')
        return redirect(url_for('login'))
    
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get document
        document_response = supabase.table('documents').select('*').eq('id', document_id).eq('user_id', session['user_id']).execute()
        
        if not document_response.data:
            flash('Document not found or you do not have permission to view it', 'error')
            return redirect(url_for('dashboard'))
        
        document = document_response.data[0]
        syllabus_id = document['syllabus_id']
        
        # For now, just redirect to the syllabus detail page
        # In a real implementation, you might have a dedicated document viewer
        flash('Document viewing functionality will be implemented in a future update', 'info')
        return redirect(url_for('view_syllabus', syllabus_id=syllabus_id))
    
    except Exception as e:
        flash(f'Error viewing document: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/ask_question/<syllabus_id>', methods=['POST'])
def ask_question(syllabus_id):
    # This route is handled within the view_syllabus route
    # It's included here for completeness and future expansion
    return redirect(url_for('view_syllabus', syllabus_id=syllabus_id))

@app.route('/view_syllabus_file/<syllabus_id>')
def view_syllabus_file(syllabus_id):
    if 'user_id' not in session:
        flash('Please log in to view syllabus files', 'error')
        return redirect(url_for('login'))
    
    try:
        # Check if both tokens exist in session before using them
        if 'access_token' in session and 'refresh_token' in session:
            supabase.auth.set_session(session['access_token'], session['refresh_token'])
        else:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get syllabus data
        syllabus_response = supabase.table('syllabi').select('*').eq('id', syllabus_id).execute()
        if not syllabus_response.data:
            flash('Syllabus not found', 'error')
            return redirect(url_for('dashboard'))
        
        syllabus = syllabus_response.data[0]
        
        # Check if user owns this syllabus
        if syllabus['user_id'] != session['user_id']:
            flash('You do not have permission to view this syllabus', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if syllabus has a file
        if syllabus['content_type'] != 'file' or not syllabus['file_path']:
            flash('No file available for this syllabus', 'error')
            return redirect(url_for('view_syllabus', syllabus_id=syllabus_id))
        
        # Serve the file
        file_path = syllabus['file_path']
        return send_file(file_path, as_attachment=False)
    
    except Exception as e:
        flash(f'Error viewing syllabus file: {str(e)}', 'error')
        return redirect(url_for('view_syllabus', syllabus_id=syllabus_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)