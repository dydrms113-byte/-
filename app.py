from flask import Flask, request, redirect, url_for, render_template_string, jsonify
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data.db")

def init_db():
    print(f"📁 DB 경로: {DB_NAME}")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS investment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invest_type TEXT,
        product TEXT,
        corporation TEXT,
        purpose TEXT,
        invest_item TEXT,
        order_target TEXT,
        order_actual TEXT,
        setup_target TEXT,
        setup_actual TEXT,
        mass_target TEXT,
        mass_actual TEXT,
        delay_reason TEXT,
        base_amount REAL,
        order_price_target REAL,
        order_price_actual REAL,
        saving_target REAL,
        saving_actual REAL,
        reduce_1 REAL,
        reduce_2 REAL,
        reduce_3 REAL,
        reduce_4 REAL,
        reduce_5 REAL,
        reduce_6 REAL,
        reduce_7 REAL,
        reduce_8 REAL,
        reduce_9 REAL,
        saving_total REAL,
        activity TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    c.execute("PRAGMA table_info(investment)")
    columns = [col[1] for col in c.fetchall()]
    if 'updated_at' not in columns:
        c.execute("ALTER TABLE investment ADD COLUMN updated_at TEXT")
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS investment_monthly (
        id INTEGER,
        year_month TEXT,
        monthly_target REAL DEFAULT 0,
        monthly_actual REAL DEFAULT 0,
        PRIMARY KEY (id, year_month),
        FOREIGN KEY (id) REFERENCES investment(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()
    print("✅ DB 초기화 완료")

init_db()

PRODUCTS     = ["키친", "빌트인쿠킹", "리빙", "부품", "ES"]
CORPORATIONS = {
    "키친": ["KR","TR","MN","IN_T","IL_N","IL_P","VH","RA"],
    "빌트인쿠킹": ["KR","MN","IL_N","MZ","VH"],
    "리빙": ["KR","PN","TH","VH","IL_N","IL_P","TN","MX","EG","RA"],
    "ES": ["KR","TA","IL_N","IL_P","TH","SR","AZ","AT","AL"],
    "부품": ["KR","TA","PN","TR","TH","IL_N","VH","MN"]
}
ALL_PURPOSES = ["신규라인", "자동화", "라인 개조", "Overhaul", "신모델 대응", "T/Time 향상", "고장 수리", "안전", "설비 이설", "노후 교체", "설비 개선", "기타"]

MONTHS = [f"{y}-{m:02d}" for y in [2026, 2027] for m in range(1, 13)]

def nz(v, default=0.0):
    if v is None or v == "": return default
    try: return float(v) if isinstance(default, float) else str(v)
    except: return default

@app.route("/")
@app.route("/edit/<int:row_id>")
def index(row_id=None):
    edit_data = None
    if row_id:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM investment WHERE id = ?", (row_id,))
        edit_data = c.fetchone()
        conn.close()
        if not edit_data:
            return "데이터를 찾을 수 없습니다.", 404
    return render_template_string(INPUT_TPL,
        products=PRODUCTS, 
        corporations_json=json.dumps(CORPORATIONS, ensure_ascii=False),
        all_purposes=ALL_PURPOSES,
        edit_data=edit_data, 
        row_id=row_id)

@app.route("/save", methods=["POST"])
def save():
    try:
        f = request.form
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        row_id = f.get("row_id")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        print("=" * 50)
        print("📝 저장 요청")
        print(f"제품: {f.get('product')}, 법인: {f.get('corporation')}, 투자항목: {f.get('invest_item')}")
        
        values = (
            f.get("invest_type") or "",
            f.get("product") or "",
            f.get("corporation") or "",
            f.get("purpose") or "",
            f.get("invest_item") or "",
            f.get("order_target") or "",
            f.get("order_actual") or "",
            f.get("setup_target") or "",
            f.get("setup_actual") or "",
            f.get("mass_target") or "",
            f.get("mass_actual") or "",
            f.get("delay_reason") or "",
            nz(f.get("base_amount")),
            nz(f.get("order_price_target")),
            nz(f.get("order_price_actual")),
            nz(f.get("saving_target")),
            nz(f.get("saving_actual")),
            nz(f.get("reduce_1")),
            nz(f.get("reduce_2")),
            nz(f.get("reduce_3")),
            nz(f.get("reduce_4")),
            nz(f.get("reduce_5")),
            nz(f.get("reduce_6")),
            nz(f.get("reduce_7")),
            nz(f.get("reduce_8")),
            nz(f.get("reduce_9")),
            nz(f.get("saving_total")),
            f.get("activity") or ""
        )
        
        if row_id:
            c.execute("""UPDATE investment SET
                invest_type=?,product=?,corporation=?,purpose=?,invest_item=?,
                order_target=?,order_actual=?,setup_target=?,setup_actual=?,
                mass_target=?,mass_actual=?,delay_reason=?,
                base_amount=?,order_price_target=?,order_price_actual=?,
                saving_target=?,saving_actual=?,
                reduce_1=?,reduce_2=?,reduce_3=?,reduce_4=?,reduce_5=?,
                reduce_6=?,reduce_7=?,reduce_8=?,reduce_9=?,
                saving_total=?,activity=?,updated_at=? WHERE id=?""", values + (now, row_id))
            c.execute("DELETE FROM investment_monthly WHERE id=?", (row_id,))
            target_id = int(row_id)
            print(f"✅ 수정: ID={target_id}")
        else:
            c.execute("""INSERT INTO investment (
                invest_type,product,corporation,purpose,invest_item,
                order_target,order_actual,setup_target,setup_actual,
                mass_target,mass_actual,delay_reason,
                base_amount,order_price_target,order_price_actual,
                saving_target,saving_actual,
                reduce_1,reduce_2,reduce_3,reduce_4,reduce_5,
                reduce_6,reduce_7,reduce_8,reduce_9,
                saving_total,activity,created_at,updated_at
            ) VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?, ?,?,?, ?,?, ?,?,?,?,?, ?,?,?,?, ?,?,?,?)""",
            values + (now, now))
            target_id = c.lastrowid
            print(f"✅ 신규: ID={target_id}")
        
        conn.commit()
        
        order_target = f.get("order_target") or ""
        order_actual = f.get("order_actual") or ""
        saving_target = nz(f.get("saving_target"))
        saving_actual = nz(f.get("saving_actual"))
        
        for ym in MONTHS:
            t = saving_target if order_target == ym else 0.0
            a = saving_actual if order_actual == ym else 0.0
            c.execute("INSERT OR REPLACE INTO investment_monthly VALUES (?,?,?,?)", (target_id, ym, t, a))
        
        conn.commit()
        conn.close()
        print("=" * 50)
        
        return redirect("/list")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return f"저장 오류: {e}", 500

@app.route("/list")
def list_page():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM investment ORDER BY id DESC")
    rows = c.fetchall()
    print(f"📊 조회: {len(rows)}건")
    
    if len(rows) > 0:
        print(f"   샘플: ID={rows[0][0]}, 제품={rows[0][2]}, 법인={rows[0][3]}")
    
    c.execute("SELECT id,year_month,monthly_target,monthly_actual FROM investment_monthly")
    monthly_rows = c.fetchall()
    conn.close()
    
    monthly_map = {}
    for mid, ym, mt, ma in monthly_rows:
        monthly_map.setdefault(mid, {})[ym] = (mt or 0, ma or 0)
    
    processed = []
    for r in rows:
        r = list(r)
        base = r[13] if r[13] else 0
        sav_tgt = r[16] if r[16] else 0
        sav_act = r[17] if r[17] else 0
        product = r[2] if r[2] else ""
        
        # 제품별 절감률 목표 설정
        if product == "ES":
            rate_target = 50
        else:
            rate_target = 30
        
        # 절감률 실적 계산
        rate_actual = "-"
        if base and base != 0:
            if sav_act:
                rate_actual = round((sav_act/base)*100, 1)
            else:
                rate_actual = 0
        
        r.append(rate_target)
        r.append(rate_actual)
        
        # updated_at 또는 created_at 사용
        timestamp = r[30] if len(r) > 30 and r[30] else r[29]
        r.append(timestamp)
        
        processed.append(r)
    
    print(f"   처리: {len(processed)}건")
    
    processed_json = json.dumps(processed, ensure_ascii=False)
    months_json = json.dumps(MONTHS, ensure_ascii=False)
    
    return render_template_string(LIST_TPL, 
        processed_json=processed_json,
        months_json=months_json,
        corporations_json=json.dumps(CORPORATIONS, ensure_ascii=False),
        all_purposes_json=json.dumps(ALL_PURPOSES, ensure_ascii=False))

@app.route("/delete/<int:row_id>", methods=["POST"])
def delete_row(row_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM investment WHERE id=?", (row_id,))
    c.execute("DELETE FROM investment_monthly WHERE id=?", (row_id,))
    conn.commit()
    conn.close()
    print(f"🗑️ 삭제: ID={row_id}")
    return jsonify({"success": True})

INPUT_TPL = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>설비투자비 한계돌파 실적 관리 시스템</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Noto Sans KR', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 16px;
    font-size: 14px;
}

.header {
    background: linear-gradient(135deg, #4a5f9d 0%, #5a4a8a 100%);
    border-radius: 12px;
    padding: 18px 30px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    max-width: 1600px;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 16px;
}

.header h1 {
    color: white;
    font-size: 22px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 10px;
}

.header-right {
    display: flex;
    gap: 12px;
    align-items: center;
}

.header-btn {
    background: rgba(255,255,255,0.15);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    gap: 6px;
}

.header-btn:hover {
    background: rgba(255,255,255,0.25);
}

.container {
    max-width: 1600px;
    margin: 0 auto;
}

.row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin-bottom: 18px;
}

.card {
    background: white;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.card-full {
    grid-column: 1 / -1;
}

.card-header {
    padding: 16px 24px;
    font-weight: 700;
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 3px solid;
}

.card-header.pink {
    background: linear-gradient(to bottom, #fce7f3 0%, #fbcfe8 100%);
    color: #be185d;
    border-bottom-color: #ec4899;
}

.card-header.cyan {
    background: linear-gradient(to bottom, #cffafe 0%, #a5f3fc 100%);
    color: #0e7490;
    border-bottom-color: #06b6d4;
}

.card-header.amber {
    background: linear-gradient(to bottom, #fef3c7 0%, #fde68a 100%);
    color: #b45309;
    border-bottom-color: #f59e0b;
}

.card-header.blue {
    background: linear-gradient(to bottom, #dbeafe 0%, #bfdbfe 100%);
    color: #1e40af;
    border-bottom-color: #3b82f6;
}

.card-header.emerald {
    background: linear-gradient(to bottom, #d1fae5 0%, #a7f3d0 100%);
    color: #047857;
    border-bottom-color: #10b981;
}

.card-header.violet {
    background: linear-gradient(to bottom, #ede9fe 0%, #ddd6fe 100%);
    color: #6d28d9;
    border-bottom-color: #8b5cf6;
}

.card-body {
    padding: 24px;
}

.form-group {
    margin-bottom: 18px;
}

.form-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 10px;
}

.toggle-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.toggle-btn {
    padding: 14px;
    border: 2px solid #cbd5e1;
    border-radius: 10px;
    background: #f1f5f9;
    text-align: center;
    font-weight: 600;
    font-size: 15px;
    color: #64748b;
    cursor: pointer;
    transition: all 0.3s;
}

.toggle-btn.active {
    background: #dbeafe;
    border-color: #3b82f6;
    color: #1e40af;
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

input[type="text"],
input[type="number"],
input[type="month"],
select,
textarea {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #cbd5e1;
    border-radius: 10px;
    font-size: 15px;
    font-family: 'Noto Sans KR', sans-serif;
    background: #f1f5f9;
    transition: all 0.3s;
}

input::placeholder {
    color: #94a3b8;
}

input:focus,
select:focus,
textarea:focus {
    outline: none;
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

select {
    cursor: pointer;
}

textarea {
    resize: vertical;
    min-height: 100px;
    line-height: 1.6;
}

input[readonly] {
    background: #f1f5f9;
    border: 3px solid #8b5cf6;
    font-weight: 700;
    color: #1e40af;
}

.info-box {
    background: #dbeafe;
    border-left: 4px solid #3b82f6;
    padding: 14px 18px;
    border-radius: 8px;
    margin-top: 12px;
    margin-bottom: 12px;
}

.info-box-title {
    font-size: 13px;
    font-weight: 600;
    color: #1e40af;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.info-box-text {
    font-size: 12px;
    color: #3b82f6;
    line-height: 1.6;
}

.table-wrapper {
    overflow-x: auto;
    margin-top: 0;
}

.reduce-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}

.reduce-table th {
    background: #f3f4f6;
    color: #374151;
    font-size: 12px;
    padding: 12px 10px;
    text-align: center;
    font-weight: 600;
    border: 1px solid #e5e7eb;
    white-space: nowrap;
}

.reduce-table th:first-child {
    border-radius: 8px 0 0 0;
}

.reduce-table th:nth-child(2) {
    background: #dcfce7;
    color: #065f46;
    font-weight: 700;
}

.reduce-table th:last-child {
    border-radius: 0 8px 0 0;
}

.reduce-table td {
    padding: 12px 10px;
    text-align: center;
    background: white;
    border: 1px solid #e5e7eb;
}

.reduce-table td:first-child {
    font-weight: 600;
    color: #374151;
    background: #f9fafb;
}

.reduce-table td:nth-child(2) {
    background: white;
    border: 1px solid #e5e7eb;
}

.reduce-table td:nth-child(2) input {
    background: #f1f5f9;
    font-weight: 700;
    color: #065f46;
    font-size: 15px;
    border: 2px solid #cbd5e1;
}

.reduce-table input {
    max-width: 90px;
    text-align: center;
    background: #f1f5f9;
    padding: 10px;
    border: 2px solid #cbd5e1;
    border-radius: 6px;
}

.reduce-number {
    display: block;
    font-size: 11px;
    color: #9ca3af;
    font-weight: 700;
    margin-bottom: 3px;
}

.activity-section {
    margin-top: 20px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
}

.activity-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 12px;
}

.button-group {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 28px;
    padding: 26px;
    background: white;
    border-radius: 14px;
}

.btn-primary {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    border: none;
    padding: 16px 48px;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 4px 16px rgba(16,185,129,0.3);
    transition: all 0.3s;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(16,185,129,0.4);
}

.btn-secondary {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    color: white;
    border: none;
    padding: 16px 48px;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 4px 16px rgba(99,102,241,0.3);
    transition: all 0.3s;
}

.btn-secondary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.4);
}
</style>
</head>
<body>

<div class="header">
    <h1>📋 설비투자비 한계돌파 실적 관리 시스템</h1>
    <div class="header-right">
        <a href="/" class="header-btn">📄 Data 입력 페이지</a>
        <a href="/list" class="header-btn">📊 투자실적 조회</a>
    </div>
</div>

<div class="container">
    <form method="post" action="/save" id="mainForm">
    {%- if row_id -%}<input type="hidden" name="row_id" value="{{ row_id }}">{%- endif -%}

    <div class="row">
        <div class="card">
            <div class="card-header pink">📌 투자 분류</div>
            <div class="card-body">
                <div class="form-group">
                    <div class="form-label">💼 투자 유형</div>
                    <div class="toggle-group">
                        <div class="toggle-btn {%- if not edit_data or edit_data[1]=='확장' %} active{%- endif -%}" onclick="selectType(this, '확장')">확장</div>
                        <div class="toggle-btn {%- if edit_data and edit_data[1]=='경상' %} active{%- endif -%}" onclick="selectType(this, '경상')">경상</div>
                    </div>
                    <input type="hidden" name="invest_type" id="invest_type" value="{%- if edit_data -%}{{ edit_data[1] or '확장' }}{%- else -%}확장{%- endif -%}">
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <div class="form-label">📦 제품</div>
                        <select name="product" id="product" onchange="updateCorporations()">
                            {%- for p in products -%}
                            <option {%- if edit_data and edit_data[2]==p %} selected{%- endif -%}>{{ p }}</option>
                            {%- endfor -%}
                        </select>
                    </div>

                    <div class="form-group">
                        <div class="form-label">🌍 법인</div>
                        <select name="corporation" id="corporation">
                        </select>
                    </div>
                </div>

                <div class="info-box">
                    <div class="info-box-title">💡 TIP</div>
                    <div class="info-box-text">
                        • 5천만원 미만인 경상투자 건은 Base금액을 집행가로 기입 ("집행가 – 발주가"로 실적 관리)<br>
                        • 해외 법인은 HQ 생산기술에서 검토/지원해주는 투자 건만 기입 (법인 자체 진행하는 직발주 제외)
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header cyan">📋 투자 항목 상세</div>
            <div class="card-body">
                <div class="form-group">
                    <div class="form-label">🎯 투자목적</div>
                    <select name="purpose">
                        {%- for p in all_purposes -%}
                        <option {%- if edit_data and edit_data[4]==p %} selected{%- endif -%}>{{ p }}</option>
                        {%- endfor -%}
                    </select>
                </div>

                <div class="form-group">
                    <div class="form-label">📝 투자항목</div>
                    <input type="text" name="invest_item" value="{%- if edit_data -%}{{ edit_data[5] or '' }}{%- endif -%}" placeholder="예: 창원 선진화 오븐라인">
                </div>

                <div class="info-box">
                    <div class="info-box-title">💡 TIP: 투자항목은 구체적으로 작성해주세요</div>
                    <div class="info-box-text">(예: "라인 #3 자동화 설비 도입" 등)</div>
                </div>
            </div>
        </div>
    </div>

    <div class="card card-full">
        <div class="card-header amber">📅 투자 주요 일정</div>
        <div class="card-body">
            <div class="form-row">
                <div class="form-group">
                    <div class="form-label">🎯 발주 목표</div>
                    <input type="month" name="order_target" value="{%- if edit_data -%}{{ edit_data[6] or '' }}{%- endif -%}">
                </div>
                <div class="form-group">
                    <div class="form-label">✅ 발주 실적</div>
                    <input type="month" name="order_actual" value="{%- if edit_data -%}{{ edit_data[7] or '' }}{%- endif -%}">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <div class="form-label">🎯 셋업 목표</div>
                    <input type="month" name="setup_target" value="{%- if edit_data -%}{{ edit_data[8] or '' }}{%- endif -%}">
                </div>
                <div class="form-group">
                    <div class="form-label">✅ 셋업 실적</div>
                    <input type="month" name="setup_actual" value="{%- if edit_data -%}{{ edit_data[9] or '' }}{%- endif -%}">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <div class="form-label">🎯 양산 목표</div>
                    <input type="month" name="mass_target" value="{%- if edit_data -%}{{ edit_data[10] or '' }}{%- endif -%}">
                </div>
                <div class="form-group">
                    <div class="form-label">✅ 양산 실적</div>
                    <input type="month" name="mass_actual" value="{%- if edit_data -%}{{ edit_data[11] or '' }}{%- endif -%}">
                </div>
            </div>

            <div class="form-group">
                <div class="form-label">❓ 연기사유</div>
                <input type="text" name="delay_reason" value="{%- if edit_data -%}{{ edit_data[12] or '' }}{%- endif -%}" placeholder="예: 제품개발 지연에 따른 양산 일정">
            </div>
        </div>
    </div>

    <div class="row" style="margin-top: 24px;">
        <div class="card">
            <div class="card-header blue">💰 투자금액 (단위: 억원)</div>
            <div class="card-body">
                <div class="form-group">
                    <div class="form-label">💵 Base 금액</div>
                    <input type="number" name="base_amount" step="0.01" value="{%- if edit_data -%}{{ edit_data[13] or '' }}{%- endif -%}" placeholder="0.00">
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <div class="form-label">🎯 발주가 목표</div>
                        <input type="number" name="order_price_target" step="0.01" value="{%- if edit_data -%}{{ edit_data[14] or '' }}{%- endif -%}" placeholder="0.00">
                    </div>

                    <div class="form-group">
                        <div class="form-label">✅ 발주가 실적</div>
                        <input type="number" name="order_price_actual" step="0.01" value="{%- if edit_data -%}{{ edit_data[15] or '' }}{%- endif -%}" placeholder="0.00">
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header violet">📊 절감 실적 (단위: 억원)</div>
            <div class="card-body">
                <div class="form-row">
                    <div class="form-group">
                        <div class="form-label">🎯 절감 목표</div>
                        <input type="number" name="saving_target" step="0.01" value="{%- if edit_data -%}{{ edit_data[16] or '' }}{%- endif -%}" placeholder="0.00">
                    </div>

                    <div class="form-group">
                        <div class="form-label">✅ 절감 실적</div>
                        <input id="saving_actual" name="saving_actual" readonly value="{%- if edit_data -%}{{ edit_data[17] or '' }}{%- endif -%}" placeholder="0.00">
                    </div>
                </div>

                <div class="info-box">
                    <div class="info-box-title">💡 절감 실적은 아래 세부 항목의 합계가 자동 계산됩니다</div>
                </div>
            </div>
        </div>
    </div>

    <div class="card card-full">
        <div class="card-header emerald">📊 투자비 절감 활동 실적 (단위: 억원)</div>
        <div class="card-body">
            <div class="table-wrapper">
                <table class="reduce-table">
                    <thead>
                        <tr>
                            <th style="width:110px">항목</th>
                            <th style="width:100px">활동 합계</th>
                            <th><span class="reduce-number">①</span>신기술<br>신공법</th>
                            <th><span class="reduce-number">②</span>염가형<br>부품</th>
                            <th><span class="reduce-number">③</span>중국/<br>Local 설비</th>
                            <th><span class="reduce-number">④</span>중국/한국<br>Collabo</th>
                            <th><span class="reduce-number">⑤</span>컨테이너<br>최소화</th>
                            <th><span class="reduce-number">⑥</span>출장 인원<br>최소화</th>
                            <th><span class="reduce-number">⑦</span>유휴<br>설비</th>
                            <th><span class="reduce-number">⑧</span>사양<br>최적화</th>
                            <th><span class="reduce-number">⑨</span>기타</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>절감 실적</td>
                            <td><input id="total_display" readonly value="{%- if edit_data -%}{{ edit_data[27] or '0.00' }}{%- else -%}0.00{%- endif -%}"></td>
                            <td><input class="reduce" type="number" name="reduce_1" step="0.01" value="{%- if edit_data -%}{{ edit_data[18] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_2" step="0.01" value="{%- if edit_data -%}{{ edit_data[19] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_3" step="0.01" value="{%- if edit_data -%}{{ edit_data[20] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_4" step="0.01" value="{%- if edit_data -%}{{ edit_data[21] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_5" step="0.01" value="{%- if edit_data -%}{{ edit_data[22] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_6" step="0.01" value="{%- if edit_data -%}{{ edit_data[23] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_7" step="0.01" value="{%- if edit_data -%}{{ edit_data[24] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_8" step="0.01" value="{%- if edit_data -%}{{ edit_data[25] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                            <td><input class="reduce" type="number" name="reduce_9" step="0.01" value="{%- if edit_data -%}{{ edit_data[26] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="activity-section">
                <div class="activity-label">📝 활동내용</div>
                <textarea name="activity" placeholder="절감 활동 내용을 상세히 입력하세요
예)
1) 자동화 공법 개발 및 설비 개선
3) 중국 업체 활용
6) 안정화 기간 단축 및 Local 업체 활용
7) 사내/협력사 유휴설비 활용">{%- if edit_data -%}{{ edit_data[28] or '' }}{%- endif -%}</textarea>
            </div>
        </div>
    </div>

    <input type="hidden" name="saving_total" id="saving_total" value="{%- if edit_data -%}{{ edit_data[27] or '' }}{%- endif -%}">

    <div class="button-group">
        <button type="submit" class="btn-primary">💾 저장하기</button>
        <a href="/list" class="btn-secondary">📊 투자실적 조회</a>
    </div>

    </form>
</div>

<script>
const CORPORATIONS = {{ corporations_json | safe }};
const EDIT_PRODUCT = {%- if edit_data -%}"{{ edit_data[2] or '키친' }}"{%- else -%}"키친"{%- endif -%};
const EDIT_CORPORATION = {%- if edit_data -%}"{{ edit_data[3] or '' }}"{%- else -%}""{%- endif -%};

function updateCorporations() {
    const product = document.getElementById('product').value;
    const corpSelect = document.getElementById('corporation');
    const corps = CORPORATIONS[product] || [];
    
    corpSelect.innerHTML = '';
    corps.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        corpSelect.appendChild(opt);
    });
}

function selectType(btn, type){
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('invest_type').value = type;
}

function calcTotal(){
    let s=0;
    document.querySelectorAll(".reduce").forEach(e=>{ s+=Number(e.value)||0; });
    const total = s.toFixed(2);
    document.getElementById("saving_actual").value = total;
    document.getElementById("saving_total").value = total;
    document.getElementById("total_display").value = total;
}

window.onload = function(){ 
    updateCorporations();
    if(EDIT_CORPORATION) {
        document.getElementById('corporation').value = EDIT_CORPORATION;
    }
    calcTotal(); 
}
</script>

</body>
</html>
"""

LIST_TPL = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>설비 투자비 활동 실적 조회</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

*{box-sizing:border-box;margin:0;padding:0}
body{
    font-family:'Noto Sans KR','Malgun Gothic',sans-serif;
    font-size:13px;
    background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color:#333;
    padding:16px;
}

.top-header{
    background:linear-gradient(135deg, #4a5f9d 0%, #5a4a8a 100%);
    backdrop-filter:blur(10px);
    padding:18px 28px;
    border-radius:16px;
    box-shadow:0 8px 32px rgba(0,0,0,0.15);
    margin-bottom:20px;
    display:flex;
    align-items:center;
    justify-content:space-between;
}

.top-header h2{
    font-size:22px;
    font-weight:700;
    color:#fff;
    display:flex;
    align-items:center;
    gap:10px;
}

.top-header-right{
    display:flex;
    gap:12px;
    align-items:center;
}

.top-header a{
    background:rgba(255,255,255,0.2);
    color:#fff;
    padding:12px 24px;
    border-radius:10px;
    text-decoration:none;
    font-weight:600;
    font-size:15px;
    transition:all 0.3s;
    border:1px solid rgba(255,255,255,0.3);
}

.top-header a:hover{
    background:rgba(255,255,255,0.3);
    transform:translateY(-2px);
}

.excel-btn{
    background:rgba(255,255,255,0.2);
    color:#fff;
    padding:10px 16px;
    border-radius:10px;
    text-decoration:none;
    font-weight:600;
    font-size:15px;
    transition:all 0.3s;
    border:1px solid rgba(255,255,255,0.3);
    cursor:pointer;
    display:flex;
    align-items:center;
    gap:6px;
}

.excel-btn:hover{
    background:rgba(255,255,255,0.3);
    transform:translateY(-2px);
}

.filter-bar{
    background:rgba(255,255,255,0.98);
    border-radius:12px;
    padding:16px 24px;
    display:flex;
    gap:20px;
    align-items:center;
    flex-wrap:wrap;
    margin-bottom:16px;
    box-shadow:0 4px 16px rgba(0,0,0,0.08);
}

.filter-bar label{
    font-weight:600;
    color:#667eea;
    font-size:14px;
}

.filter-bar select{
    padding:8px 32px 8px 12px;
    border:2px solid #e2e8f0;
    border-radius:8px;
    font-size:14px;
    background:#f8fafc;
    cursor:pointer;
    appearance:none;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23667eea' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    background-repeat:no-repeat;
    background-position:right 10px center;
    transition:all 0.3s;
}

.filter-bar select:focus{
    border-color:#667eea;
    outline:none;
    box-shadow:0 0 0 3px rgba(102,126,234,0.1);
}

.legend{
    margin-left:auto;
    display:flex;
    gap:16px;
    align-items:center;
    font-size:13px;
}

.legend-item{
    display:flex;
    align-items:center;
    gap:6px;
    color:#64748b;
    font-weight:500;
}

.sig{
    width:16px;
    height:16px;
    border-radius:50%;
    box-shadow:0 2px 4px rgba(0,0,0,0.2);
}

.s-g{background:#10b981}
.s-y{background:#fbbf24}
.s-x{background:#94a3b8}

.table-container{
    background:rgba(255,255,255,0.98);
    border-radius:16px;
    box-shadow:0 8px 32px rgba(0,0,0,0.12);
    overflow:hidden;
}

.table-wrap{
    overflow-x:auto;
    overflow-y:auto;
    max-height:calc(100vh - 220px);
}

table{
    border-collapse:collapse;
    white-space:nowrap;
    min-width:100%;
    background:#fff;
}

thead th{
    position:sticky;
    top:0;
    z-index:10;
    background:#667eea;
    color:#fff;
    font-weight:600;
    font-size:12px;
    padding:11px 9px;
    border:1px solid #94a3b8;
    text-align:center;
}

thead tr.gh th{
    background:#5a67d8;
    font-size:13px;
    padding:9px;
    border:1px solid #94a3b8;
}

td.sc,th.sc{
    position:sticky;
    z-index:5;
    background:#f1f5f9;
}

th.sc{
    background:#667eea !important;
    z-index:15;
}

td.sc{
    background:#f1f5f9;
}

.c0{left:0;min-width:54px}
.c1{left:54px;min-width:46px}
.c2{left:100px;min-width:58px}
.c3{left:158px;min-width:70px}
.c4{left:228px;min-width:120px}
.c5{left:348px;min-width:100px}

th.c0,th.c1,th.c2,th.c3,th.c4,th.c5{
    background:#667eea !important;
    z-index:15 !important;
}

tbody tr:nth-child(even) td.sc{background:#f1f5f9}
tbody tr:nth-child(odd) td.sc{background:#e2e8f0}
tbody tr:hover td.sc{background:#ddd6fe !important}

tbody td{
    padding:9px 11px;
    border:1px solid #94a3b8;
    font-size:13px;
    text-align:center;
    vertical-align:middle;
}

td.left{text-align:left}

td.act-cell{
    text-align:left;
    max-width:300px;
    white-space:normal;
    word-break:break-all;
    line-height:1.5;
}

tbody tr:nth-child(even) td{background:#f8fafc}
tbody tr:nth-child(odd) td{background:#fff}
tbody tr:hover td{background:#e0e7ff !important}

tfoot td{
    padding:10px 11px;
    border:1px solid #94a3b8;
    font-size:13px;
    text-align:center;
    font-weight:700;
    background:#fef3c7;
    color:#78350f;
}

th.gs{background:#3b82f6;border:1px solid #94a3b8}
th.gv{background:#10b981;border:1px solid #94a3b8}
th.gr{background:#fbbf24;color:#78350f;border:1px solid #94a3b8}
th.ge{background:#8b5cf6;border:1px solid #94a3b8}

tr.gh .g-s{background:#2563eb;border:1px solid #94a3b8}
tr.gh .g-v{background:#059669;border:1px solid #94a3b8}
tr.gh .g-r{background:#f59e0b;border:1px solid #94a3b8}
tr.gh .g-e{background:#7c3aed;border:1px solid #94a3b8}
tr.gh .g-c{background:#5a67d8;border:1px solid #94a3b8}

.np{color:#10b981;font-weight:700}
.nn{color:#ef4444;font-weight:700}

.footer-info{
    padding:12px 24px;
    font-size:14px;
    color:#64748b;
    background:rgba(255,255,255,0.95);
    border-top:2px solid #e2e8f0;
    font-weight:600;
}

.row-actions{
    display:flex;
    gap:6px;
    align-items:center;
    justify-content:center;
}

.icon-btn{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    width:28px;
    height:28px;
    border-radius:6px;
    cursor:pointer;
    transition:all 0.3s;
    border:none;
    background:#fff;
    font-size:14px;
    text-decoration:none;
    box-shadow:0 2px 4px rgba(0,0,0,0.1);
}

.icon-edit{color:#3b82f6}
.icon-edit:hover{background:#3b82f6;color:#fff;transform:scale(1.1)}

.icon-del{color:#ef4444}
.icon-del:hover{background:#ef4444;color:#fff;transform:scale(1.1)}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
</head>
<body>

<div class="top-header">
    <h2>📊 설비 투자비 활동 실적 조회</h2>
    <div class="top-header-right">
        <button class="excel-btn" onclick="downloadExcel()">📥 Excel 다운로드</button>
        <a href="/">◀ 입력 페이지</a>
    </div>
</div>

<div class="filter-bar">
    <label>제품</label>
    <select id="fp" onchange="applyFilter(); updateFilterCorporations();">
        <option value="">전체</option>
        <option>키친</option><option>빌트인쿠킹</option><option>리빙</option><option>부품</option><option>ES</option>
    </select>
    
    <label>법인</label>
    <select id="fc" onchange="applyFilter()">
        <option value="">전체</option>
    </select>
    
    <label>투자유형</label>
    <select id="ft" onchange="applyFilter()">
        <option value="">전체</option><option>확장</option><option>경상</option>
    </select>
    
    <label>투자목적</label>
    <select id="fpu" onchange="applyFilter()">
        <option value="">전체</option>
    </select>
    
    <div class="legend">
        <div class="legend-item"><span class="sig s-g"></span> 목표 초과 (HS: 30% 이상 / ES: 50% 이상)</div>
        <div class="legend-item"><span class="sig s-y"></span> 목표 미달</div>
        <div class="legend-item"><span class="sig s-x"></span> 미입력</div>
    </div>
</div>

<div class="table-container">
    <div class="table-wrap">
        <table id="mainTable">
            <thead>
                <tr class="gh">
                    <th class="sc c0 g-c" colspan="6">투자 분류</th>
                    <th class="g-s" colspan="7">📅 투자 주요 일정</th>
                    <th class="g-v" colspan="4">💰 투자절감</th>
                    <th class="g-r" colspan="11">📊 절감 활동 및 실적</th>
                    <th class="g-e" colspan="3">🎯 목표</th>
                </tr>
                <tr>
                    <th class="sc c0">수정/<br>삭제</th>
                    <th class="sc c1">제품</th>
                    <th class="sc c2">법인</th>
                    <th class="sc c3">투자<br>유형</th>
                    <th class="sc c4">투자항목</th>
                    <th class="sc c5">투자목적</th>
                    <th class="gs">발주목표</th><th class="gs">발주실적</th>
                    <th class="gs">셋업목표</th><th class="gs">셋업실적</th>
                    <th class="gs">양산목표</th><th class="gs">양산실적</th>
                    <th class="gs">연기사유</th>
                    <th class="gv">Base</th>
                    <th class="gv">발주가<br>목표</th>
                    <th class="gv">발주가<br>실적</th>
                    <th class="gv">절감<br>목표</th>
                    <th class="gr">절감<br>실적<br>(합계)</th>
                    <th class="gr">①신기술<br>신공법</th>
                    <th class="gr">②염가형<br>부품</th>
                    <th class="gr">③중국/<br>Local</th>
                    <th class="gr">④중국/한국<br>Collabo</th>
                    <th class="gr">⑤컨테이너<br>최소화</th>
                    <th class="gr">⑥출장<br>최소화</th>
                    <th class="gr">⑦유휴<br>설비</th>
                    <th class="gr">⑧사양<br>최적화</th>
                    <th class="gr">⑨기타</th>
                    <th class="gr">활동내용</th>
                    <th class="ge">절감률<br>목표(%)</th>
                    <th class="ge">절감률<br>실적(%)</th>
                    <th class="ge">Signal</th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
            <tfoot id="tableFoot"></tfoot>
        </table>
    </div>
    <div class="footer-info" id="footerInfo">총 0건</div>
</div>

<script>
const DATA = {{ processed_json | safe }};
const MONTHS = {{ months_json | safe }};
const CORPORATIONS = {{ corporations_json | safe }};
const ALL_PURPOSES = {{ all_purposes_json | safe }};

console.log("✅ 데이터 로드:", DATA.length, "건");

function f(v){ return (v!=null&&v!=="")? v : "-"; }

function deleteRow(id){
    if(!confirm("정말 삭제하시겠습니까?")) return;
    fetch("/delete/"+id, {method:"POST"})
        .then(r=>r.json())
        .then(d=>{ if(d.success) location.reload(); });
}

function updateFilterCorporations() {
    const product = document.getElementById('fp').value;
    const corpSelect = document.getElementById('fc');
    
    let corps = [];
    if(product && CORPORATIONS[product]) {
        corps = CORPORATIONS[product];
    } else {
        const allCorps = new Set();
        Object.values(CORPORATIONS).forEach(arr => arr.forEach(c => allCorps.add(c)));
        corps = Array.from(allCorps).sort();
    }
    
    const currentValue = corpSelect.value;
    corpSelect.innerHTML = '<option value="">전체</option>';
    corps.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        corpSelect.appendChild(opt);
    });
    
    if(corps.includes(currentValue)) {
        corpSelect.value = currentValue;
    }
}

function renderTable(data){
    const tb = document.getElementById("tableBody");
    const tf = document.getElementById("tableFoot");
    let out = "";
    
    let totals = {
        base: 0, order_price_target: 0, order_price_actual: 0,
        saving_target: 0, saving_actual: 0,
        r1: 0, r2: 0, r3: 0, r4: 0, r5: 0, r6: 0, r7: 0, r8: 0, r9: 0
    };

    data.forEach(r => {
        const rid = r[0];
        const product = r[2] || "";
        let h = "<tr>";

        h += "<td class='sc c0'><div class='row-actions'>";
        h += "<a href='/edit/"+rid+"' class='icon-btn icon-edit' title='수정'>✏️</a>";
        h += "<button class='icon-btn icon-del' title='삭제' onclick='deleteRow("+rid+")'>🗑️</button>";
        h += "</div></td>";

        h += "<td class='sc c1'>"+f(r[2])+"</td>";
        h += "<td class='sc c2'>"+f(r[3])+"</td>";
        h += "<td class='sc c3'>"+f(r[1])+"</td>";
        h += "<td class='sc c4 left'>"+f(r[5])+"</td>";
        h += "<td class='sc c5'>"+f(r[4])+"</td>";

        h += "<td>"+f(r[6])+"</td><td>"+f(r[7])+"</td>";
        h += "<td>"+f(r[8])+"</td><td>"+f(r[9])+"</td>";
        h += "<td>"+f(r[10])+"</td><td>"+f(r[11])+"</td>";
        h += "<td class='left'>"+f(r[12])+"</td>";

        const base = parseFloat(r[13]) || 0;
        const opt = parseFloat(r[14]) || 0;
        const opa = parseFloat(r[15]) || 0;
        const sgt = parseFloat(r[16]) || 0;
        const sga = parseFloat(r[17]) || 0;
        
        totals.base += base;
        totals.order_price_target += opt;
        totals.order_price_actual += opa;
        totals.saving_target += sgt;
        totals.saving_actual += sga;

        h += "<td>"+f(r[13])+"</td>";
        h += "<td>"+f(r[14])+"</td>";
        h += "<td>"+f(r[15])+"</td>";
        h += "<td>"+f(r[16])+"</td>";
        h += "<td>"+f(r[17])+"</td>";
        
        for(let i=18;i<=26;i++){
            const val = parseFloat(r[i]) || 0;
            totals['r'+(i-17)] += val;
            h += "<td>"+f(r[i])+"</td>";
        }

        h += "<td class='act-cell'>"+f(r[28])+"</td>";

        // ===== 핵심: 여기서 절감률 목표, 실적, Signal을 모두 계산 =====
        
        // 1. 절감률 목표: 제품에 따라 30% 또는 50%
        const rateTarget = (product === "ES") ? 50 : 30;
        
        // 2. 절감률 실적: (절감실적 ÷ Base) × 100
        let rateActual = "-";
        let rateActualNum = 0;
        
        if(base > 0 && sga > 0) {
            rateActualNum = (sga / base) * 100;
            rateActual = rateActualNum.toFixed(1);
        } else if(base > 0 && sga === 0) {
            rateActualNum = 0;
            rateActual = "0";
        }
        
        // 3. Signal 계산
        let signalClass = "s-x"; // 기본값: 회색(미입력)
        
        if(base > 0 && sga > 0) {
            // 절감실적이 있는 경우: 목표 대비 비교
            if(rateActualNum >= rateTarget) {
                signalClass = "s-g"; // 초록색: 목표 이상
            } else {
                signalClass = "s-y"; // 주황색: 목표 미달
            }
        }
        
        console.log(`ID=${rid}, 제품=${product}, Base=${base}, 절감실적=${sga}, 목표=${rateTarget}%, 실적=${rateActual}%, Signal=${signalClass}`);
        
        h += "<td>"+rateTarget+"%</td>";
        h += "<td>"+(rateActual !== "-" ? rateActual+"%" : "-")+"</td>";
        h += "<td><span class='sig "+signalClass+"'></span></td>";

        h += "</tr>";
        out += h;
    });

    tb.innerHTML = out;
    
    // 합계 행
    let footHtml = "<tr>";
    footHtml += "<td colspan='6' style='text-align:center;background:#fef9c3;'>합 계</td>";
    footHtml += "<td colspan='7' style='background:#fef9c3;'></td>";
    footHtml += "<td>"+totals.base.toFixed(2)+"</td>";
    footHtml += "<td>"+totals.order_price_target.toFixed(2)+"</td>";
    footHtml += "<td>"+totals.order_price_actual.toFixed(2)+"</td>";
    footHtml += "<td>"+totals.saving_target.toFixed(2)+"</td>";
    footHtml += "<td>"+totals.saving_actual.toFixed(2)+"</td>";
    for(let i=1;i<=9;i++){
        footHtml += "<td>"+totals['r'+i].toFixed(2)+"</td>";
    }
    footHtml += "<td colspan='4' style='background:#fef9c3;'></td>";
    footHtml += "</tr>";
    tf.innerHTML = footHtml;
    
    document.getElementById("footerInfo").textContent = "총 "+data.length+"건";
}

function applyFilter(){
    const fp=document.getElementById("fp").value;
    const fc=document.getElementById("fc").value;
    const ft=document.getElementById("ft").value;
    const fpu=document.getElementById("fpu").value;
    renderTable(DATA.filter(r=>{
        if(fp&&r[2]!==fp) return false;
        if(fc&&r[3]!==fc) return false;
        if(ft&&r[1]!==ft) return false;
        if(fpu&&r[4]!==fpu) return false;
        return true;
    }));
}

function downloadExcel() {
    const wb = XLSX.utils.book_new();
    
    const headers = [
        ["제품", "법인", "투자유형", "투자항목", "투자목적",
         "발주목표", "발주실적", "셋업목표", "셋업실적", "양산목표", "양산실적", "연기사유",
         "Base", "발주가목표", "발주가실적", "절감목표", "절감실적",
         "①신기술신공법", "②염가형부품", "③중국/Local", "④중국/한국Collabo",
         "⑤컨테이너최소화", "⑥출장최소화", "⑦유휴설비", "⑧사양최적화", "⑨기타",
         "활동내용", "절감률목표(%)", "절감률실적(%)"]
    ];
    
    const rows = DATA.map(r => {
        const product = r[2] || "";
        const base = parseFloat(r[13]) || 0;
        const sga = parseFloat(r[17]) || 0;
        const rateTarget = (product === "ES") ? 50 : 30;
        let rateActual = "-";
        if(base > 0 && sga > 0) {
            rateActual = ((sga / base) * 100).toFixed(1);
        } else if(base > 0) {
            rateActual = "0";
        }
        
        return [
            r[2], r[3], r[1], r[5], r[4],
            r[6], r[7], r[8], r[9], r[10], r[11], r[12],
            r[13], r[14], r[15], r[16], r[17],
            r[18], r[19], r[20], r[21], r[22], r[23], r[24], r[25], r[26],
            r[28], rateTarget, rateActual
        ];
    });
    
    const ws = XLSX.utils.aoa_to_sheet([...headers, ...rows]);
    XLSX.utils.book_append_sheet(wb, ws, "투자실적");
    XLSX.writeFile(wb, "설비투자비_활동실적_" + new Date().toISOString().slice(0,10) + ".xlsx");
}

window.onload = function() {
    console.log("🎬 페이지 로드 완료");
    updateFilterCorporations();
    
    const purposeSelect = document.getElementById('fpu');
    ALL_PURPOSES.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        purposeSelect.appendChild(opt);
    });
    
    renderTable(DATA);
    console.log("✅ 테이블 렌더링 완료");
}
</script>

</body>
</html>
"""

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Flask 서버 시작")
    print(f"📁 DB: {DB_NAME}")
    print("📍 주소: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)