import io
import os
import re
import sqlite3
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response
import database
import bid_document_generator

app = Flask(__name__)

# Ensure DB is initialized (though app.py should have done it, we remain robust)
database.init_db()

def infer_bid_type(title, text):
    """
    Analyzes the title and text to infer whether the bid is for:
    - '온누리상품권' (Onnuri)
    - '모바일상품권' (Mobile Coupon/Voucher)
    - '선물세트 (육류)'
    - '선물세트 (과일/농산물)'
    - '선물세트 (생선/수산물)'
    - '선물세트 (가전제품)'
    - '선물세트 (주방기구/생활용품)'
    - '선물세트 (건강식품/기타)'
    """
    combined = (title + " " + text).lower()
    
    if '온누리' in combined:
        return '온누리상품권'
    elif '기프티콘' in combined or '쿠폰' in combined or '모바일 상품권' in combined or '모바일형' in combined or '기프트카드' in combined:
        return '모바일상품권'
    
    # Analyze physical gift categories
    if any(k in combined for k in ('한우', '육류', '갈비', '고기', '돈육')):
        return '선물세트 (육류)'
    elif any(k in combined for k in ('사과', '배', '농산물', '과일', '곶감', '쌀', '버섯')):
        return '선물세트 (과일/농산물)'
    elif any(k in combined for k in ('굴비', '조기', '생선', '수산물', '멸치', '김', '해산물')):
        return '선물세트 (생선/수산물)'
    elif any(k in combined for k in ('청소기', '공청기', '공기청정기', '가전', '마사지기', '전자', '인덕션')):
        return '선물세트 (가전제품)'
    elif any(k in combined for k in ('냄비', '그릇', '식기', '주방', '생활용품', '침구', '의류', '가죽', '잡화')):
        return '선물세트 (주방기구/생활용품)'
    else:
        return '선물세트 (건강식품/기타)'

def analyze_company_type(title, text):
    """
    Infers the primary type of supplier requested for the bid:
    - '온라인쇼핑몰'
    - '유통사업자'
    - '직접 생산자'
    - '쿠폰/대행사업자'
    """
    combined = (title + " " + text).lower()
    
    # Rules based on common terms
    if any(k in combined for k in ('기프티콘', '쿠폰', '모바일 상품권', '상품권 발송', '대행 발송')):
        return '쿠폰/대행사업자'
    elif any(k in combined for k in ('선택형 복지몰', '복지몰', '쇼핑몰', '모바일몰', '시스템 연동')):
        return '온라인쇼핑몰'
    elif any(k in combined for k in ('생산 전문', '직접 생산', '제조사', '자체 가공', '농가 협력', 'haccp', '해썹')):
        return '직접 생산자'
    else:
        return '유통사업자'

def analyze_qualifications(title, text):
    """
    Parses the text to find required qualifications/criteria.
    """
    combined = (title + " " + text).lower()
    quals = []
    
    if any(k in combined for k in ('haccp', '해썹', '위생인증', '품질인증', '식품 안전')):
        quals.append('HACCP/위생인증')
    if any(k in combined for k in ('개별 가호', '자택 배송', '개별 배송', '전국 배송망', '택배 배송')):
        quals.append('전국 개별 배송망')
    if any(k in combined for k in ('cs', '콜센터', '고객센터', '전담 상담', '민원')):
        quals.append('CS 전담 고객센터')
    if any(k in combined for k in ('공식 지정', '공식 가맹', '수탁 금융', '공식 판매', '조달 자격')):
        quals.append('공식 수탁/가맹 자격')
    if any(k in combined for k in ('신용평가', '신용등급', '경영상태', '보증보험')):
        quals.append('신용평가등급 보증')
        
    return quals

