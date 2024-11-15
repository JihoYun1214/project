import requests
import base64
import time
from app.config.settings import Settings

class OCRProcessor:
    def __init__(self):
        settings = Settings()
        self.api_url = settings.OCR_API_URL
        self.client_id = settings.OCR_CLIENT_ID
        self.client_secret = settings.OCR_CLIENT_SECRET

    def process(self, file):
        try:
            if not file:
                return {'error': '파일이 없습니다'}

            # 파일 데이터 읽기
            file_data = file.read()
            base64_image = base64.b64encode(file_data).decode('utf-8')

            # API 요청 헤더
            headers = {
                "X-OCR-SECRET": self.client_secret,
                "X-NCP-APIGW-API-KEY-ID": self.client_id,
                "Content-Type": "application/json"
            }

            # API 요청 본문
            request_json = {
                "version": "V2",
                "requestId": str(int(time.time())),
                "timestamp": int(time.time() * 1000),
                "images": [
                    {
                        "format": "jpg",
                        "name": "test_image",
                        "data": base64_image
                    }
                ]
            }

            # 세션 생성 및 SSL 검증 비활성화
            session = requests.Session()
            session.verify = False

            # API 호출
            response = session.post(
                self.api_url,
                headers=headers,
                json=request_json
            )

            print(f"API Response Status: {response.status_code}")  # 디버깅용
            print(f"API Response: {response.text}")  # 디버깅용

            if response.status_code != 200:
                return {
                    'error': f'OCR API 오류: {response.status_code}',
                    'details': response.text
                }

            result = response.json()

            # 결과 처리
            extracted_text = ""
            if 'images' in result and result['images']:
                fields = result['images'][0].get('fields', [])
                for field in fields:
                    extracted_text += field.get('inferText', '') + " "

            # 텍스트 분석 수행
            analysis_result = self.analyze_text(extracted_text.strip())

            return {
                'success': True,
                'text': extracted_text.strip(),
                'analysis': analysis_result
            }

        except Exception as e:
            print(f"Error in OCR processing: {str(e)}")  # 디버깅용
            return {'error': str(e)}

    def analyze_text(self, text):
        # 1. 법률 용어 및 키워드 분석
        legal_keywords = {
            # 개인정보 관련
            '개인정보': '생존하는 개인에 관한 정보로서 개인을 알아볼 수 있는 정보',
            '정보주체': '처리되는 정보에 의하여 알아볼 수 있는 당사자',
            '처리': '개인정보의 수집, 생성, 기록, 저장, 보유, 가공, 편집, 검색, 출력, 정정, 복구, 이용, 제공, 공개, 파기 등',

            # 계약 관련
            '계약': '두 당사자 간의 법적 구속력이 있는 합의',
            '채무불이행': '계약상의 의무를 이행하지 않는 것',
            '손해배상': '계약 불이행이나 불법행위로 인한 손해를 배상하는 것',

            # 형사 관련
            '고소': '범죄의 피해자나 그 법정대리인이 수사기관에 범죄사실을 신고하여 처벌을 구하는 의사표시',
            '피고소인': '고소당한 자',
            '합의': '분쟁 당사자간의 상호 양해'
        }

        # 2. 관련 법령 정보
        relevant_laws = {
            '개인정보': {
                'title': '개인정보 보호법 제2조',
                'content': '''
                1. "개인정보"란 살아 있는 개인에 관한 정보로서 다음 각 목의 어느 하나에 해당하는 정보를 말한다.
                   가. 성명, 주민등록번호 및 영상 등을 통하여 개인을 알아볼 수 있는 정보
                   나. 해당 정보만으로는 특정 개인을 알아볼 수 없더라도 다른 정보와 쉽게 결합하여 알아볼 수 있는 정보
                '''
            },
            '계약위반': {
                'title': '민법 제390조',
                'content': '채무자가 채무의 내용에 따른 이행을 하지 아니한 때에는 채권자는 손해배상을 청구할 수 있다.'
            },
            '고소': {
                'title': '형사소송법 제223조',
                'content': '범죄의 피해자나 그 법정대리인은 고소할 수 있다.'
            }
        }

        # 3. 관련 판례 데이터베이스
        relevant_cases = {
            '개인정보': [
                {
                    'case_number': '대법원 2014다235080',
                    'summary': '개인정보 무단수집 및 이용 사건',
                    'ruling': '정보주체의 동의 없는 개인정보 수집 및 이용은 불법행위를 구성',
                    'reference': '개인정보보호법 위반에 따른 손해배상 책임 인정'
                },
                {
                    'case_number': '대법원 2016다251839',
                    'summary': '개인정보 유출 사고',
                    'ruling': '기업의 개인정보보호 의무 위반으로 인한 손해배상 책임',
                    'reference': '안전조치의무 위반에 따른 책임 인정'
                }
            ],
            '계약위반': [
                {
                    'case_number': '대법원 2018다248909',
                    'summary': '채무불이행에 따른 손해배상',
                    'ruling': '계약상 채무불이행에 따른 손해배상 범위 판단',
                    'reference': '통상손해 및 특별손해의 판단 기준 제시'
                }
            ],
            '고소합의': [
                {
                    'case_number': '대법원 2017도8033',
                    'summary': '고소인과 피고소인 간의 합의 효력',
                    'ruling': '처벌불원의 의사표시로 인한 공소기각 판결',
                    'reference': '합의에 따른 처벌불원의 효력 인정'
                }
            ]
        }

        # 4. 사례별 분석 로직
        def analyze_case_type(text):
            """텍스트 내용을 기반으로 사례 유형 분석"""
            case_types = {
                '개인정보': ['개인정보', '정보유출', '동의'],
                '계약분쟁': ['계약', '채무', '손해배상'],
                '형사고소': ['고소', '피고소인', '합의']
            }

            found_types = []
            for case_type, keywords in case_types.items():
                if any(keyword in text for keyword in keywords):
                    found_types.append(case_type)
            return found_types

        # 분석 결과 저장
        case_types = analyze_case_type(text)
        analysis_result = {
            'case_types': case_types,
            'identified_terms': [],
            'relevant_laws': [],
            'relevant_cases': [],
            'recommendations': []
        }

        # 발견된 법률 용어 분석
        for term, definition in legal_keywords.items():
            if term in text:
                analysis_result['identified_terms'].append({
                    'term': term,
                    'definition': definition
                })

        # 관련 법령 찾기
        for key, law_info in relevant_laws.items():
            if key in text:
                analysis_result['relevant_laws'].append(law_info)

        # 관련 판례 찾기
        for key, cases in relevant_cases.items():
            if key in text:
                analysis_result['relevant_cases'].extend(cases)

        # 권장사항 생성
        recommendations = self.generate_recommendations(case_types, text)
        analysis_result['recommendations'] = recommendations

        return analysis_result

    def generate_recommendations(self, case_types, text):
        """사례 유형별 권장사항 생성"""
        recommendations = []

        if '개인정보' in case_types:
            recommendations.append({
                'title': '개인정보 관련 권장사항',
                'items': [
                    '정보주체의 명시적 동의 확보 필요',
                    '개인정보 처리방침 준수',
                    '안전조치의무 이행 확인'
                ]
            })

        if '계약분쟁' in case_types:
            recommendations.append({
                'title': '계약 관련 권장사항',
                'items': [
                    '서면 계약서 작성 및 보관',
                    '채무불이행에 대한 증거 수집',
                    '내용증명 발송 고려'
                ]
            })

        if '형사고소' in case_types:
            recommendations.append({
                'title': '형사고소 관련 권장사항',
                'items': [
                    '증거자료 확보 및 보관',
                    '진술서 작성',
                    '합의 시 문서화 필요'
                ]
            })

        return recommendations

    def generate_case_summary(self, text, analysis):
        """사례 분석 요약 생성"""
        summary = []

        # 법률 용어가 발견된 경우
        if analysis['identified_terms']:
            terms = [item['term'] for item in analysis['identified_terms']]
            summary.append(f"본 사례에서 발견된 주요 법률 용어: {', '.join(terms)}")

        # 관련 법령이 있는 경우
        if analysis['relevant_laws']:
            laws = [law['title'] for law in analysis['relevant_laws']]
            summary.append(f"적용 가능한 법령: {', '.join(laws)}")

        # 관련 판례가 있는 경우
        if analysis['relevant_cases']:
            summary.append("참고할 만한 판례:")
            for case in analysis['relevant_cases']:
                summary.append(f"- {case['case_number']}: {case['summary']}")

        # 분석 결과가 없는 경우
        if not summary:
            summary.append("해당 사례에 대한 직접적인 법령 또는 판례를 찾을 수 없습니다.")

        return '\\n'.join(summary)






