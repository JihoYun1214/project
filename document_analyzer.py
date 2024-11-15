from app.analyzer.ocr_processor import OCRProcessor
import os

class DocumentAnalyzer:
    def __init__(self):
        self.ocr_processor = OCRProcessor()

    def analyze(self, file):
        try:
            # 업로드 폴더가 없으면 생성
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # 파일 저장
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)

            try:
                # 파일을 열어서 OCR 처리
                with open(file_path, 'rb') as f:
                    # OCR 처리
                    ocr_result = self.ocr_processor.process(f)

                    if 'error' in ocr_result:
                        return ocr_result

                    # 텍스트 분석
                    if 'text' in ocr_result:
                        analysis = self.ocr_processor.analyze_text(ocr_result['text'])
                        return {
                            'success': True,
                            'text': ocr_result['text'],
                            'analysis': analysis
                        }
                    else:
                        return {'error': '텍스트를 추출할 수 없습니다.'}

            finally:
                # 임시 파일 삭제
                if os.path.exists(file_path):
                    os.remove(file_path)

        except Exception as e:
            print(f"Analysis Error: {str(e)}")  # 디버깅용
            return {'error': str(e)}