def generate_ai_analysis(bid):
    """
    Dynamically simulates an AI analyzer parsing RFP (hwpx text) and extracting
    specific requirements, custom winning strategies, and critical risk factors based on refined categories.
    """
    bid_type = infer_bid_type(bid['title'], bid['hwpx_parsed_text'])
    text = bid['hwpx_parsed_text']
    
    # 1. Base Structure
    analysis = {
        'type': bid_type,
        'company_type': analyze_company_type(bid['title'], bid['hwpx_parsed_text']),
        'qualifications': analyze_qualifications(bid['title'], bid['hwpx_parsed_text']),
        'requirements': [],
        'strategies': [],
        'risks': []
    }
    
    # Extract approximate quantity if mentioned
    qty_match = re.search(r'(약\s*\d+[,0-9]*\s*명|총\s*\d+[,0-9]*\s*장|약\s*\d+[,0-9]*\s*개|\d+[,0-9]*\s*세트)', text)
    qty_info = f"({qty_match.group(1)} 규모)" if qty_match else ""
    
    if bid_type == '온누리상품권':
        analysis['requirements'] = [
            f"전통시장 온누리상품권 공식 판매 및 조달 대행 자격 입증 {qty_info}",
            "전국 단위 본사 및 산하 지사 임직원 대상 상품권 배부 및 수령 확인 대책",
            "지류형 상품권의 일련번호 추적 및 배송 유실 방지 방안",
            "모바일/카드형 상품권 도입 시 임직원 등록/충전 편의 솔루션 제공"
        ]
        analysis['strategies'] = [
            "온누리상품권 공식 가맹 지정 및 수탁 금융기관 자격을 첫머리에 강조하여 신뢰성을 확보하세요.",
            "지자체 및 공공기관의 특성상 지역 경제 활성화, ESG 상생 공헌 부문을 제안서에 명시하는 것이 중요합니다.",
            "분실 및 도난 방지를 위한 일련번호 보증보험 및 배송 프로세스를 제안하여 안정성을 어필하십시오."
        ]
        analysis['risks'] = [
            "상품권 수령 누락에 따른 임직원 불만 및 노조 민원 발생 우려",
            "지류 온누리상품권 발송 시 등기배송 요금 상승 및 수령 부재 시 반송 처리 리스크",
            "모바일형 상품권 등록에 미숙한 고령 임직원 지원 매뉴얼 미비 시 감점 위험"
        ]
    elif bid_type == '모바일상품권':
        analysis['requirements'] = [
            f"대규모 모바일 기프티콘/쿠폰 일괄 및 예약 발송 서버 연동 역량 {qty_info}",
            "백화점 모바일 상품권, 베이커리, 커피 등 임직원 선택형 기프트 옵션 구축",
            "대량 발송 후 미수신, 번호 변경, 오발송에 대처할 1:1 전담 CS 고객센터 상시 운영",
            "발송 결과 및 쿠폰 교환율에 대한 실시간 대시보드 리포팅 시스템 제공"
        ]
        analysis['strategies'] = [
            "임직원들이 직접 모바일로 선물을 고를 수 있는 '선택형 주문 폼 시스템'의 높은 편리성을 강하게 강조하세요.",
            "자체 전담 CS 콜센터 인력 및 빠른 오발송 대처 속도(2시간 이내 재발송 보장)를 정성 평가 항목에서 어필하십시오.",
            "다양한 프랜차이즈 브랜드(스타벅스, 투썸, 파리바게뜨 등)와의 공식 제휴 증빙을 첨부하여 가점 획득이 가능합니다."
        ]
        analysis['risks'] = [
            "통신사 스팸 필터링 또는 문자 스팸 처리로 인한 대량 미수신 리스크",
            "유효기간 만료 전 미사용 쿠폰에 대한 환불/연장 처리 기준 불분명 시 노사 마찰 유발 리스크",
            "기프티콘 교환처(오프라인 매장) 부족 또는 서비스 중단 시 대규모 클레임 가능성"
        ]
    else: # Physical gifts
        # Base physical requirements
        analysis['requirements'] = [
            f"임직원 맞춤형 선택식 구성 {qty_info}",
            "전국 임직원 개별 자택(가호)으로의 택배 배송망 및 콜드체인/보냉 포장력",
            "1차 서류 통과 후 실물 견본품(샘플) 오프라인 제출 및 실물 품평회 전시 준비",
            "배송 파손, 오배송, 제품 하자 시 즉각적인 맞춤 교환/회수 프로세스 수립"
        ]
        
        # Specific category tuning
        if bid_type == '선물세트 (육류)':
            analysis['requirements'].insert(0, "HACCP 인증 육가공 시설 확보 및 온도 관리 유통망 증빙")
            analysis['strategies'] = [
                "한우/육류 등 신선 정육의 마블링 및 품질 일관성을 보증할 등급 확인서를 필수 증빙으로 제시하세요.",
                "명절 배송 중 고기가 해동되는 현상을 막기 위한 친환경 3중 보냉 가방 및 드라이아이스 배치 계획을 강조하십시오."
            ]
            analysis['risks'] = [
                "하절기/명절 물류 대란 시 냉동 상태 유지 실패로 인한 위생/변질 리스크",
                "개별 가구 부재 시 신선 정육 방치로 인한 상함 및 대량 민원 리스크"
            ]
        elif bid_type == '선물세트 (과일/농산물)':
            analysis['requirements'].insert(0, "신선 농산물(과일, 버섯 등) 수확 직후 포장 및 산지 직송 조달 역량")
            analysis['strategies'] = [
                "당도 측정(Brix 기준) 선별 시스템과 충격 흡수 패키징 특허를 부각하여 품질 균일성을 어필하세요.",
                "지역 농가 협력 및 친환경 저탄소 농산물 인증을 통한 조달 명분을 강화하십시오."
            ]
            analysis['risks'] = [
                "기후 변화 및 장마에 따른 과일 당도 저하 및 품질 불균일 리스크",
                "운송 중 박스 내 충격으로 인한 과일 뭉개짐 및 표면 손상 리스크"
            ]
        elif bid_type == '선물세트 (생선/수산물)':
            analysis['requirements'].insert(0, "영광 굴비, 제주 옥돔 등 산지 원산지 증명 및 염장/건조 위생 관리")
            analysis['strategies'] = [
                "진공 급속 냉동 포장 및 아이스팩 밀봉 배송 시스템의 무결성을 도해로 표현하여 설득력을 높이십시오.",
                "전수 검사를 통한 원산지 둔갑 우려 배제 장치(이력 추적 시스템 등)를 어필하세요."
            ]
            analysis['risks'] = [
                "신선도 하락에 따른 수산물 비린내 유발 및 포장 파손 시 냄새 클레임 리스크",
                "수산물 유통 단계에서의 온도 일탈 및 세균 번식 리스크"
            ]
        elif bid_type == '선물세트 (가전제품)':
            analysis['requirements'].insert(0, "국내 KC 안전 인증 획득 및 1년 무상 A/S 보증 계획")
            analysis['strategies'] = [
                "국내 대기업 브랜드 가전 또는 가성비 높은 글로벌 인기 생활 가전의 A/S 센터 전국망망을 어필하십시오.",
                "불량 발생 시 1대1 즉시 맞교환 및 고장 수리 접수 전용 모바일 챗봇 운영안을 제안하세요."
            ]
            analysis['risks'] = [
                "수송 중 기기 파손 및 내부 정밀 부품 유격 발생에 따른 초기 불량 리스크",
                "중소 가전 브랜드 도입 시 지방 거주 임직원의 A/S 불편 호소 리스크"
            ]
        elif bid_type == '선물세트 (주방기구/생활용품)':
            analysis['requirements'].insert(0, "유명 브랜드 쿡웨어/그릇/식기 세트 정품 조달 자격 및 라이선스 증빙")
            analysis['strategies'] = [
                "임직원 선호도가 높은 프리미엄 쿡웨어 브랜드(테팔, 휘슬러 등)와의 직접 총판 자격을 어필하십시오.",
                "가정 친화적 테마에 맞춰 명절 한정 패키지 쇼핑백 포함 구성을 시각적으로 어필하세요."
            ]
            analysis['risks'] = [
                "도자기/유리 식기류 배송 시 파손율 상승에 따른 신속 반품 인프라 부족 리스크",
                "시중 유통 가격 대비 높은 마진율 책정에 따른 가격 경쟁력 평가 감점 리스크"
            ]
        else: # 건강식품/기타
            analysis['requirements'].insert(0, "건강기능식품 판매업 신고 필 및 식품의약품안전처 기능성 인정 증빙")
            analysis['strategies'] = [
                "정관장, 한삼인 등 임직원 인지도가 최상위인 건강기능식품 조달 가성비를 주 무기로 내세우십시오.",
                "홍삼, 종합 비타민 등 연령대별 복합 구성을 패키지로 묶어 넓은 선택 폭을 제공하는 기획이 유리합니다."
            ]
            analysis['risks'] = [
                "유통기한 미달(임박) 제품 오배송으로 인한 위생/도덕성 클레임 리스크",
                "기능성 부작용 호소 시 피해보상 규정 미비 리스크"
            ]
            
    return analysis

