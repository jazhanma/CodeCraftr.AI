
from flask import Flask, request, jsonify, render_template
import sqlite3
import os
print("Flask is running in:", os.getcwd())  # Print working directory

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the database table if it doesn't exist
with app.app_context():
    db = get_db_connection()
    db.execute('''
        CREATE TABLE IF NOT EXISTS code_snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()

@app.route('/')
def home():
    return render_template('index.html')  # Serve the HTML UI

# Endpoint to save a code snippet
@app.route('/save', methods=['POST'])
def save_code():
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({'error': 'No code provided'}), 400

    code = data['code']
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('INSERT INTO code_snippets (code) VALUES (?)', (code,))
    db.commit()
    snippet_id = cursor.lastrowid
    db.close()
    
    return jsonify({'url': f'/snippet/{snippet_id}'})

# Endpoint to retrieve a saved code snippet
@app.route('/snippet/<int:id>', methods=['GET'])
def get_snippet(id):
    db = get_db_connection()
    snippet = db.execute('SELECT code FROM code_snippets WHERE id = ?', (id,)).fetchone()
    db.close()

    if snippet:
        return f"""
        <h1>Saved Code Snippet</h1>
        <pre><code class="language-python" id="snippetCode">{snippet['code']}</code></pre>
        <button onclick="copyCode()">Copy Code</button>
        <button onclick="deleteSnippet({id})" style="background-color:red;">Delete Snippet</button>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.25.0/prism.min.js"></script>
        <script>
            Prism.highlightAll();

            function copyCode() {{
                let code = document.getElementById("snippetCode").innerText;
                navigator.clipboard.writeText(code).then(() => {{
                    alert("Code copied to clipboard!");
                }});
            }}

            function deleteSnippet(id) {{
                fetch(`/delete/${{id}}`, {{ method: 'DELETE' }})
                    .then(response => response.json())
                    .then(data => {{
                        alert(data.message);
                        window.location.href = "/";
                    }});
            }}
        </script>
        """, 200
    else:
        return "<h1>Snippet not found</h1>", 404

# Endpoint to delete a snippet
@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_snippet(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DELETE FROM code_snippets WHERE id = ?', (id,))
    db.commit()
    db.close()

    return jsonify({'message': f'Snippet {id} deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)
