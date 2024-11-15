from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from app.analyzer.document_analyzer import DocumentAnalyzer
from app.config.settings import Settings
from app.database.database import init_db
import os

# Flask 앱 생성
app = Flask(__name__)
CORS(app)

# 설정 로드
settings = Settings()
app.config.from_object(settings)

# 템플릿 폴더 경로 설정
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
print(f"Template directory: {template_dir}")  # 디버깅용

# 데이터베이스 초기화
init_db()

# 기본 라우트
@app.route('/')
def home():
    try:
        return render_template('test.html')
    except Exception as e:
        print(f"Error loading template: {str(e)}")  # 디버깅용
        return str(e)

# API 엔드포인트
@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '선택된 파일이 없습니다'})

    try:
        analyzer = DocumentAnalyzer()
        result = analyzer.analyze(file)
        print("Analysis result:", result)  # 디버깅용
        return jsonify(result)
    except Exception as e:
        print(f"Error in analyze_document: {str(e)}")  # 디버깅용
        return jsonify({'error': str(e)})

# 테스트용 엔드포인트
@app.route('/test')
def test():
    return "Server is running!"

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Debug mode:", app.debug)
    print("Template folder:", app.template_folder)
    app.run(debug=True, port=5000)