@app.route('/')
def index():
    type_filter = request.args.get('type_filter', '전체')
    keyword = request.args.get('keyword', '').strip()
    
    # Fetch all B2B gift bids
    db_filters = {'keyword': keyword} if keyword else {}
    raw_bids = database.get_all_gift_bids(db_filters)
    
    # Classify types dynamically
    bids = []
    
    # Count variables for refined sub-categories
    counts = {
        '온누리상품권': 0,
        '모바일상품권': 0,
        '선물세트 (육류)': 0,
        '선물세트 (과일/농산물)': 0,
        '선물세트 (생선/수산물)': 0,
        '선물세트 (가전제품)': 0,
        '선물세트 (주방기구/생활용품)': 0,
        '선물세트 (건강식품/기타)': 0
    }
    
    # Count variables for corporate types
    company_counts = {
        '온라인쇼핑몰': 0,
        '유통사업자': 0,
        '직접 생산자': 0,
        '쿠폰/대행사업자': 0
    }
    
    # Count variables for qualifications
    qual_counts = {
        'HACCP/위생인증': 0,
        '전국 개별 배송망': 0,
        'CS 전담 고객센터': 0,
        '공식 수탁/가맹 자격': 0,
        '신용평가등급 보증': 0
    }
    
    # Budget classification counts for chart
    budget_bands = [0, 0, 0, 0, 0]
    
    for bid in raw_bids:
        inferred = infer_bid_type(bid['title'], bid['hwpx_parsed_text'])
        bid['inferred_type'] = inferred
        
        # Analyze and store corporate metrics
        comp_type = analyze_company_type(bid['title'], bid['hwpx_parsed_text'])
        bid['company_type'] = comp_type
        if comp_type in company_counts:
            company_counts[comp_type] += 1
            
        quals = analyze_qualifications(bid['title'], bid['hwpx_parsed_text'])
        bid['qualifications'] = quals
        for q in quals:
            if q in qual_counts:
                qual_counts[q] += 1
        
        # Track counts safely
        if inferred in counts:
            counts[inferred] += 1
        else:
            counts['선물세트 (건강식품/기타)'] += 1
            
        # Parse budgets for charts
        budget_str = bid['budget'].replace(',', '')
        numbers = re.findall(r'\d+', budget_str)
        
        if not numbers:
            budget_bands[4] += 1 # Unit price or non-specified
        else:
            val = int(numbers[0])
            if '억' in bid['budget']:
                val *= 100000000
            elif '만' in bid['budget'] and '원' in bid['budget']:
                val *= 10000
            
            if val < 10000:
                budget_bands[4] += 1
            elif val < 50000000:
                budget_bands[0] += 1
            elif val <= 100000000:
                budget_bands[1] += 1
            elif val <= 300000000:
                budget_bands[2] += 1
            else:
                budget_bands[3] += 1
        
        # Filter matching
        if type_filter == '전체' or inferred == type_filter:
            bids.append(bid)
            
    total_count = len(raw_bids)
    
    # Calculate percentage for main overview metrics (Grouped)
    onnuri_pct = int((counts['온누리상품권'] / total_count) * 100) if total_count > 0 else 0
    coupon_pct = int((counts['모바일상품권'] / total_count) * 100) if total_count > 0 else 0
    
    physical_total = (
        counts['선물세트 (육류)'] + counts['선물세트 (과일/농산물)'] +
        counts['선물세트 (생선/수산물)'] + counts['선물세트 (가전제품)'] +
        counts['선물세트 (주방기구/생활용품)'] + counts['선물세트 (건강식품/기타)']
    )
    physical_pct = int((physical_total / total_count) * 100) if total_count > 0 else 0
    
    stats = {
        'total': total_count,
        'onnuri_pct': onnuri_pct,
        'coupon_pct': coupon_pct,
        'physical_pct': physical_pct,
        'meat_pct': int((counts['선물세트 (육류)'] / total_count) * 100) if total_count > 0 else 0,
        'fruit_pct': int((counts['선물세트 (과일/농산물)'] / total_count) * 100) if total_count > 0 else 0,
        'fish_pct': int((counts['선물세트 (생선/수산물)'] / total_count) * 100) if total_count > 0 else 0,
        'appliance_pct': int((counts['선물세트 (가전제품)'] / total_count) * 100) if total_count > 0 else 0,
        'kitchen_pct': int((counts['선물세트 (주방기구/생활용품)'] / total_count) * 100) if total_count > 0 else 0,
        'health_etc_pct': int((counts['선물세트 (건강식품/기타)'] / total_count) * 100) if total_count > 0 else 0,
    }
    
    chart_data = {
        'onnuri': counts['온누리상품권'],
        'coupon': counts['모바일상품권'],
        'meat': counts['선물세트 (육류)'],
        'fruit': counts['선물세트 (과일/농산물)'],
        'fish': counts['선물세트 (생선/수산물)'],
        'appliance': counts['선물세트 (가전제품)'],
        'kitchen': counts['선물세트 (주방기구/생활용품)'],
        'health_etc': counts['선물세트 (건강식품/기타)'],
        'budget_bands': budget_bands,
        # Corporate type statistics
        'company_types': {
            'mall': company_counts['온라인쇼핑몰'],
            'distributor': company_counts['유통사업자'],
            'producer': company_counts['직접 생산자'],
            'coupon_provider': company_counts['쿠폰/대행사업자']
        },
        # Qualification statistics
        'quals': {
            'haccp': qual_counts['HACCP/위생인증'],
            'delivery': qual_counts['전국 개별 배송망'],
            'cs': qual_counts['CS 전담 고객센터'],
            'official': qual_counts['공식 수탁/가맹 자격'],
            'credit': qual_counts['신용평가등급 보증']
        }
    }
    
    return render_template(
        'index.html',
        bids=bids,
        stats=stats,
        chart_data=chart_data,
        current_filter=type_filter
    )

