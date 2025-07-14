from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import traceback
import requests
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError

# -------------------- ✅ Flask Setup --------------------
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- ✅ MySQL Config --------------------
DB_USER = "root"
DB_PASSWORD = "system"
DB_HOST = "localhost"
DB_NAME = "threatdb"
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# -------------------- ✅ SQLAlchemy Models --------------------
class Threat(Base):
    __tablename__ = 'threats'
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    description = Column(Text)
    vulnerabilities = relationship('Vulnerability', backref='threat', cascade='all, delete-orphan')

class Vulnerability(Base):
    __tablename__ = 'vulnerabilities'
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    threat_id = Column(Integer, ForeignKey('threats.id'))
    test_cases = relationship('TestCase', backref='vulnerability', cascade='all, delete-orphan')

class TestCase(Base):
    __tablename__ = 'test_cases'
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    vulnerability_id = Column(Integer, ForeignKey('vulnerabilities.id'))

Base.metadata.create_all(engine)

# -------------------- ✅ Ollama Functions --------------------
def call_ollama(prompt, timeout=180):
    try:
        print("🔁 Calling Ollama...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False},
            timeout=timeout
        )
        response.raise_for_status()
        text = response.json().get("response", "")
        print("✅ Ollama response received.")
        return text
    except requests.exceptions.ReadTimeout:
        print("❌ Ollama timed out.")
        return ""
    except Exception as e:
        print("❌ Ollama error:", e)
        return ""

def extract_list_items(text):
    lines = [line.strip("-• ").strip() for line in text.split("\n") if line.strip()]
    return [line for line in lines if len(line) > 3]

def extract_test_cases(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return [line for line in lines if line.startswith("✅") or "TC" in line]

# -------------------- ✅ AI Generation --------------------
def generate_vulnerabilities(title, description):
    prompt = (
        f"Title:\n{title}\n\n"
        f"Description:\n{description}\n\n"
        f"List all possible vulnerabilities related to this threat using plain bullet points, "
        f"no numbers, and short clear descriptions."
    )
    raw = call_ollama(prompt)
    return extract_list_items(raw)

def generate_test_cases(vuln_desc, vuln_index):
    prompt = (
        f"Vulnerability:\n{vuln_desc}\n\n"
        f"Generate as many well-labeled cybersecurity test cases as possible for this vulnerability.\n"
        f"Use ✅ TC{vuln_index}.x format for each line.\n"
        f"Example:\n✅ TC{vuln_index}.1: Attempt a SQL injection...\n✅ TC{vuln_index}.2: Exceed login attempts...\n"
    )
    raw = call_ollama(prompt)
    return extract_test_cases(raw)

# -------------------- ✅ Upload Endpoint --------------------
@app.route('/upload', methods=['POST'])
def upload_file():
    session = Session()
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        df = pd.read_csv(file_path, encoding='utf-8')

        threats_output = []

        for row in df.to_dict(orient='records'):
            title = row.get("Title", "").strip()
            description = row.get("Description", "").strip()

            if not title or not description:
                continue

            print(f"\n🔐 Title:\n{title}\n\nDescription:\n{description}")
            threat = Threat(title=title, description=description)
            session.add(threat)

            vuln_list = generate_vulnerabilities(title, description)
            vuln_data = []

            for i, vuln_desc in enumerate(vuln_list, start=1):
                print(f"\n🔐 Vulnerability {i}: {vuln_desc}")
                vuln = Vulnerability(description=vuln_desc, threat=threat)
                session.add(vuln)

                tc_list = generate_test_cases(vuln_desc, i)
                for tc in tc_list:
                    session.add(TestCase(description=tc, vulnerability=vuln))

                vuln_data.append({
                    "description": vuln_desc,
                    "test_cases": tc_list
                })

            threats_output.append({
                "title": title,
                "description": description,
                "vulnerabilities": vuln_data
            })

        session.commit()
        return jsonify({'message': 'Processed successfully', 'threats': threats_output})

    except SQLAlchemyError as e:
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except Exception as e:
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    finally:
        session.close()

# -------------------- ✅ Run Flask --------------------
if __name__ == '__main__':
    app.run(debug=True)