@app.route('/analyzer/<int:bid_id>')
def analyzer(bid_id):
    bid = database.get_gift_bid_by_id(bid_id)
    if not bid:
        return "해당 공고를 찾을 수 없습니다.", 404
        
    ai_analysis = generate_ai_analysis(bid)
    bundle = bid_document_generator.generate_full_bid_bundle(bid, tab='b2b_gift')
    
    return render_template(
        'detail.html',
        bid=bid,
        ai_analysis=ai_analysis,
        bundle=bundle
    )

@app.route('/notice/<tab>/<doc_id>')
def view_notice(tab, doc_id):
    if tab == 'b2b_gift':
        item = database.get_gift_bid_by_id(doc_id)
    else:
        item = database.get_program_by_id(doc_id)
        
    if not item:
        return "공고를 찾을 수 없습니다.", 404
        
    bundle = bid_document_generator.generate_full_bid_bundle(item, tab=tab)
    item['bundle'] = bundle
    item['formatted_html'] = bundle['html_sections']['full']
    item['attachments'] = bundle['attachments_list']
    return render_template('notice_detail.html', item=item, tab=tab, bundle=bundle)

@app.route('/api/view_hwpx/<doc_id>')
def api_view_hwpx(doc_id):
    tab = request.args.get('tab', 'b2b_gift')
    if tab == 'b2b_gift':
        doc_item = database.get_gift_bid_by_id(doc_id)
    else:
        doc_item = database.get_program_by_id(doc_id)
        
    if doc_item:
        bundle = bid_document_generator.generate_full_bid_bundle(doc_item, tab=tab)
        return jsonify({
            "success": True,
            "title": doc_item['title'],
            "org": doc_item.get('institution') or doc_item.get('organization', '소관 부처'),
            "date": doc_item.get('announcement_date', ''),
            "deadline": doc_item.get('deadline', ''),
            "budget": doc_item.get('budget') or doc_item.get('budget_size', ''),
            "html_content": bundle['html_sections']['full'],
            "sections": bundle['html_sections'],
            "attachments": bundle['attachments_list']
        })
    return jsonify({"success": False, "message": "파일을 찾을 수 없습니다."}), 404

@app.route('/api/notice_attachments/<doc_id>')
def api_notice_attachments(doc_id):
    tab = request.args.get('tab', 'b2b_gift')
    if tab == 'b2b_gift':
        doc_item = database.get_gift_bid_by_id(doc_id)
    else:
        doc_item = database.get_program_by_id(doc_id)
        
    if doc_item:
        bundle = bid_document_generator.generate_full_bid_bundle(doc_item, tab=tab)
        return jsonify({
            "success": True,
            "title": doc_item['title'],
            "org": doc_item.get('institution') or doc_item.get('organization', '소관 부처'),
            "date": doc_item.get('announcement_date', ''),
            "deadline": doc_item.get('deadline', ''),
            "budget": doc_item.get('budget') or doc_item.get('budget_size', ''),
            "attachments": bundle['attachments_list']
        })
    return jsonify({"success": False, "message": "파일을 찾을 수 없습니다."}), 404

@app.route('/download_doc/<doc_id>')
def download_doc(doc_id):
    tab = request.args.get('tab', 'b2b_gift')
    file_type = request.args.get('file_type', 'zip')
    fmt = request.args.get('format', 'hwpx')
    
    if tab == 'b2b_gift':
        doc_item = database.get_gift_bid_by_id(doc_id)
    else:
        doc_item = database.get_program_by_id(doc_id)
        
    if not doc_item:
        return "공고를 찾을 수 없습니다.", 404
        
    org = doc_item.get('institution') if tab == 'b2b_gift' else doc_item.get('organization', '기관')
    clean_title = bid_document_generator.clean_filename(doc_item.get('title', '공고문'))
    bundle = bid_document_generator.generate_full_bid_bundle(doc_item, tab=tab)
    
    if file_type == 'zip':
        zip_buf = bid_document_generator.create_bid_zip_bytes(doc_item, tab=tab)
        filename = f"[전체첨부파일]_{org}_{clean_title}.zip"
        encoded_filename = urllib.parse.quote(filename)
        return Response(
            zip_buf,
            mimetype="application/zip",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    elif file_type == 'announcement':
        if fmt == 'txt':
            content = bundle['announcement'].encode('utf-8')
            mimetype = "text/plain; charset=utf-8"
            filename = f"[입찰공고문]_{org}_{clean_title}.txt"
            buf = io.BytesIO(content)
        else:
            buf = bid_document_generator.create_hwpx_bytes(f"입찰공고문 - {clean_title}", bundle['announcement'])
            mimetype = "application/hwp+zip"
            filename = f"[입찰공고문]_{org}_{clean_title}.hwpx"
    elif file_type == 'rfp':
        if fmt == 'txt':
            content = bundle['rfp'].encode('utf-8')
            mimetype = "text/plain; charset=utf-8"
            filename = f"[제안요청서]_{org}_{clean_title}_RFP.txt"
            buf = io.BytesIO(content)
        else:
            buf = bid_document_generator.create_hwpx_bytes(f"제안요청서 - {clean_title}", bundle['rfp'])
            mimetype = "application/hwp+zip"
            filename = f"[제안요청서]_{org}_{clean_title}_RFP.hwpx"
    elif file_type == 'spec':
        if fmt == 'txt':
            content = bundle['specification'].encode('utf-8')
            mimetype = "text/plain; charset=utf-8"
            filename = f"[과업지시서]_{org}_{clean_title}_과업지시서.txt"
            buf = io.BytesIO(content)
        else:
            buf = bid_document_generator.create_hwpx_bytes(f"과업지시서 - {clean_title}", bundle['specification'])
            mimetype = "application/hwp+zip"
            filename = f"[과업지시서]_{org}_{clean_title}_과업지시서.hwpx"
    elif file_type == 'forms':
        if fmt == 'txt':
            content = bundle['forms'].encode('utf-8')
            mimetype = "text/plain; charset=utf-8"
            filename = f"[제출서식]_{org}_{clean_title}_입찰참가서식.txt"
            buf = io.BytesIO(content)
        else:
            buf = bid_document_generator.create_hwpx_bytes(f"입찰서식 - {clean_title}", bundle['forms'])
            mimetype = "application/hwp+zip"
            filename = f"[제출서식]_{org}_{clean_title}_입찰참가서식.hwpx"
    else: # txt or full
        content = bundle['full_text'].encode('utf-8')
        mimetype = "text/plain; charset=utf-8"
        filename = f"[공고문_통합전문]_{org}_{clean_title}.txt"
        buf = io.BytesIO(content)
        
    encoded_filename = urllib.parse.quote(filename)
    return Response(
        buf,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@app.route('/evaluator')
def evaluator():
    bid_id = request.args.get('bid_id')
    target_bid = None
    if bid_id:
        target_bid = database.get_gift_bid_by_id(bid_id)
        
    return render_template(
        'evaluator.html',
        target_bid=target_bid
    )

if __name__ == '__main__':
    # Defaulting to 8080 for standard cloud environments (e.g. Render)
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Gift Bid AI Trend Analyzer on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
