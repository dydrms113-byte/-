from flask import Flask, request, redirect, render_template_string, jsonify
import psycopg2
import psycopg2.extras
from datetime import datetime
import os
import json

app = Flask(__name__)

# ===== Supabase PostgreSQL 연결 설정 =====
# Render 환경변수에 DATABASE_URL을 설정하세요
# Supabase 대시보드 → Settings → Database → Connection string (URI) 복사
DATABASE_URL = os.environ.get("DATABASE_URL", "")

def get_conn():
    """PostgreSQL 연결 생성"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    return conn

def get_conn_tuple():
    """튜플 형태 결과를 위한 연결 (기존 코드 호환)"""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn

def init_db():
    conn = get_conn_tuple()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS investment (
        id SERIAL PRIMARY KEY,
        invest_type TEXT, product TEXT, corporation TEXT, purpose TEXT,
        invest_item TEXT, order_target TEXT, order_actual TEXT,
        setup_target TEXT, setup_actual TEXT, mass_target TEXT, mass_actual TEXT,
        delay_reason TEXT, base_amount REAL, order_price_target REAL,
        order_price_actual REAL, saving_target REAL, saving_actual REAL,
        reduce_1 REAL, reduce_2 REAL, reduce_3 REAL, reduce_4 REAL,
        reduce_5 REAL, reduce_6 REAL, reduce_7 REAL, reduce_8 REAL,
        reduce_9 REAL, saving_total REAL, activity TEXT,
        created_at TEXT, updated_at TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS investment_monthly (
        id INTEGER, year_month TEXT,
        monthly_target REAL DEFAULT 0, monthly_actual REAL DEFAULT 0,
        PRIMARY KEY (id, year_month),
        FOREIGN KEY (id) REFERENCES investment(id) ON DELETE CASCADE
    )""")
    conn.commit(); conn.close()

init_db()

PRODUCTS = ["키친", "빌트인쿠킹", "리빙", "부품", "ES"]
CORPORATIONS = {
    "키친": ["KR","TR","MN","IN_T","IL_N","IL_P","VH","RA"],
    "빌트인쿠킹": ["KR","MN","IL_N","MZ","VH"],
    "리빙": ["KR","PN","TH","VH","IL_N","IL_P","TN","MX","EG","RA"],
    "ES": ["KR","TA","IL_N","IL_P","TH","SR","AZ","AT","AL"],
    "부품": ["KR","TA","PN","TR","TH","IL_N","VH","MN"]
}
ALL_PURPOSES = ["신규라인","자동화","라인 개조","Overhaul","신모델 대응","T/Time 향상","고장 수리","안전","설비 이설","노후 교체","설비 개선","기타"]
MONTHS = [f"{y}-{m:02d}" for y in [2026, 2027] for m in range(1, 13)]

def nz(v, default=0.0):
    if v is None or v == "": return default
    try: return float(v) if isinstance(default, float) else str(v)
    except: return default

def get_processed_rows():
    conn = get_conn_tuple(); c = conn.cursor()
    c.execute("SELECT * FROM investment ORDER BY id DESC"); rows = c.fetchall(); conn.close()
    processed = []
    for r in rows:
        r = list(r)
        base = r[13] if r[13] else 0; sav_act = r[17] if r[17] else 0; product = r[2] if r[2] else ""
        rate_target = 50 if product == "ES" else 30
        rate_actual = "-"
        if base and base != 0: rate_actual = round((sav_act/base)*100, 1) if sav_act else 0
        r.append(rate_target); r.append(rate_actual)
        timestamp = r[30] if len(r) > 30 and r[30] else (r[29] if len(r) > 29 else "")
        r.append(timestamp); processed.append(r)
    return processed

@app.route("/")
@app.route("/edit/<int:row_id>")
def index(row_id=None):
    edit_data = None
    if row_id:
        conn = get_conn_tuple(); c = conn.cursor()
        c.execute("SELECT * FROM investment WHERE id = %s", (row_id,)); edit_data = c.fetchone(); conn.close()
        if not edit_data: return "데이터를 찾을 수 없습니다.", 404
    return render_template_string(INPUT_TPL, products=PRODUCTS, corporations_json=json.dumps(CORPORATIONS, ensure_ascii=False), all_purposes=ALL_PURPOSES, edit_data=edit_data, row_id=row_id)

@app.route("/save", methods=["POST"])
def save():
    try:
        f = request.form; conn = get_conn_tuple(); c = conn.cursor()
        row_id = f.get("row_id"); now = datetime.now().strftime("%Y-%m-%d %H:%M")
        values = (f.get("invest_type") or "", f.get("product") or "", f.get("corporation") or "", f.get("purpose") or "",
            f.get("invest_item") or "", f.get("order_target") or "", f.get("order_actual") or "",
            f.get("setup_target") or "", f.get("setup_actual") or "", f.get("mass_target") or "", f.get("mass_actual") or "",
            f.get("delay_reason") or "", nz(f.get("base_amount")), nz(f.get("order_price_target")),
            nz(f.get("order_price_actual")), nz(f.get("saving_target")), nz(f.get("saving_actual")),
            nz(f.get("reduce_1")), nz(f.get("reduce_2")), nz(f.get("reduce_3")), nz(f.get("reduce_4")),
            nz(f.get("reduce_5")), nz(f.get("reduce_6")), nz(f.get("reduce_7")), nz(f.get("reduce_8")),
            nz(f.get("reduce_9")), nz(f.get("saving_total")), f.get("activity") or "")
        if row_id:
            c.execute("""UPDATE investment SET invest_type=%s,product=%s,corporation=%s,purpose=%s,invest_item=%s,
                order_target=%s,order_actual=%s,setup_target=%s,setup_actual=%s,mass_target=%s,mass_actual=%s,delay_reason=%s,
                base_amount=%s,order_price_target=%s,order_price_actual=%s,saving_target=%s,saving_actual=%s,
                reduce_1=%s,reduce_2=%s,reduce_3=%s,reduce_4=%s,reduce_5=%s,reduce_6=%s,reduce_7=%s,reduce_8=%s,reduce_9=%s,
                saving_total=%s,activity=%s,updated_at=%s WHERE id=%s""", values + (now, row_id))
            c.execute("DELETE FROM investment_monthly WHERE id=%s", (row_id,)); target_id = int(row_id)
        else:
            c.execute("""INSERT INTO investment (invest_type,product,corporation,purpose,invest_item,
                order_target,order_actual,setup_target,setup_actual,mass_target,mass_actual,delay_reason,
                base_amount,order_price_target,order_price_actual,saving_target,saving_actual,
                reduce_1,reduce_2,reduce_3,reduce_4,reduce_5,reduce_6,reduce_7,reduce_8,reduce_9,
                saving_total,activity,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id""",
                values + (now, now)); target_id = c.fetchone()[0]
        conn.commit()
        ot = f.get("order_target") or ""; oa = f.get("order_actual") or ""
        st = nz(f.get("saving_target")); sa = nz(f.get("saving_actual"))
        for ym in MONTHS:
            t = st if ot == ym else 0.0; a = sa if oa == ym else 0.0
            c.execute("""INSERT INTO investment_monthly (id, year_month, monthly_target, monthly_actual)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (id, year_month) DO UPDATE SET monthly_target=EXCLUDED.monthly_target, monthly_actual=EXCLUDED.monthly_actual""",
                (target_id, ym, t, a))
        conn.commit(); conn.close(); return redirect("/list")
    except Exception as e:
        import traceback; traceback.print_exc(); return f"저장 오류: {e}", 500

@app.route("/dashboard")
def dashboard():
    processed = get_processed_rows()
    months_2026 = [f"2026-{m:02d}" for m in range(1,13)]
    mt = {m: 0.0 for m in months_2026}; ma = {m: 0.0 for m in months_2026}
    for r in processed:
        ot = r[6] if r[6] else ""; oa = r[7] if r[7] else ""
        st = float(r[16]) if r[16] else 0.0; sa = float(r[17]) if r[17] else 0.0
        if ot in mt: mt[ot] += st
        if oa in ma: ma[oa] += sa
    monthly_json = json.dumps({"labels": [f"{m}월" for m in range(1,13)],
        "target": [round(mt[f"2026-{m:02d}"],2) for m in range(1,13)],
        "actual": [round(ma[f"2026-{m:02d}"],2) for m in range(1,13)]}, ensure_ascii=False)
    return render_template_string(DASHBOARD_TPL, processed_json=json.dumps(processed, ensure_ascii=False),
        corporations_json=json.dumps(CORPORATIONS, ensure_ascii=False), monthly_json=monthly_json,
        all_purposes_json=json.dumps(ALL_PURPOSES, ensure_ascii=False))

@app.route("/list")
def list_page():
    conn = get_conn_tuple(); c = conn.cursor()
    c.execute("SELECT * FROM investment ORDER BY id DESC"); rows = c.fetchall(); conn.close()
    processed = []
    for r in rows:
        r = list(r); base = r[13] if r[13] else 0; sav_act = r[17] if r[17] else 0; product = r[2] if r[2] else ""
        rt = 50 if product == "ES" else 30; ra = "-"
        if base and base != 0: ra = round((sav_act/base)*100, 1) if sav_act else 0
        r.append(rt); r.append(ra)
        ts = r[30] if len(r) > 30 and r[30] else r[29]; r.append(ts); processed.append(r)
    return render_template_string(LIST_TPL, processed_json=json.dumps(processed, ensure_ascii=False),
        months_json=json.dumps(MONTHS, ensure_ascii=False), corporations_json=json.dumps(CORPORATIONS, ensure_ascii=False),
        all_purposes_json=json.dumps(ALL_PURPOSES, ensure_ascii=False))

@app.route("/delete/<int:row_id>", methods=["POST"])
def delete_row(row_id):
    conn = get_conn_tuple(); c = conn.cursor()
    c.execute("DELETE FROM investment WHERE id=%s", (row_id,)); c.execute("DELETE FROM investment_monthly WHERE id=%s", (row_id,))
    conn.commit(); conn.close(); return jsonify({"success": True})

INPUT_TPL = r"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>설비투자비 한계돌파 실적 관리 시스템</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans KR',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:16px;font-size:14px}
.header{background:linear-gradient(135deg,#4a5f9d 0%,#5a4a8a 100%);border-radius:12px;padding:18px 30px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 4px 12px rgba(0,0,0,0.2);max-width:1600px;margin-left:auto;margin-right:auto}
.header h1{color:white;font-size:22px;font-weight:700;display:flex;align-items:center;gap:10px}
.header-right{display:flex;gap:12px;align-items:center}
.header-btn{background:rgba(255,255,255,0.15);color:white;border:1px solid rgba(255,255,255,0.3);padding:10px 20px;border-radius:8px;font-size:14px;font-weight:500;text-decoration:none;transition:all 0.3s;display:flex;align-items:center;gap:6px}
.header-btn:hover{background:rgba(255,255,255,0.25)}
.lang-toggle-header{display:flex;gap:4px;background:rgba(255,255,255,0.1);border-radius:20px;padding:3px;border:1px solid rgba(255,255,255,0.2);margin-right:8px}
.lang-btn-h{padding:6px 14px;border-radius:18px;font-size:12px;font-weight:700;cursor:pointer;border:none;background:transparent;color:rgba(255,255,255,0.6);transition:all 0.25s}
.lang-btn-h.active{background:rgba(255,255,255,0.9);color:#667eea}
.container{max-width:1600px;margin:0 auto}
.row{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}
.card{background:white;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08)}
.card-full{grid-column:1/-1}
.card-header{padding:16px 24px;font-weight:700;font-size:16px;display:flex;align-items:center;gap:8px;border-bottom:3px solid}
.card-header.pink{background:linear-gradient(to bottom,#fce7f3,#fbcfe8);color:#be185d;border-bottom-color:#ec4899}
.card-header.cyan{background:linear-gradient(to bottom,#cffafe,#a5f3fc);color:#0e7490;border-bottom-color:#06b6d4}
.card-header.amber{background:linear-gradient(to bottom,#fef3c7,#fde68a);color:#b45309;border-bottom-color:#f59e0b}
.card-header.blue{background:linear-gradient(to bottom,#dbeafe,#bfdbfe);color:#1e40af;border-bottom-color:#3b82f6}
.card-header.emerald{background:linear-gradient(to bottom,#d1fae5,#a7f3d0);color:#047857;border-bottom-color:#10b981}
.card-header.violet{background:linear-gradient(to bottom,#ede9fe,#ddd6fe);color:#6d28d9;border-bottom-color:#8b5cf6}
.card-body{padding:24px}
.form-group{margin-bottom:18px}
.form-label{display:flex;align-items:center;gap:6px;font-size:14px;font-weight:600;color:#64748b;margin-bottom:10px}
.toggle-group{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.toggle-btn{padding:14px;border:2px solid #cbd5e1;border-radius:10px;background:#f1f5f9;text-align:center;font-weight:600;font-size:15px;color:#64748b;cursor:pointer;transition:all 0.3s}
.toggle-btn.active{background:#dbeafe;border-color:#3b82f6;color:#1e40af}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
input[type="text"],input[type="number"],input[type="month"],select,textarea{width:100%;padding:12px 16px;border:2px solid #cbd5e1;border-radius:10px;font-size:15px;font-family:'Noto Sans KR',sans-serif;background:#f1f5f9;transition:all 0.3s}
input:focus,select:focus,textarea:focus{outline:none;border-color:#667eea;background:white;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
textarea{resize:vertical;min-height:100px;line-height:1.6}
input[readonly]{background:#f1f5f9;border:3px solid #8b5cf6;font-weight:700;color:#1e40af}
.info-box{background:#dbeafe;border-left:4px solid #3b82f6;padding:14px 18px;border-radius:8px;margin-top:12px;margin-bottom:12px}
.info-box-title{font-size:13px;font-weight:600;color:#1e40af;margin-bottom:4px}
.info-box-text{font-size:12px;color:#3b82f6;line-height:1.6}
.table-wrapper{overflow-x:auto}
.reduce-table{width:100%;border-collapse:separate;border-spacing:0}
.reduce-table th{background:#f3f4f6;color:#374151;font-size:12px;padding:12px 10px;text-align:center;font-weight:600;border:1px solid #e5e7eb;white-space:nowrap}
.reduce-table th:nth-child(2){background:#dcfce7;color:#065f46;font-weight:700}
.reduce-table td{padding:12px 10px;text-align:center;background:white;border:1px solid #e5e7eb}
.reduce-table td:first-child{font-weight:600;color:#374151;background:#f9fafb}
.reduce-table td:nth-child(2) input{background:#f1f5f9;font-weight:700;color:#065f46;font-size:15px;border:2px solid #cbd5e1}
.reduce-table input{max-width:90px;text-align:center;background:#f1f5f9;padding:10px;border:2px solid #cbd5e1;border-radius:6px}
.reduce-number{display:block;font-size:11px;color:#9ca3af;font-weight:700;margin-bottom:3px}
.activity-section{margin-top:20px;padding:20px;background:#f9fafb;border-radius:10px;border:1px solid #e5e7eb}
.activity-label{display:flex;align-items:center;gap:6px;font-size:14px;font-weight:600;color:#374151;margin-bottom:12px}
.button-group{display:flex;justify-content:center;gap:16px;margin-top:28px;padding:26px;background:white;border-radius:14px}
.btn-primary{background:linear-gradient(135deg,#10b981 0%,#059669 100%);color:white;border:none;padding:16px 48px;border-radius:10px;font-size:16px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:8px;box-shadow:0 4px 16px rgba(16,185,129,0.3);transition:all 0.3s}
.btn-primary:hover{transform:translateY(-2px)}
.btn-secondary{background:linear-gradient(135deg,#6366f1 0%,#4f46e5 100%);color:white;border:none;padding:16px 48px;border-radius:10px;font-size:16px;font-weight:700;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:8px;box-shadow:0 4px 16px rgba(99,102,241,0.3);transition:all 0.3s}
.btn-secondary:hover{transform:translateY(-2px)}
</style></head><body>
<div class="header">
  <h1>📋 <span class="i18n" data-ko="설비투자비 한계돌파 실적 관리 시스템" data-en="Facility Investment Breakthrough System">설비투자비 한계돌파 실적 관리 시스템</span></h1>
  <div class="header-right">
    <div class="lang-toggle-header">
      <button class="lang-btn-h active" id="langKoI" onclick="setLang('ko')">🇰🇷 한글</button>
      <button class="lang-btn-h" id="langEnI" onclick="setLang('en')">🇺🇸 ENG</button>
    </div>
    <a href="/dashboard" class="header-btn">🏠 <span class="i18n" data-ko="대시보드" data-en="Dashboard">대시보드</span></a>
    <a href="/" class="header-btn">📄 Data <span class="i18n" data-ko="입력" data-en="Entry">입력</span></a>
    <a href="/list" class="header-btn">📊 <span class="i18n" data-ko="투자실적 조회" data-en="Records">투자실적 조회</span></a>
  </div>
</div>
<div class="container">
  <form method="post" action="/save" id="mainForm">
  {%- if row_id -%}<input type="hidden" name="row_id" value="{{ row_id }}">{%- endif -%}
  <div class="row">
    <div class="card"><div class="card-header pink">📌 <span class="i18n" data-ko="투자 분류" data-en="Investment Classification">투자 분류</span></div><div class="card-body">
        <div class="form-group"><div class="form-label">💼 <span class="i18n" data-ko="투자 유형" data-en="Investment Type">투자 유형</span></div>
          <div class="toggle-group">
            <div class="toggle-btn {%- if not edit_data or edit_data[1]=='확장' %} active{%- endif -%}" onclick="selectType(this,'확장')"><span class="i18n" data-ko="확장" data-en="Expansion">확장</span></div>
            <div class="toggle-btn {%- if edit_data and edit_data[1]=='경상' %} active{%- endif -%}" onclick="selectType(this,'경상')"><span class="i18n" data-ko="경상" data-en="Recurring">경상</span></div>
          </div><input type="hidden" name="invest_type" id="invest_type" value="{%- if edit_data -%}{{ edit_data[1] or '확장' }}{%- else -%}확장{%- endif -%}"></div>
        <div class="form-row">
          <div class="form-group"><div class="form-label">📦 <span class="i18n" data-ko="제품" data-en="Product">제품</span></div>
            <select name="product" id="product" onchange="updateCorporations()">{%- for p in products -%}<option value="{{ p }}" {%- if edit_data and edit_data[2]==p %} selected{%- endif -%}>{{ p }}</option>{%- endfor -%}</select></div>
          <div class="form-group"><div class="form-label">🌍 <span class="i18n" data-ko="법인" data-en="Corporation">법인</span></div>
            <select name="corporation" id="corporation"></select></div>
        </div>
        <div class="info-box"><div class="info-box-title">💡 TIP</div><div class="info-box-text"><span class="i18n" data-ko="• 5천만원 미만인 경상투자 건은 Base금액을 집행가로 기입
• 해외 법인은 HQ 생산기술에서 검토/지원해주는 투자 건만 기입" data-en="• For recurring investments under 50M KRW, enter Base amount as execution price
• For overseas subsidiaries, enter only investments reviewed/supported by HQ Prod. Tech.">• 5천만원 미만인 경상투자 건은 Base금액을 집행가로 기입<br>• 해외 법인은 HQ 생산기술에서 검토/지원해주는 투자 건만 기입</span></div></div>
    </div></div>
    <div class="card"><div class="card-header cyan">📋 <span class="i18n" data-ko="투자 항목 상세" data-en="Investment Details">투자 항목 상세</span></div><div class="card-body">
        <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="투자목적" data-en="Purpose">투자목적</span></div>
          <select name="purpose" id="purpose_select">{%- for p in all_purposes -%}<option value="{{ p }}" {%- if edit_data and edit_data[4]==p %} selected{%- endif -%}>{{ p }}</option>{%- endfor -%}</select></div>
        <div class="form-group"><div class="form-label">📝 <span class="i18n" data-ko="투자항목" data-en="Item">투자항목</span></div>
          <input type="text" name="invest_item" value="{%- if edit_data -%}{{ edit_data[5] or '' }}{%- endif -%}" placeholder="예: 창원 선진화 오븐라인" id="invest_item_input"></div>
    </div></div>
  </div>
  <div class="card card-full"><div class="card-header amber">📅 <span class="i18n" data-ko="투자 주요 일정" data-en="Schedule">투자 주요 일정</span></div><div class="card-body">
      <div class="form-row">
        <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="발주 목표" data-en="Order Target">발주 목표</span></div><input type="month" name="order_target" class="month-i" value="{%- if edit_data -%}{{ edit_data[6] or '' }}{%- endif -%}"></div>
        <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="발주 실적" data-en="Order Actual">발주 실적</span></div><input type="month" name="order_actual" class="month-i" value="{%- if edit_data -%}{{ edit_data[7] or '' }}{%- endif -%}"></div></div>
      <div class="form-row">
        <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="셋업 목표" data-en="Setup Target">셋업 목표</span></div><input type="month" name="setup_target" class="month-i" value="{%- if edit_data -%}{{ edit_data[8] or '' }}{%- endif -%}"></div>
        <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="셋업 실적" data-en="Setup Actual">셋업 실적</span></div><input type="month" name="setup_actual" class="month-i" value="{%- if edit_data -%}{{ edit_data[9] or '' }}{%- endif -%}"></div></div>
      <div class="form-row">
        <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="양산 목표" data-en="Mass Target">양산 목표</span></div><input type="month" name="mass_target" class="month-i" value="{%- if edit_data -%}{{ edit_data[10] or '' }}{%- endif -%}"></div>
        <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="양산 실적" data-en="Mass Actual">양산 실적</span></div><input type="month" name="mass_actual" class="month-i" value="{%- if edit_data -%}{{ edit_data[11] or '' }}{%- endif -%}"></div></div>
      <div class="form-group"><div class="form-label">❓ <span class="i18n" data-ko="연기사유" data-en="Delay Reason">연기사유</span></div><input type="text" name="delay_reason" value="{%- if edit_data -%}{{ edit_data[12] or '' }}{%- endif -%}" placeholder="예 : 제품개발 지연에 따른 양산 일정 지연" id="delay_reason_input" style="color:#999" onfocus="this.style.color='#333'" onblur="if(!this.value)this.style.color='#999'"></div>
  </div></div>
  <div class="row" style="margin-top:24px">
    <div class="card"><div class="card-header blue">💰 <span class="i18n" data-ko="투자금액 (억원)" data-en="Amount (100M KRW)">투자금액 (억원)</span></div><div class="card-body">
        <div class="form-group"><div class="form-label">💵 Base</div><input type="number" name="base_amount" step="0.01" value="{%- if edit_data -%}{{ edit_data[13] or '' }}{%- endif -%}" placeholder="0.00"></div>
        <div class="form-row">
          <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="발주가 목표" data-en="Order Price Tgt">발주가 목표</span></div><input type="number" name="order_price_target" step="0.01" value="{%- if edit_data -%}{{ edit_data[14] or '' }}{%- endif -%}" placeholder="0.00"></div>
          <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="발주가 실적" data-en="Order Price Act">발주가 실적</span></div><input type="number" name="order_price_actual" step="0.01" value="{%- if edit_data -%}{{ edit_data[15] or '' }}{%- endif -%}" placeholder="0.00"></div></div>
    </div></div>
    <div class="card"><div class="card-header violet">📊 <span class="i18n" data-ko="절감 실적 (억원)" data-en="Savings (100M KRW)">절감 실적 (억원)</span></div><div class="card-body">
        <div class="form-row">
          <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="절감 목표" data-en="Savings Target">절감 목표</span></div><input type="number" name="saving_target" step="0.01" value="{%- if edit_data -%}{{ edit_data[16] or '' }}{%- endif -%}" placeholder="0.00"></div>
          <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="절감 실적(자동)" data-en="Savings(auto)">절감 실적(자동)</span></div><input id="saving_actual" name="saving_actual" readonly value="{%- if edit_data -%}{{ edit_data[17] or '' }}{%- endif -%}" placeholder="0.00"></div></div>
    </div></div>
  </div>
  <div class="card card-full"><div class="card-header emerald">📊 <span class="i18n" data-ko="절감 활동 실적 (억원)" data-en="Reduction Activities (100M KRW)">절감 활동 실적 (억원)</span></div><div class="card-body">
      <div class="table-wrapper"><table class="reduce-table"><thead><tr>
        <th style="width:110px"><span class="i18n" data-ko="항목" data-en="Item">항목</span></th><th style="width:100px"><span class="i18n" data-ko="합계" data-en="Total">합계</span></th>
        <th><span class="reduce-number">①</span><span class="i18n" data-ko="신기술/신공법" data-en="New Tech/Method">신기술/신공법</span></th>
            <th><span class="reduce-number">②</span><span class="i18n" data-ko="염가형 부품" data-en="Low-cost Parts">염가형 부품</span></th>
            <th><span class="reduce-number">③</span><span class="i18n" data-ko="중국/Local 설비" data-en="China/Local Equip">중국/Local 설비</span></th>
            <th><span class="reduce-number">④</span><span class="i18n" data-ko="중국/한국 Collabo" data-en="CN/KR Collabo">중국/한국 Collabo</span></th>
            <th><span class="reduce-number">⑤</span><span class="i18n" data-ko="컨테이너(FR) 최소화" data-en="Container(FR) Min.">컨테이너(FR) 최소화</span></th>
            <th><span class="reduce-number">⑥</span><span class="i18n" data-ko="출장인원 최소화" data-en="Travel Staff Min.">출장인원 최소화</span></th>
            <th><span class="reduce-number">⑦</span><span class="i18n" data-ko="유휴설비" data-en="Idle Equip">유휴설비</span></th>
            <th><span class="reduce-number">⑧</span><span class="i18n" data-ko="사양최적화" data-en="Spec Opt.">사양최적화</span></th>
            <th><span class="reduce-number">⑨</span><span class="i18n" data-ko="기타" data-en="Others">기타</span></th>
      </tr></thead><tbody><tr>
        <td><span class="i18n" data-ko="절감 실적" data-en="Savings">절감 실적</span></td>
        <td><input id="total_display" readonly value="{%- if edit_data -%}{{ edit_data[27] or '0.00' }}{%- else -%}0.00{%- endif -%}"></td>
        {%- for i in range(18,27) -%}<td><input class="reduce" type="number" name="reduce_{{ i-17 }}" step="0.01" value="{%- if edit_data -%}{{ edit_data[i] or '' }}{%- endif -%}" oninput="calcTotal()"></td>{%- endfor -%}
      </tr></tbody></table></div>
      <div class="activity-section"><div class="activity-label">📝 <span class="i18n" data-ko="활동내용" data-en="Activity">활동내용</span></div>
        <textarea name="activity" placeholder="예 : 1) cabinet 가공설비 신기술 적용, 3) 모터 중국설, 6) Local 인원 활용한 한국 출장자 축소(100 → 50명)" id="activity_input" style="color:#999" onfocus="this.style.color='#333'" onblur="if(!this.value)this.style.color='#999'">{%- if edit_data -%}{{ edit_data[28] or '' }}{%- endif -%}</textarea></div>
  </div></div>
  <input type="hidden" name="saving_total" id="saving_total" value="{%- if edit_data -%}{{ edit_data[27] or '' }}{%- endif -%}">
  <div class="button-group">
    <button type="submit" class="btn-primary">💾 <span class="i18n" data-ko="저장" data-en="Save">저장</span></button>
    <a href="/list" class="btn-secondary">📊 <span class="i18n" data-ko="조회" data-en="View">조회</span></a>
  </div></form>
</div>
<script>
const CORPORATIONS={{ corporations_json | safe }};
const EDIT_PRODUCT={%- if edit_data -%}"{{ edit_data[2] or '키친' }}"{%- else -%}"키친"{%- endif -%};
const EDIT_CORPORATION={%- if edit_data -%}"{{ edit_data[3] or '' }}"{%- else -%}""{%- endif -%};
function updateCorporations(){const p=document.getElementById('product').value,s=document.getElementById('corporation');s.innerHTML='';(CORPORATIONS[p]||[]).forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;s.appendChild(o)});}
function selectType(btn,type){document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');document.getElementById('invest_type').value=type;}
function calcTotal(){let s=0;document.querySelectorAll(".reduce").forEach(e=>{s+=Number(e.value)||0;});const t=s.toFixed(2);document.getElementById("saving_actual").value=t;document.getElementById("saving_total").value=t;document.getElementById("total_display").value=t;}
function setLang(l){localStorage.setItem('app_lang',l);applyLang();}
function applyLang(){const l=localStorage.getItem('app_lang')||'ko';document.querySelectorAll('.lang-btn-h').forEach(b=>b.classList.remove('active'));if(l==='ko'&&document.getElementById('langKoI'))document.getElementById('langKoI').classList.add('active');if(l==='en'&&document.getElementById('langEnI'))document.getElementById('langEnI').classList.add('active');document.querySelectorAll('.i18n').forEach(el=>{const t=el.getAttribute('data-'+l);if(t)el.innerHTML=t.replace(/\n/g,'<br>');});
const PE={'키친':'Kitchen','빌트인쿠킹':'Built-in Cooking','리빙':'Living','부품':'Parts','ES':'ES'};
const ps=document.getElementById('product');if(ps){[...ps.options].forEach(o=>{if(o.value)o.textContent=l==='en'?(PE[o.value]||o.value):o.value;});}
const ii=document.getElementById('invest_item_input');if(ii&&!ii.value)ii.placeholder=l==='en'?'e.g. Changwon advanced oven line':'예: 창원 선진화 오븐라인';
const dr=document.getElementById('delay_reason_input');if(dr&&!dr.value)dr.placeholder=l==='en'?'e.g. Mass production delayed due to product development delay':'예 : 제품개발 지연에 따른 양산 일정 지연';
const ai=document.getElementById('activity_input');if(ai&&!ai.value)ai.placeholder=l==='en'?'e.g. 1) New tech for cabinet processing, 3) China motor equip, 6) Reduce travel staff (100→50)':'예 : 1) cabinet 가공설비 신기술 적용, 3) 모터 중국설, 6) Local 인원 활용한 한국 출장자 축소(100 → 50명)';
const PU={'신규라인':'New Line','자동화':'Automation','라인 개조':'Line Remodel','Overhaul':'Overhaul','신모델 대응':'New Model','T/Time 향상':'T/Time Improve','고장 수리':'Repair','안전':'Safety','설비 이설':'Equip. Relocation','노후 교체':'Aging Replace','설비 개선':'Equip. Improve','기타':'Others'};
const pu=document.getElementById('purpose_select');if(pu){[...pu.options].forEach(o=>{if(o.value)o.textContent=l==='en'?(PU[o.value]||o.value):o.value;});}
document.documentElement.lang=l==='en'?'en':'ko';
document.querySelectorAll('.month-i').forEach(m=>{
  const wrap=m.closest('.form-group')||m.parentElement;
  if(!wrap.querySelector('.month-overlay')){
    const ov=document.createElement('span');
    ov.className='month-overlay';
    ov.style.cssText='position:absolute;left:16px;top:0;bottom:0;display:none;pointer-events:none;font-size:15px;color:#999;line-height:1;z-index:1';
    ov.style.display='flex';ov.style.alignItems='center';ov.style.display='none';
    const p=m.parentElement;p.style.position='relative';p.appendChild(ov);
    m.addEventListener('change',()=>{ov.style.display=m.value?'none':(l==='en'?'block':'none');});
  }
  const ov=m.parentElement.querySelector('.month-overlay');
  if(ov){
    ov.textContent=l==='en'?'YYYY-MM':'';
    if(l==='en'&&!m.value){
      m.style.color='transparent';ov.style.display='block';
      m.onfocus=function(){this.style.color='';ov.style.display='none';};
      m.onblur=function(){if(!this.value){this.style.color='transparent';ov.style.display='block';}};
    } else {
      m.style.color='';ov.style.display='none';
      m.onfocus=null;m.onblur=null;
    }
  }
});
}
window.onload=function(){updateCorporations();if(EDIT_CORPORATION)document.getElementById('corporation').value=EDIT_CORPORATION;calcTotal();applyLang();}
</script></body></html>"""

# ===== DASHBOARD TEMPLATE =====
DASHBOARD_TPL = r"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>대시보드</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans KR',sans-serif;background:#eef0f4;display:flex;min-height:100vh;font-size:14px}
.sidebar{width:230px;min-height:100vh;background:linear-gradient(180deg,#1e2a45 0%,#0f1724 100%);display:flex;flex-direction:column;position:fixed;top:0;left:0;z-index:100;box-shadow:3px 0 15px rgba(0,0,0,0.3)}
.logo-wrap{padding:22px 18px 18px;border-bottom:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:12px}
.logo-svg{width:46px;height:46px;flex-shrink:0}
.logo-text-group{display:flex;align-items:baseline;gap:2px}
.logo-text-lg{font-size:26px;font-weight:900;color:#d1d5db;letter-spacing:1px;font-family:'Noto Sans KR',Arial,sans-serif;line-height:1}
.logo-text-sub{font-size:24px;font-weight:700;color:#d1d5db;font-family:'Noto Sans KR',sans-serif;line-height:1}
.menu-section{padding:16px 0;flex:1}
.menu-label{font-size:11px;font-weight:700;color:#4a5568;text-transform:uppercase;letter-spacing:1px;padding:8px 20px}
.menu-item{display:flex;align-items:center;gap:12px;padding:14px 20px;color:#a0aec0;text-decoration:none;font-size:14px;font-weight:500;transition:all 0.2s;border-left:3px solid transparent}
.menu-item:hover{background:rgba(255,255,255,0.06);color:#fff}
.menu-item.active{background:rgba(102,126,234,0.2);color:#fff;border-left-color:#667eea}
.menu-icon{font-size:17px;width:22px;text-align:center}
.main{margin-left:230px;flex:1;padding:24px;min-width:0}
.topbar{background:white;border-radius:12px;padding:16px 24px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.topbar-title{font-size:21px;font-weight:700;color:#1a202c}
.topbar-sub{font-size:14px;color:#718096;font-weight:500}
.filter-bar{background:white;border-radius:12px;padding:16px 24px;margin-bottom:20px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.filter-group{display:flex;flex-direction:column;gap:5px}
.filter-label{font-size:12px;font-weight:700;color:#718096}
.filter-group select{padding:9px 16px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:14px;font-family:'Noto Sans KR',sans-serif;min-width:140px;background:#f8fafc;cursor:pointer}
.lang-toggle{margin-left:auto;display:flex;gap:8px;background:#f1f5f9;border-radius:24px;padding:4px;border:1.5px solid #e2e8f0}
.lang-btn{padding:7px 16px;border-radius:20px;font-size:13px;font-weight:700;cursor:pointer;border:none;background:transparent;color:#718096;transition:all 0.25s}
.lang-btn.active{background:#667eea;color:#fff;box-shadow:0 2px 8px rgba(102,126,234,0.3)}
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:20px}
.kpi-card{background:white;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-top:4px solid transparent}
.kpi-card.expand{border-top-color:#667eea}.kpi-card.normal{border-top-color:#10b981}
.kpi-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}
.kpi-label{font-size:12px;font-weight:600;color:#718096}
.kpi-badge{font-size:11px;padding:3px 9px;border-radius:20px;font-weight:700}
.kpi-badge.expand{background:#ede9fe;color:#6d28d9}.kpi-badge.normal{background:#d1fae5;color:#047857}
.kpi-value{font-size:25px;font-weight:700;color:#1a202c}.kpi-unit{font-size:14px;color:#718096;font-weight:500;margin-left:3px}
.chart-grid{display:grid;gap:20px}.chart-row-2{grid-template-columns:1fr 1fr}.chart-row-3{grid-template-columns:2fr 1fr}.chart-row-4{grid-template-columns:1fr}
.chart-card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.chart-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.chart-title{font-size:15px;font-weight:700;color:#2d3748;display:flex;align-items:center;gap:8px}
.chart-wrap{position:relative;height:240px}.chart-wrap.tall{height:300px}.chart-wrap.pie{height:300px}.chart-wrap.monthly{height:300px}.chart-wrap.activity{height:360px}
.invest-type-total-wrap{position:relative;border-right:2px dashed #e2e8f0;padding-right:8px;height:100%;background:linear-gradient(145deg,#f8fafc,#eef1f6);border-radius:12px;box-shadow:4px 4px 12px rgba(0,0,0,0.1),-2px -2px 8px rgba(255,255,255,0.8),inset 0 1px 0 rgba(255,255,255,0.6)}
.invest-type-total-label{font-size:14px;font-weight:800;color:#1e293b;text-align:center;margin-bottom:6px;padding-top:4px;text-shadow:1px 1px 2px rgba(0,0,0,0.08);letter-spacing:1px}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.6;transform:scale(1.3)}}
.city-popup{position:absolute;z-index:20;background:rgba(10,22,40,0.95);border:1px solid #2a5a8c;border-radius:10px;padding:14px 18px;min-width:180px;box-shadow:0 4px 20px rgba(0,100,255,0.3);pointer-events:auto;display:none}
.city-popup-title{font-size:14px;font-weight:700;color:#4af;margin-bottom:10px;border-bottom:1px solid #1a3a5c;padding-bottom:6px}
.city-popup-row{display:flex;justify-content:space-between;padding:4px 0;font-size:13px}
.city-popup-label{color:#8bc4ff}.city-popup-val{color:#fff;font-weight:600}
.city-popup-close{position:absolute;top:6px;right:10px;color:#4af;cursor:pointer;font-size:16px}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head><body>
<div class="sidebar">
  <div class="logo-wrap">
    <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCADxAPYDASIAAhEBAxEB/8QAHQABAAMAAwEBAQAAAAAAAAAAAAcICQQFBgEDAv/EAFAQAAEDAwEEBgMIDQwBBQEAAAEAAgMEBQYRBxIhMQgTQVFhcSKBkRQVMlKCkqGzFiQ2N0JWYnJ0dZWi0hgjM0NTVGOTlLHB0bIlNHOD8MP/xAAbAQEAAgMBAQAAAAAAAAAAAAAAAQIFBgcEA//EADsRAAIABAIHBgUBBwUBAAAAAAABAgMEEQUGEiExQVFxkRNhobHB0RQigeHwNBUWIzNCU5JSYnLC0vH/2gAMAwEAAhEDEQA/ALloiIAiIgCIiAIiIAiIgCIiAIhIAJJAA4kledvOdYXZ94XTK7LSubzZJWxh/wA3XU+xC8uVHMdoE2+49Eijyfbbsrh+HmNEfzI5X/7NK4zdveyVz9wZdHr40VSB7er0S561hla9kmL/ABfsSYij+n20bLpyAzM7eNeHph7P/JoXqLNlWMXnd96MitNwLuQpqyOQ+xpQ+UyjqJSvMltc00dwiIh5giIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiI4hoJJAA4knsQBfjW1VLQ0klXW1MNNTxDeklmeGMYO8k8AFC+1zpD45ipltmNCK/XdurXOa/7WhcDp6Th8M+DfaFVfPtoWXZzV9dkV4mqIgdY6ZnoQR/msHDXxOp8VDZs2GZWqqxKOZ8kPftfJe5a3NeklgNjL4LQarIKlp00pm7kOvjI7n5tDlCuV9JjaDdXPZaG0FjgI0b1MIllA8XP1Gvk0KEkUXN3o8s4fTa9DSfGLX4bPA7rI8sybI5TJfb/AHK46nXdqKhzmDybroPUF0qIoM7BLhlrRgVl3BEHE6BcllBXPbvMoqlwPaInEf7IWbS2nGREQk9RjG0LN8a3RZMoudJG3lD1xfF8x2rfoUr4h0o8uoZGx5Ja6C8QcN58Q9zzeJ1GrT5boUAIlzH1WFUdV/Nlpvjaz6rWXuwbb1s7yh8VObm6z1shDRBcG9WC49geCWH2g+ClFrmuaHNIc0jUEHUELMBSDs02wZtgj44LfcTWW1pGtBWEyRacODe1nySB4FTc1LEMmQ2cVJF9H6P36l/0UabJttGJZ+yOkim97LyR6VBUuALj/hu5P8hx8FJasaNU0s6lmOXOhcLXEIiIfAIiIAiIgCIiAIiIAiIgCIvM7Ss2smA4zNfL3KQwHcggZp1lRIRwY0d/eeQGpQ+kqVHOjUuBXb2I5+X5LZMTsU96v9fHR0cI4ucfSe7sa0c3OPcFTjbbt1vucyTWmzma0Y+fRMLXaTVI75HDs/IHDv1XjNqe0PINod/dcrxNuU7CRSUcZPVU7O4d573HifAaAeQVWzp2CZZlUaU2oWlM8F7vv6BF9AJIAGpPIKbdknR4yXKhFcskMtgtLtHNa9n2zM3TX0WH4I8XewqDYKyukUUvtJ8Vl58lvIXoqWqrquOkoqaapqJTuxxQsL3vPcAOJKmDCOjjn9+3J7rHT4/Su471W7elI8I28fU4tVsMB2e4jg1J1OO2eGnlI0kqX+nPJ+c88dPAaDwXDzratgmGOfDer9B7sZzpKf8Anpte4tb8H5RCmxpVTmypqY+yoJf1td9FqXiR9jHRfwe3lsl6uFzvMg5sLxBEfUz0v3lI1m2W7OrRumhwyyhzfgvmpmzPHyn6n6VBeWdKypdI+LFcYiYzTRs9xkLifHq2EafOKjC+bd9qV1e7eyeSjjdyjo4Y4g3ycBve0qbo+SwfHa7XPmaK74vSHUXtpaOjpWBlLSwQNA0AjjDQPYuFl33J3j9Bn+rcs8a7M8wrnufWZVfKhzuZkuErv93LgMvV5ZIZGXava883CoeD7dUufWXkqaolFFOV+X3OAiIqnQAiIgCIiA/qN745GyRvcx7SC1zToQRyIKsXsO6RVVa/c9gz2SSroR6EVz0LpoR2CQfht/K+EPFVyRDw1+HU9fL7OdDfg965GnFsrqO52+C4W+qhqqSoYJIZonhzHtPIgjmuQqJ7CNsV12c3BtDWCWvxyd+s9IDq+EnnJFrwDu9vAO8DxF3rBd7bfrNS3iz1kdZQVcYkgmj5OafA8QQdQQdCCCCAQrJnKcZwWdhky0WuB7H6PvOciIpMMEREAREQBERAERHENBJIAHEk9iA6jMcjtOJ45WX+9VAgo6Vm8483PPYxo7XE8AFQja5tAu+0TKpLvcHOipY9WUNIHasp49eQ73HgXO7T4AAew6Tm1F+c5MbPaajXH7ZIWwlvAVMo4OlPeOxvhqe1Q6qtnUss4GqOUqicv4kXgvd7+gXMstruF6utNarVRy1lbUvEcMMTdXPP/wC4k8gASV8s9tr7vdKa2Wyllq62pkEcMMY1c9x7ArzbBNkts2c2NtTUsiq8jqo/tyr01EYPHqYu5g7TzceJ4BobCVzI41jMrDJV3rjexer7jothuwW0Ya2nvmRiK6X/AHQ5rSN6Ckd+QD8Jw+MfUBzPvtpe0XF9n1sFXf63SeRpNPRxelPOR8VvYPE6DxXkdv22a3bPqJ9qtboa3JZmehATqylBHB8unbpxDeZ4HlzpZkl8u+R3ie73uvmrq2c6vlldqfADsAHYBwCtexqWH4PVY3M+LrYmoHs4vlwX53kl7UtveZZhPLS22pksNoOrRT0shEkjf8SQaE+Q0HgVEjiXOLnEkk6knmV8RVN+paORSQdnJhUK/NvEIiIekIiIAiIgCIiAIiIAiIgClvo77XqrZ7dxbLm6SoxuskBnjHF1M88OtYPZvDtA7xxiREPNV0kqrkuTNV0zTylnhqqWKqppWSwTMEkcjDq17SNQQe4hfoqudEDakWyR7PL5OS12rrTM93I8zAdfWW+sdytGrnG8Uw6Zh9Q5Mf0fFcQiIhjwiIgCIiAKEelptFOK4gMatk27d7zG5rnNJDoafk53DkXcWj5XcporqqnoaKetq5Ww09PG6WWR3JjGjUk+AAKzv2sZfUZzntzyKbebFNJuU0Z/q4W8GN89OJ8SVDZs2VsMVZVdpGvlg183uXqeVX0AkgAak8gvim7ol7OxlWYnJLlDv2myyNe1rgC2ao5sbx5hvwj8nvVTpldWS6KRFPmbF48F9SZui7spbhthGR3ylZ7/ANwjBa1w1dSQniGeDnc3eodh153SL2vwbPrSbVaHxzZLWR6wtIDm0jDw6145E/FaeZ4ngND7TarmtvwHDKvIK7R72Dq6WDXQzzH4LB/uT2AFZ+ZRfbnkuQVl9vFQZ62skMkr+Q8AB2ADQAdgCs9RoWD0EzG6qKtq9cCezi+HJfm84VbVVNbWTVlZUS1NTO90k00ry58jydS5xPEknjqV+KL9aOmqKyrhpKSCWoqZ5GxxRRMLnyPcdGta0cSSSAAOaqdH1QruPyRWLwjotXm4UEVZlN9jtD5G73uSCETSM8HO3g0HwG95rl5b0VK6no3z4xkzK2Zo1FNWQdVv+AeCRr5geaWMI8yYYpnZ9rr5O3W1vQrSi51+tFzsN3qbReKKahr6Z+5NBM3RzTpqPMEEEEcCCCNQVwUM1DEokooXdMIu3wu0x37MbLY5pnwx3G4QUj5GjUsEkjWEgd41Vk7v0XMet9prK/7KLpJ7mgfNudTGN7daTpr2cksY6uxeloY4YJ0VnFs1NlVUREMmEREAREQBERAEREB+1FU1FFWQ1lJK6GogkbLFI06FjmnUEeIIWgWxHPKfaDgdJeAWNr4v5iviBHoTNHE6djXcHDz07Fnupg6KWc/YltGjtlZPuWu97tNNvHRrJdf5p/dzJbr3OPcpTNbzNhiraRxwr54Na5b1+by8CIiscmCIiAIiICF+mFk5seyt1qgkLam9Ttphpz6pvpyHy4Nb8pUnU39MzIHXTapHZmSB0FnpGR7oPKSQb7j7CwepQgqs67lmj+Gw+C+2L5n9dnhY/ahpaiurYKKkidNUVEjYoo283vcdAB4kkLRDZPiFPg2BWzHYd10sMe/UyD+smdxe7y14DwAVTeiHi/v9tXiuc0e9S2WE1TteRkPoxjz1Jd8hWo23ZWcM2ZXi9xSBlWIuppNf7Z/otI8tS75KI1/NlTHU1Mugld1+b1LovMqh0ps+my/aFPa6abW0WV7qana12rZJBwkkPZzG6PBo7yoiX17nPcXvcXOcdSSdSSvig3ejpYKSRDJl7IV+P6hWS6EmI0Ndc7tl9bCyaWgLaaiDm69W9wJe8eO7ugH8pyrarQ9BrIqRjL9i00jWVMj2VtO0n+kGm4/TxGjPae5SjFZlimQ4bMcvuvyvr/OBZ9ERWOQFb+m3iVHJYLbmdPExlbBUNo6lwGhljcHFpPeWlug8HKp6t9028ipaTB7djTZAayvrG1BZrxbFGDxPm4tA8j3KoKq9p1nKkUx4bDp8Xbl/9ueo2RffXxD9e0X17FoJl33J3j9Bn+rcs+9kX318Q/XtF9exaCZd9yd4/QZ/q3KUYHOP6uRy9TNNERVOhBERAEREAREQBERAF9a5zXBzSWuB1BB0IK+IgNE9j2TDL9mtkvrnh881MGVPHU9cz0H6+bmk+sL1qrV0G8hdNar9i80hPueVlbTtPxXjdfp5FrPnKyqujiuM0nwdbMlLYnq5PWgiIhjAhIA1J0ARef2lXP3m2e5DdA7ddS2yokYfyhG7dHt0QvLgcyNQLa3Yz7z69OyPNr1fXEkV1bLMwdzC47o9TdB6l0aIqHd5cClwqCHYtRcjoUWL3Bs2rr3I3SS61x3DpzjiG6P3jIvJ9ObIXmqx/FYpQGNY+vnYDzJJZGfVpJ7VOWw+2e8+yLFqHd3He9sUz29zpB1jh7XlU/6UV2fdttt9O/vRUZjpIh8UMY3eHzy8+tWew57g6+Ox2ZPeyHSf/VeBGKIiqdFC5+P3e5WC9Ul5s9XJSV9JIJYJmc2uHgeBB4gg6ggkHUFcBEKxQqJOGJXTLb4T0pcfqaSKHLbPW0FWGgPnpGiWFx79CQ5vl6XmuXl3SixChgkZjlsuF3qdDuPlaIIdewknVx8t0eap6im5rjynhrmaei7cL6vfxO7zjKr3meR1F/v9V7orJ9B6Ld1kbBwaxjexo+niTqSSekRFBsUuXDLhUECslsR6jZF99fEP17RfXsWgmXfcneP0Gf6tyz72RffXxD9e0X17FoJl33J3j9Bn+rcrI0DOP6uRy9TNNERVOhBERAEREAREQBERAEREBK/RPvbrNtptcRcWw3KOWil4895u8399jFelZt4Bc/ebOrDdt7dFHcYJnH8lsjSfo1WkisjmudZGjVS5q/qVuj+4REUmmBR70kZep2IZQ/XTWlaz50jB/wAqQlGfSkDzsHyUM57lOfV7pi1+hD3YYr1slf7ofNFC0RftRFjayB0nFgkaXeWvFUO3M0zt1O2kt9PSsAa2GJsYA7AAAs59pdS+s2i5LVSO3nS3aqeT5yuWj6zWzQOGY3oO+ELhPr59Y5SznuSdc6dE+C82dQiIoOhhERAEREAREQHqNkX318Q/XtF9exaCZd9yd4/QZ/q3LPvZF99fEP17RfXsWgmXfcneP0Gf6tysjnucf1cjl6maaIiqdCOVbLdcLpU+5bZQVVdPul3VU8LpH6DmdGgnRdp9heY/infv2dL/AAqROh/JHDtlgklkZGwUM+rnHQDgO1XU98bf/f6X/Ob/ANqUrmp41mKbh1T2MEvSVk73M5/sLzH8U79+zpf4U+wvMfxTv37Ol/hWjHvjb/7/AEv+c3/tPfG3/wB/pf8AOb/2psYj99J/9ldX7Gc/2F5j+Kd+/Z0v8KfYXmP4p379nS/wrRj3xt/9/pf85v8A2nvjb/7/AEv+c3/tLD99J/8AZXV+xnP9heY/infv2dL/AAp9heY/infv2dL/AArRj3xt/wDf6X/Ob/2v7iraOaQRxVdPI88mtkBJ9SWH76z/AOyur9jOCpxHK6ankqanGL1DDEwvkkkoJWtY0DUkkt0AA46rpVoXt1kbHscyxzuRtkzfWW6D/dZ6KGrGzYFi8eKSopkUOjZ28AtOqCXr6Gnn116yJr/aAVmKtMMZDxjdsEnwxRxB3nuBEYDPC+WS/wDl6HYIiKxz4KP+kZCZ9iWUMA10pA/5r2u/4UgLpc7tnvzhF8tG7vGst08DR4ujcB9JQ9NHMUqolxvc0+jM2URFQ7oaa2WqbXWairWHebUU8crT3hzQf+VndtSpJKDaXk1HINHRXapHmOtdofWNCrz7Cbm277HsWrGvD923RwOd+VEOrd69WFVK6V1odattl2k3d2K4Rw1kXiHMDXH57HqzOd5TfYYhOp3wfgyKURFU6IEREAREQBERAeo2RffXxD9e0X17FoJl33J3j9Bn+rcs+9kX318Q/XtF9exaCZd9yd4/QZ/q3KyOe5x/VyOXqZpoiKp0IIiIAiIgCIiAKYOiBQ+69ttBPpr7ipKify1jMf8A/RQ+rH9Be0mXJMjvhbwpqOOla7xkfvH6oe1EYjH5vZYdOi7rddXqTV0maptJsNyWRztN+GOIeJfMxv8AyqDK5/TTubKPZPT0AeBJX3KJm52ljGueT5AhvtCpgpZicmytCgcT3xPySPoBcQACSeAAWnVHF1FJDD/Zxtb7Bos5tmNs9+No2OWst3m1Nzp2PH5HWDe+jVaPIjF54mJxyYOF31t7BERWNDCIiAzk2p2L7Gdo1/sYbux0tdI2Ef4RO9H+6WrzSnzpr46+37QqHIo2HqLrSBj3af1sXonj+YWewqA1RnbcKqviqOXN3tK/PY/EuB0I78K3A7pYJJGmW21vWxt14iKVuo4fnNf7V0/TkxuSWisWWQs1bA51DUkDkHenGfLUPHrCi3or5WMY2tUMU8ojors00M+8dAHOIMZ+eGjycVcPapi8eZ7P7xjrtwSVUB6hzhwZK30mH5wHq1VtqNIxF/srHYaj+mLX9Hqi9zOZF+tVBNS1UtLURuimheY5GO5tcDoQfIr8lU6MncIiISEREAREQHqNkX318Q/XtF9exaCZd9yd4/QZ/q3LPvZF99fEP17RfXsWgmXfcneP0Gf6tysjnucf1cjl6maaIiqdCCIiAIiIAiIgCvB0R8Z94dkdNXyxhtTeZnVjz29X8GMeW63e+Uqe7PsbqcuzS1Y5S6h1bUNje4D4DOb3epoJ9S0WiZQ2SysjbuU1BQUwaNfgxxRt/wBgApRpGc63RlQUsO2J3fJbOr8ip/TfvwrM2s+PRSbzLdRmaQA8BJK7kfHdY0/KVe13+0TIpcszi8ZFNrrXVTpGA/gx8mN9TQ0epdAoZs+FUnwdHLkvalr5vW/EmHohWI3fbHS1r2Ew2mmlq3d28R1bR56v1+Srvqu/Qgxx1Hid4yaaMB1xqG08BPPq4gdSPAucR8lWIVkc1zVVdviMSWyFJer8WERFJrgREQEUdKnFHZPslrZaeEyVtpeK6ENGpLW6iQfMLj8kKiy0/kYySN0cjWvY4EOa4agg9hWfe3fCn4JtIuFpjjc2gmPumgcRwMLydB8k6t+Sqs6DkzEE4YqSLata9V69Tw0b3xyNkje5j2kOa5p0II5EFaDbDc0jzrZzbrw6Vjq6NnuevaDxbMwaEkdm8NHDwcs91K3Ro2jHA84ZBcJ9yx3QthrN5x3YXfgS+onQ+BPcETM1mXC3XUl4F88Gtd/Ffm9Hoel/s+ksGX/ZfQRONtvLyZ9BwiqdPSB/PA3vPeUELSTNsbtOZ4pWWG6MEtHWR8Ht0JY7m17T3g6ELP7aNh91wbLKvHru0GWE70UrR6E8Z+DI3wP0HUdiNHlyti6qpHw8x/PB4r7bGecREUG2BERAEREB6jZF99fEP17RfXsWiNxpY6+31NDM57Y6iJ0Ty06EBwIOnjxWbGL3aSw5Nar5DCyaS3VsNWyNx0DzG8PAJ7jop6/lXZD+Kdr/ANRIpTNNzNhFXXzpcdPDey4pb+8kb+TFs3/t79/q2fwJ/Ji2b/29+/1bP4FHP8q7IfxTtf8AqJE/lXZD+Kdr/wBRIp1GN+BzJ/rf+S9z50idjOH4Bs/bfLG+5vq31sdP9s1Ae0NcHEkANHH0R9Kropd2t7c7ptExQY/XWGioo21LKgSwyucdWhw00PZ6RURKrNtwWVWSqbRrHeO7331BERDLhEUldH7ZpVbRMvY2oikZYqFzZLhOOAcOyJp+M76Bqe5D4VNTLpZUU6a7QomvoZ7PzbbNPnVzp92qr2mG3h44sg19J41+MRoPBviu56YebCwYEzGqOYNr72SyQA8WUzfhn5R0b5F3cpjuFXa8dsEtZVSQ0Ntt9PvOPBrIo2DgB6hoAs+Nq+ZVeeZzX5FU7zI5XdXSxE/0ULeDG+enE+JKs9Rz7CJUzGsTirJq+WF3/wDK+m1/c8qv1pKeerq4aSmidLPNI2ONjebnOOgA8yV+SnbodYR7/ZxLlNbFvUNkAMWo4PqXD0fmjV3nuqpvmIVkFFTRz49y6vcupavZ1j0WKYNZ8diA+0aVkchH4UnN7vW4uPrXfoiucRmTIpkbji2t36hERCgREQBRT0mdnQzrBn1VBBvXu1B09Jugb0rdPTi9YGo8QO8qVkQ9FJVTKSdDOlvXC/zqZgEEEgggjmCvin7pZ7LPsdu7s0sdOG2mvl+24o26CmnP4Xg159h1HaFAKodpoK6XXSIZ8vY/B70W16JW1dl0t8WCZDWf+o0zdLZLIf6eID+i17XNHLvb5KTdtmzO17SMadSTCOnu1M0uoKwjjG74rtOJY7tHZzHEKgNLPPS1MVTTTSQTwvEkUkbi1zHA6hwI4gg8dVdbo8baaLOqCGw36aOlyaCPTjo1lc0D4bOwP04uZ628NQ2UzSsfwidQz/2hR6td3bc+PJ7/AG2U2yOyXXHb3VWW9UUtFX0r9yWGQcQewg8iCNCCNQQQQSCuuV/9tGyyybSbMGVIbR3enYRR17WauZ27jx+Ewns7NdRpx1pHtBwnIcFvjrTkNEYJCC6GVvpRTt+Mx3aPpHaAjRseC47JxKDReqYtq9V3eR5xERQZ4IiIAiIgCIiAIiIAiKQdkGyjJNotxb7jidR2hjtKi4ysPVt05tYPw3eA9ZCHxqKiVTS3MmxWhR1Oy7A73tByeOy2ePdaNH1VU8fzdNHrxc7vPcOZPrIvrs9xG04PitLj1mjIggGr5H6b80h+E92nafoGg7F+ezvCbBgePR2Ww0vVxj0ppn8Zah/a97u0/QOQAUDdJbbnF1FVhmFVm+92sVxuMTuAHIxREcyeRcPIc9RbYc5raypzFVKnp1aWvy79EeY6Vu1gZNc3YbYKhr7NRSa1c0btRVTNPIHtY0+08ewKA0RVOgUFDKoZEMmVsXi+JzbFa6693mjtFtgdPWVkzYYYx2ucdPZ3nsC0M2XYdQ4JhNBjtFo4wt36iUf10zuL3+s8u4ADsUQdEnZWbJbmZ1fqZzLlWRkW+KQaGCFw/pCPjPHLub5qwyskc9zXjCqpvw0p/LDt739vcIiKTUAiIgCIiAIiIDiXq2UF5tNVarnSx1VFVRmKaJ41Dmn/APc+xUQ27bLrjs3yQsa2SosdW4mgqyNeHPq39zx9I4jtAv0uqyzHrPlNiqLJfaKOsoagaPY7mD2OaebXDsIUNGcwPGpmGTr7YHtXqu/zM1F+lNPPS1MdTTTSQzROD45I3FrmOB1BBHIhSRtw2RXnZxcjO3fr7BPJpS1obxbryjlA5P8AHk7TUacQIzVTrNNUyquUpsp3hZbPYd0iqS4spsfz2RlJW6COK6HhFMezrfiOPxvgnwU65RjmP5fZTbr7bqa5UUo3m741015OY4cWnxBWa6knZVtmzDAHMpaeo98rQD6VBVOJY0f4bubPVw8CpTNSxXKulH29C9GLbbZ0e7y5EhbUOjJdqB8twwWq98qXi73DUPDZ2czo13Brx56HzVf7vbLjZ7hLb7rQ1NDVxHR8M8ZY9vqKvTs0224Pm/V0sVd71XR/D3FWkMc49zHfBf5A6+C9pk+L47k9L7myCy0Nyj00HXxBzm/mu5t9RCmx4afM1bh8XY18tu2/Y/Z/mszXRXDyzouYfcJHzY/drhZXuHCJ4FRC0+AcQ794qML70X8+o5HG2VtnukQ+DuzOikPm1zdB84qLGy02ZsNnr+Zovv1fbxILRSRV7C9q1NI5j8QqH6dsVRC8H1h5XGGxnaiXbowy5a+O5p7d5QZFYlRtXU2H/Je54BFJtu2C7VqyXcGLPp29r56qFgH7+vsC9tjvRXyyqe119v1qtsR5iAPqJB6tGt/eKWPhOxvD5KvFOh+jv5XK+LusTxXIsrrxQ47Z6u4zfhdUz0WeLnH0WjxJCt9h/Rt2fWV7Z7m2sv07Tr9tSbkQP5jNNfIkqW7Zb7VYraKW3UVHbaKFpd1cMbYo2ADidBoBwHNTY12tznIgWjTQOJ8XqXu/Arxsq6MdJSmK5Z/VNq5QQ4W6leRGOP8AWP5u8m6DxKsFI+yYtj+891HabTQReEcULB9AUU7TukTh+MCaisThkNzbq3SB2lPG7j8KT8Lybr5hVU2i7Rcsz2u6/ILm+SBrtYaSL0IIvzWd/idT4qbpGNlYVimNxqbVxOGDv9IfV+JLG3bpC1N/hqscwky0lqkHVz17gWzVA7WsHNjD38yO7ka9Iiqb3QYfIoJXZSVZeL5hTv0ZNjT8trIssySnc2wU8mtNC8ae7pGn6sEcT2kadh0+9HfYXNl3U5NlkUtPYAQ6nptSySu8debY/EcT2ac1cOkp6ejpIaSkgip6eBjY4oomBrI2NGga0DgAAAAApSNWzHmNSU6WlfzbG+Hcu/y57P0a0NaGtADQNAAOAX1EVjnAREQBERAEREAREQBERAca62+hutunt1ypIaujqGFk0MzA5j2nsIKqjtu6OldaXT3zAo5a63/CltupdPD39Web2+Hwh4q26JYyeGYtUYdM0pT1b1uf5xMwZY3xSOilY5j2Etc1w0LSOYI71/KvxtX2NYjtAjfU1EHvbd9PRuFKwBx/+RvKQefHuIVU9pexLOMI6yqloffW1s4+7aIF7Wjve34TPMjTxVWjpWGZjpK5KFvRj4P0e/z7iM17/Ctse0PEwyK35BPU0rOApa3+fj07hvcWj80heARQZqfTyqiHQmwqJd6uWhxvpXt9FmR4kR8aagqNf3H/AMSkOy9IvZbcQ0T3Wstr3fg1dG/h5lgcB7VRtFNzX5+UsOm64U4eT97mh1PtU2bzsa9mb2EB3Eb9axh9jiCFyDtJ2eBu8c6xnTwukJP/AJLOlEuY95Jp901+BoVXbW9mlHEZZs2szmjshqBKfYzUrx186SuzSga73FNdLq4cvc1GWA+uUtVJkS595WTKKF3jiifRehZTJulbc5WyRY5i1NS6ghs1bOZT57jQ0D2lQvmu0fNcxe73/wAgrKiBxP2sx3Vwj5DdGn1gleTRRczlJg9FRu8mWk+O19WEX9RMfLI2KJjnveQ1rWjUuJ5ADvUzbMujtmOT9VW3xv2O2x2jtahmtRI3h8GP8Hh2u08ih6Kuup6ODTnxqFfmxbyIrRbbhd7jDbrXRT1tXM7djhhYXvcfABWq2HdHWktXue/55HHWVw9OK2cHQwnsMh5Pd+T8EeKl/Zzs7xXAbf7mx+3Njme0Nmq5fSnm/Od3eA0HgvWKyRz3GM1zalOVS/LDx3v28z4xrWMaxjQ1rRoABoAO5fURSaeEREAREQBERAEREAREQBERAEREAREQEfZrsZ2d5YXy12Pw0lU86mqof5iTXvO76Lj+cCoVyzop3KJz5cWyamqWaathuEZjcPDfZqD80K1aKLGXo8dr6TVLmO3B6147PoUAyPYvtNsT3e6cTrqqMcpKECpBHfpHqR6wF4i4264W6XqrhQVVHJ8SeF0Z9hC02X51EENREYaiGOaN3Nj2hwPqKWNhkZ2nL+bKT5Nr3Mw0Wks+IYnP/T4vZJfz6CI/7tXGbgGCNfvtwrGw74wtcGv/AIqLHtWd5O+U+qM412NosV7vDg202a43Ak6AUtM+U/ugrRenxbGKcg0+OWeEjiCyijbp7Au3a0NaGtAAA0AA4BLHxmZ3Vv4cnq/sUPxnYLtPvm64Y+bbCf6y4SiHTzZxf+6pYxDoqU0cjZssyV84GhNPb49wH/7H8dPkhWZRTYw9Vm3EJ2qBqBdy9Xc8nhezfCcPax1hx6jp52j/ANy9vWTn5btXD1EBesRFJrk2dMnRacyJt8XrCIiHzCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiID/2Q==" style="width:46px;height:46px;border-radius:8px;object-fit:contain;background:transparent" alt="LG">
    <div class="logo-text-group"><span class="logo-text-lg">LG</span><span class="logo-text-sub">전자</span></div>
  </div>
  <div class="menu-section">
    <div class="menu-label"><span class="i18n" data-ko="설비투자비 한계돌파" data-en="Investment Breakthrough">설비투자비 한계돌파</span></div>
    <a href="/dashboard" class="menu-item active"><span class="menu-icon">🏠</span><span class="i18n" data-ko="대시보드" data-en="Dashboard">대시보드</span></a>
    <a href="/list" class="menu-item"><span class="menu-icon">📋</span><span class="i18n" data-ko="투자실적 조회" data-en="Records">투자실적 조회</span></a>
    <a href="/" class="menu-item"><span class="menu-icon">✏️</span><span class="i18n" data-ko="Data 입력" data-en="Data Entry">Data 입력</span></a>
  </div>
</div>
<div class="main">
  <div class="topbar"><div class="topbar-title">📊 <span class="i18n" data-ko="'26년 설비 투자비 한계돌파 현황" data-en="'26 Facility Investment Breakthrough">'26년 설비 투자비 한계돌파 현황</span></div><div class="topbar-sub" style="font-size:17px;font-weight:600"><span class="i18n" data-ko="창원생산기술실" data-en="Changwon Prod. Tech.">창원생산기술실</span></div></div>
  <div class="filter-bar">
    <div class="filter-group"><div class="filter-label"><span class="i18n" data-ko="제품" data-en="Product">제품</span></div><select id="fProduct" onchange="onProductChange()"></select></div>
    <div class="filter-group"><div class="filter-label"><span class="i18n" data-ko="법인" data-en="Corp.">법인</span></div><select id="fCorp" onchange="applyFilter()"><option value="">전체</option></select></div>
    <div class="filter-group"><div class="filter-label"><span class="i18n" data-ko="투자유형" data-en="Type">투자유형</span></div><select id="fType" onchange="applyFilter()"></select></div>
    <div class="filter-group"><div class="filter-label"><span class="i18n" data-ko="투자목적" data-en="Purpose">투자목적</span></div><select id="fPurpose" onchange="applyFilter()"><option value="">전체</option></select></div>
    <div class="lang-toggle"><button class="lang-btn active" id="langKo" onclick="setLang('ko')">🇰🇷 한글</button><button class="lang-btn" id="langEn" onclick="setLang('en')">🇺🇸 ENG</button></div>
  </div>
  <div class="kpi-grid">
    <div class="kpi-card expand"><div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="건수" data-en="Count">건수</span></div><div class="kpi-badge expand"><span class="i18n" data-ko="확장 투자" data-en="Expansion">확장 투자</span></div></div><div><span class="kpi-value" id="kExpCnt">0</span><span class="kpi-unit"><span class="i18n" data-ko="건" data-en="cases">건</span></span></div></div>
    <div class="kpi-card expand"><div class="kpi-top"><div class="kpi-label">Base</div><div class="kpi-badge expand"><span class="i18n" data-ko="확장 투자" data-en="Expansion">확장 투자</span></div></div><div><span class="kpi-value" id="kExpBase">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div></div>
    <div class="kpi-card expand"><div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="절감실적" data-en="Savings">절감실적</span></div><div class="kpi-badge expand"><span class="i18n" data-ko="확장 투자" data-en="Expansion">확장 투자</span></div></div><div><span class="kpi-value" id="kExpSave">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div></div>
    <div class="kpi-card normal"><div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="건수" data-en="Count">건수</span></div><div class="kpi-badge normal"><span class="i18n" data-ko="경상 투자" data-en="Recurring">경상 투자</span></div></div><div><span class="kpi-value" id="kNorCnt">0</span><span class="kpi-unit"><span class="i18n" data-ko="건" data-en="cases">건</span></span></div></div>
    <div class="kpi-card normal"><div class="kpi-top"><div class="kpi-label">Base</div><div class="kpi-badge normal"><span class="i18n" data-ko="경상 투자" data-en="Recurring">경상 투자</span></div></div><div><span class="kpi-value" id="kNorBase">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div></div>
    <div class="kpi-card normal"><div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="절감실적" data-en="Savings">절감실적</span></div><div class="kpi-badge normal"><span class="i18n" data-ko="경상 투자" data-en="Recurring">경상 투자</span></div></div><div><span class="kpi-value" id="kNorSave">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div></div>
  </div>
  <div class="chart-grid chart-row-2" style="margin-bottom:20px">
    <div class="chart-card"><div class="chart-header"><div class="chart-title">💰 <span class="i18n" data-ko="전체 Base 대비 절감 실적" data-en="Total Base vs Savings">전체 Base 대비 절감 실적</span></div></div><div class="chart-wrap"><canvas id="cBaseTotal"></canvas></div></div>
    <div class="chart-card"><div class="chart-header"><div class="chart-title">📦 <span class="i18n" data-ko="제품별 Base 대비 절감 실적" data-en="Product Base vs Savings">제품별 Base 대비 절감 실적</span></div></div><div class="chart-wrap"><canvas id="cBaseProduct"></canvas></div></div>
  </div>
  <div class="chart-grid chart-row-4" style="margin-bottom:20px">
    <div class="chart-card"><div class="chart-header"><div class="chart-title">📊 <span class="i18n" data-ko="투자유형별 절감 실적" data-en="Savings by Type">투자유형별 절감 실적</span></div></div>
      <div style="display:grid;grid-template-columns:240px 1fr;gap:0;height:320px">
        <div class="invest-type-total-wrap"><div class="invest-type-total-label">Total</div><div style="position:relative;height:calc(100% - 30px)"><canvas id="cInvestTypeTotal"></canvas></div></div>
        <div style="position:relative;padding-left:8px;height:100%"><div style="position:relative;height:100%"><canvas id="cInvestTypeProduct"></canvas></div></div>
      </div></div>
  </div>
  <div class="chart-grid chart-row-3" style="margin-bottom:20px">
    <div class="chart-card"><div class="chart-header"><div class="chart-title">🔧 <span class="i18n" data-ko="절감 활동별 실적" data-en="By Activity">절감 활동별 실적</span></div></div><div class="chart-wrap activity"><canvas id="cActivity"></canvas></div></div>
    <div class="chart-card"><div class="chart-header"><div class="chart-title">🥧 <span class="i18n" data-ko="제품별 절감 실적" data-en="By Product">제품별 절감 실적</span></div></div><div class="chart-wrap pie"><canvas id="cPie"></canvas></div></div>
  </div>
  <div class="chart-grid chart-row-4" style="margin-bottom:20px">
    <div class="chart-card"><div class="chart-header"><div class="chart-title">🌍 <span class="i18n" data-ko="법인별 절감 목표 및 실적" data-en="Corp. Target vs Actual">법인별 절감 목표 및 실적</span></div></div><div class="chart-wrap tall"><canvas id="cCorp"></canvas></div></div>
  </div>
  <div class="chart-grid chart-row-4" style="margin-bottom:20px">
    <div class="chart-card"><div class="chart-header"><div class="chart-title">📅 <span class="i18n" data-ko="월별 절감 실적 (2026년)" data-en="Monthly Savings (2026)">월별 절감 실적 (2026년)</span></div></div><div class="chart-wrap monthly"><canvas id="cMonthly"></canvas></div></div>
  </div>
</div>
<!-- World Map Modal -->
<script>
const ALL_DATA={{ processed_json | safe }};const CORPS_MAP={{ corporations_json | safe }};const MONTHLY_DATA={{ monthly_json | safe }};const ALL_PURPOSES={{ all_purposes_json | safe }};
const PRODUCTS=['키친','빌트인쿠킹','리빙','부품','ES'];
const PRODUCTS_EN={'키친':'Kitchen','빌트인쿠킹':'Built-in Cooking','리빙':'Living','부품':'Parts','ES':'ES'};
function pn(k){return getLang()==='en'?(PRODUCTS_EN[k]||k):k;}function getLang(){return localStorage.getItem('app_lang')||'ko';}
const _allCorps=[...new Set(Object.values(CORPS_MAP).flat())].sort();const ALL_CORPS_ORDERED=['KR',..._allCorps.filter(c=>c!=='KR')];
let filtered=[...ALL_DATA];
const charts={};
function t(ko,en){return getLang()==='en'?en:ko;}
function sum(a,i){return a.reduce((s,r)=>s+(parseFloat(r[i])||0),0);}
function setLang(l){localStorage.setItem('app_lang',l);document.getElementById('langKo').classList.toggle('active',l==='ko');document.getElementById('langEn').classList.toggle('active',l==='en');applyLang();initProductFilter();initTypeFilter();initCorpFilter(document.getElementById('fProduct').value);initPurposeFilter();renderAll();}
function applyLang(){const l=getLang();document.getElementById('langKo').classList.toggle('active',l==='ko');document.getElementById('langEn').classList.toggle('active',l==='en');document.querySelectorAll('.i18n').forEach(el=>{const t=el.getAttribute('data-'+l);if(t)el.innerHTML=t.replace(/\n/g,'<br>');});}
const _PU={'신규라인':'New Line','자동화':'Automation','라인 개조':'Line Remodel','Overhaul':'Overhaul','신모델 대응':'New Model','T/Time 향상':'T/Time Improve','고장 수리':'Repair','안전':'Safety','설비 이설':'Equip. Relocation','노후 교체':'Aging Replace','설비 개선':'Equip. Improve','기타':'Others'};
function initPurposeFilter(){const l=getLang(),s=document.getElementById('fPurpose');s.innerHTML='<option value="">'+t('전체','All')+'</option>';ALL_PURPOSES.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=l==='en'?(_PU[p]||p):p;s.appendChild(o);});}
function initProductFilter(){const s=document.getElementById('fProduct'),cur=s.value;s.innerHTML='<option value="">'+t('전체','All')+'</option>';PRODUCTS.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=pn(p);s.appendChild(o);});if(cur)s.value=cur;}
function initTypeFilter(){const s=document.getElementById('fType'),cur=s.value;s.innerHTML='<option value="">'+t('전체','All')+'</option>';const o1=document.createElement('option');o1.value='확장';o1.textContent=t('확장','Expansion');s.appendChild(o1);const o2=document.createElement('option');o2.value='경상';o2.textContent=t('경상','Recurring');s.appendChild(o2);if(cur)s.value=cur;}
function initCorpFilter(product){const s=document.getElementById('fCorp'),cur=s.value;s.innerHTML='<option value="">'+t('전체','All')+'</option>';const corps=product&&CORPS_MAP[product]?CORPS_MAP[product]:ALL_CORPS_ORDERED;corps.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;s.appendChild(o);});if([...s.options].some(o=>o.value===cur))s.value=cur;}
function onProductChange(){initCorpFilter(document.getElementById('fProduct').value);applyFilter();}
function applyFilter(){const p=document.getElementById('fProduct').value,c=document.getElementById('fCorp').value,tp=document.getElementById('fType').value,pu=document.getElementById('fPurpose').value;filtered=ALL_DATA.filter(r=>(!p||r[2]===p)&&(!c||r[3]===c)&&(!tp||r[1]===tp)&&(!pu||r[4]===pu));renderAll();}
function updateKPI(){const e=filtered.filter(r=>r[1]==='확장'),n=filtered.filter(r=>r[1]==='경상');document.getElementById('kExpCnt').textContent=e.length;document.getElementById('kExpBase').textContent=sum(e,13).toFixed(1);document.getElementById('kExpSave').textContent=sum(e,17).toFixed(1);document.getElementById('kNorCnt').textContent=n.length;document.getElementById('kNorBase').textContent=sum(n,13).toFixed(1);document.getElementById('kNorSave').textContent=sum(n,17).toFixed(1);}
const P={gray:'rgba(180,180,180,0.85)',grayL:'rgba(180,180,180,0.4)',red:'rgba(180,30,30,0.85)',purple:'rgba(102,126,234,0.85)',green:'rgba(16,185,129,0.85)',amber:'rgba(245,158,11,0.85)',blue:'rgba(59,130,246,0.85)',blueL:'rgba(59,130,246,0.3)',teal:'rgba(20,184,166,0.85)',violet:'rgba(139,92,246,0.85)',pink:'rgba(236,72,153,0.85)',orange:'rgba(249,115,22,0.85)'};
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}
const barLP={id:'barLabel',afterDatasetsDraw(ch){if(ch.config.type==='doughnut'||ch.config.type==='pie')return;const{ctx}=ch;ch.data.datasets.forEach((ds,di)=>{const m=ch.getDatasetMeta(di);if(m.hidden)return;m.data.forEach((bar,idx)=>{const v=ds.data[idx];if(!v||v<=0)return;ctx.save();ctx.font='600 11px "Noto Sans KR",sans-serif';ctx.fillStyle='#374151';ctx.textAlign='center';ctx.textBaseline='bottom';if(ch.config.options?.indexAxis==='y'){ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(v.toFixed(1),bar.x+4,bar.y);}else{ctx.fillText(v.toFixed(1),bar.x,bar.y-4);}ctx.restore();});});}};
Chart.register(barLP);
function chart_BaseTotal(){mk('cBaseTotal',{type:'bar',data:{labels:[t('전체','Total')],datasets:[{label:t('Base 금액','Base'),data:[sum(filtered,13)],backgroundColor:P.purple,borderRadius:6,maxBarThickness:60},{label:t('절감 실적','Savings'),data:[sum(filtered,17)],backgroundColor:P.green,borderRadius:6,maxBarThickness:60}]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:{top:20}},plugins:{legend:{position:'top',labels:{font:{size:12},padding:12}}},scales:{y:{beginAtZero:true,suggestedMax:Math.ceil(Math.max(sum(filtered,13),sum(filtered,17))*1.2)||10,title:{display:true,text:t('억원','100M'),font:{size:12}}}}}});}
function chart_BaseProduct(){const b=PRODUCTS.map(p=>sum(filtered.filter(r=>r[2]===p),13)),s=PRODUCTS.map(p=>sum(filtered.filter(r=>r[2]===p),17));mk('cBaseProduct',{type:'bar',data:{labels:PRODUCTS.map(p=>pn(p)),datasets:[{label:t('Base 금액','Base'),data:b,backgroundColor:P.purple,borderRadius:5,maxBarThickness:40},{label:t('절감 실적','Savings'),data:s,backgroundColor:P.green,borderRadius:5,maxBarThickness:40}]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:{top:20}},plugins:{legend:{position:'top',labels:{font:{size:12},padding:12}}},scales:{y:{beginAtZero:true,suggestedMax:Math.ceil(Math.max(...b,...s)*1.2)||10,title:{display:true,text:t('억원','100M'),font:{size:12}}}}}});}
function chart_InvestTypeTotal(){const eT=sum(filtered.filter(r=>r[1]==='확장'),16),eA=sum(filtered.filter(r=>r[1]==='확장'),17),nT=sum(filtered.filter(r=>r[1]==='경상'),16),nA=sum(filtered.filter(r=>r[1]==='경상'),17);mk('cInvestTypeTotal',{type:'bar',data:{labels:[t('확장','Exp.'),t('경상','Rec.')],datasets:[{label:t('목표','Target'),data:[eT,nT],backgroundColor:P.grayL,borderColor:P.gray,borderWidth:2,borderRadius:4},{label:t('실적','Actual'),data:[eA,nA],backgroundColor:P.red,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{font:{size:13}}},y:{beginAtZero:true,max:Math.ceil(Math.max(eT,eA,nT,nA)*1.25)||10,title:{display:true,text:t('억원','100M'),font:{size:12}}}}}});}
function chart_InvestTypeProduct(){const eT=[],eA=[],nT=[],nA=[];PRODUCTS.forEach(p=>{eT.push(sum(filtered.filter(r=>r[2]===p&&r[1]==='확장'),16));eA.push(sum(filtered.filter(r=>r[2]===p&&r[1]==='확장'),17));nT.push(sum(filtered.filter(r=>r[2]===p&&r[1]==='경상'),16));nA.push(sum(filtered.filter(r=>r[2]===p&&r[1]==='경상'),17));});mk('cInvestTypeProduct',{type:'bar',data:{labels:PRODUCTS.map(p=>pn(p)),datasets:[{label:t('확장목표','Exp.Tgt'),data:eT,backgroundColor:P.grayL,borderColor:P.gray,borderWidth:2,borderRadius:3},{label:t('확장실적','Exp.Act'),data:eA,backgroundColor:P.red,borderRadius:3},{label:t('경상목표','Rec.Tgt'),data:nT,backgroundColor:'rgba(160,160,160,0.25)',borderColor:'rgba(160,160,160,0.7)',borderWidth:2,borderRadius:3},{label:t('경상실적','Rec.Act'),data:nA,backgroundColor:'rgba(180,30,30,0.5)',borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top',labels:{font:{size:11},boxWidth:12,padding:8}}},scales:{x:{ticks:{font:{size:12}}},y:{beginAtZero:true,max:Math.ceil(Math.max(...eT,...eA,...nT,...nA)*1.25)||10,title:{display:true,text:t('억원','100M'),font:{size:12}}}}}});}
function chart_Activity(){const aL=[t('합계','Total'),t('①신기술 신공법','①New Tech'),t('②염가형 부품','②Low-cost Parts'),t('③중국/Local 설비','③China/Local'),t('④중국/한국 Collabo','④CN/KR Collabo'),t('⑤컨테이너(FR) 최소화','⑤Container Min.'),t('⑥출장인원 최소화','⑥Travel Min.'),t('⑦유휴설비','⑦Idle Equip'),t('⑧사양 최적화','⑧Spec Opt.'),t('⑨기타','⑨Others')];const tS=sum(filtered,17),aD=[18,19,20,21,22,23,24,25,26].map(i=>sum(filtered,i));const cols=[P.orange,P.amber,P.green,P.teal,P.blue,P.violet,P.pink,P.purple,P.red];mk('cActivity',{type:'bar',data:{labels:aL,datasets:[{label:t('절감(억원)','Savings'),data:[tS,...aD],backgroundColor:[P.purple,...cols],borderRadius:5}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,title:{display:true,text:t('억원','100M'),font:{size:12}}},y:{ticks:{font:{size:12},padding:6}}}}});}
function chart_Pie(){const pd=PRODUCTS.map(p=>sum(filtered.filter(r=>r[2]===p),17)),total=pd.reduce((a,b)=>a+b,0);const pc=[P.purple,P.amber,P.green,P.blue,P.red];const centerPlugin={id:'ctr',afterDraw(ch){const{ctx,chartArea:{left,right,top,bottom}}=ch;const cx=(left+right)/2,cy=(top+bottom)/2;ctx.save();ctx.font='700 22px "Noto Sans KR",sans-serif';ctx.fillStyle='#1a202c';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(total.toFixed(1),cx,cy-8);ctx.font='500 12px "Noto Sans KR",sans-serif';ctx.fillStyle='#718096';ctx.fillText(t('억원','100M'),cx,cy+14);ctx.restore();}};const lblPlugin={id:'plbl',afterDatasetsDraw(ch){const{ctx}=ch;ch.getDatasetMeta(0).data.forEach((arc,i)=>{const v=ch.data.datasets[0].data[i];if(!v||v<=0)return;const{x,y}=arc.tooltipPosition();ctx.save();ctx.font='600 12px "Noto Sans KR",sans-serif';ctx.fillStyle='#fff';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(v.toFixed(1),x,y);ctx.restore();});}};mk('cPie',{type:'doughnut',data:{labels:PRODUCTS.map(p=>pn(p)),datasets:[{data:pd,backgroundColor:pc,borderWidth:2,borderColor:'#fff'}]},options:{responsive:true,maintainAspectRatio:false,cutout:'55%',plugins:{legend:{position:'bottom',labels:{boxWidth:13,padding:12,font:{size:13}}}}},plugins:[centerPlugin,lblPlugin]});}
function chart_Corp(){const cT={},cA={};ALL_CORPS_ORDERED.forEach(c=>{cT[c]=0;cA[c]=0;});filtered.forEach(r=>{const c=r[3];if(c&&cT[c]!==undefined){cT[c]+=parseFloat(r[16])||0;cA[c]+=parseFloat(r[17])||0;}});mk('cCorp',{type:'bar',data:{labels:ALL_CORPS_ORDERED,datasets:[{label:t('절감 목표','Target'),data:ALL_CORPS_ORDERED.map(c=>cT[c]),backgroundColor:P.blueL,borderColor:P.blue,borderWidth:2,borderRadius:4},{label:t('절감 실적','Actual'),data:ALL_CORPS_ORDERED.map(c=>cA[c]),backgroundColor:P.green,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top',labels:{font:{size:13}}}},scales:{x:{ticks:{font:{size:12}}},y:{beginAtZero:true,suggestedMax:Math.ceil(Math.max(...ALL_CORPS_ORDERED.map(c=>cT[c]),...ALL_CORPS_ORDERED.map(c=>cA[c]))*1.2)||10,title:{display:true,text:t('억원','100M'),font:{size:13}}}}}});}
function chart_Monthly(){const labels=getLang()==='en'?['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']:MONTHLY_DATA.labels;const tgt=MONTHLY_DATA.target,act=MONTHLY_DATA.actual;const cT=[],cA=[];let st=0,sa=0;for(let i=0;i<12;i++){st+=tgt[i];cT.push(+st.toFixed(2));sa+=act[i];cA.push(+sa.toFixed(2));}const mB=Math.max(...tgt,...act,1),mC=Math.max(...cT,...cA,1);mk('cMonthly',{type:'bar',data:{labels,datasets:[{type:'bar',label:t('절감목표','Target'),data:tgt,order:1,backgroundColor:P.grayL,borderColor:P.gray,borderWidth:2,borderRadius:4,yAxisID:'y'},{type:'bar',label:t('절감실적','Actual'),data:act,order:2,backgroundColor:P.red,borderRadius:4,yAxisID:'y'},{type:'line',label:t('누적목표','Cum.Tgt'),data:cT,order:3,borderColor:'rgba(130,130,130,0.95)',backgroundColor:'transparent',borderDash:[6,3],borderWidth:2,pointRadius:5,pointBackgroundColor:'white',pointBorderColor:'rgba(130,130,130,0.95)',pointBorderWidth:2,tension:0.1,yAxisID:'y2'},{type:'line',label:t('누적실적','Cum.Act'),data:cA,order:4,borderColor:P.red,backgroundColor:'transparent',borderWidth:2.5,pointRadius:5,pointBackgroundColor:'white',pointBorderColor:P.red,pointBorderWidth:2,tension:0.1,yAxisID:'y2'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top',labels:{font:{size:12},boxWidth:14,padding:20}}},scales:{x:{ticks:{font:{size:12}}},y:{beginAtZero:true,position:'left',max:Math.ceil(mB*3),title:{display:true,text:t('월별(억원)','Monthly'),font:{size:12}}},y2:{beginAtZero:true,position:'right',max:Math.ceil(mC*1.3),title:{display:true,text:t('누적(억원)','Cumulative'),font:{size:12}},grid:{drawOnChartArea:false}}}}});}
function renderAll(){updateKPI();chart_BaseTotal();chart_BaseProduct();chart_InvestTypeTotal();chart_InvestTypeProduct();chart_Activity();chart_Pie();chart_Corp();chart_Monthly();}
window.onload=function(){initProductFilter();initTypeFilter();initCorpFilter('');initPurposeFilter();applyLang();renderAll();};
</script></body></html>"""

# ===== LIST TEMPLATE =====
LIST_TPL = r"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>실적 조회</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Noto Sans KR',sans-serif;font-size:13px;background:linear-gradient(135deg,#667eea,#764ba2);color:#333;padding:16px}
.top-header{background:linear-gradient(135deg,#4a5f9d,#5a4a8a);padding:18px 28px;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.15);margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.top-header h2{font-size:22px;font-weight:700;color:#fff;display:flex;align-items:center;gap:10px}
.top-header-right{display:flex;gap:12px;align-items:center}
.top-header a,.excel-btn{background:rgba(255,255,255,0.2);color:#fff;padding:10px 20px;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px;transition:all 0.3s;border:1px solid rgba(255,255,255,0.3);cursor:pointer;display:flex;align-items:center;gap:6px}
.lang-toggle-list{display:flex;gap:4px;background:rgba(255,255,255,0.15);border-radius:20px;padding:3px;border:1px solid rgba(255,255,255,0.2)}
.lang-btn-list{padding:6px 14px;border-radius:18px;font-size:12px;font-weight:700;cursor:pointer;border:none;background:transparent;color:rgba(255,255,255,0.6);transition:all 0.25s}
.lang-btn-list.active{background:rgba(255,255,255,0.9);color:#667eea}
.filter-bar{background:rgba(255,255,255,0.98);border-radius:12px;padding:16px 24px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin-bottom:16px;box-shadow:0 4px 16px rgba(0,0,0,0.08)}
.filter-bar label{font-weight:600;color:#667eea;font-size:14px}
.filter-bar select{padding:8px 32px 8px 12px;border:2px solid #e2e8f0;border-radius:8px;font-size:14px;background:#f8fafc;cursor:pointer}
.legend{margin-left:auto;display:flex;gap:16px;align-items:center;font-size:13px}
.legend-item{display:flex;align-items:center;gap:6px;color:#64748b;font-weight:500}
.sig{width:16px;height:16px;border-radius:50%;display:inline-block}
.s-g{background:radial-gradient(circle at 40% 35%,#34d399,#059669);box-shadow:0 0 6px rgba(16,185,129,0.5)}
.s-y{background:radial-gradient(circle at 40% 35%,#fcd34d,#f59e0b);box-shadow:0 0 6px rgba(245,158,11,0.5)}
.s-x{background:radial-gradient(circle at 40% 35%,#d1d5db,#94a3b8)}
.table-container{background:rgba(255,255,255,0.98);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.12);overflow:hidden}
.table-wrap{overflow-x:auto;overflow-y:auto;max-height:calc(100vh - 220px)}
table{border-collapse:collapse;white-space:nowrap;min-width:100%;background:#fff}
thead th{position:sticky;z-index:10;background:#667eea;color:#fff;font-weight:600;font-size:12px;padding:11px 9px;border:1px solid #94a3b8;text-align:center}
tr.gh th{top:0;z-index:12}
tr.gh+tr th{top:37px}
thead tr.gh th{background:#5a67d8;font-size:13px;padding:9px}
td.sc,th.sc{position:sticky;z-index:5;background:#f1f5f9}
th.sc{background:#667eea !important;z-index:15}
.c0{left:0;min-width:54px}.c1{left:54px;min-width:46px}.c2{left:100px;min-width:58px}.c3{left:158px;min-width:70px}.c4{left:228px;min-width:120px}.c5{left:348px;min-width:100px}
th.c0,th.c1,th.c2,th.c3,th.c4,th.c5{background:#667eea !important;z-index:15 !important}
tbody tr:nth-child(even) td.sc{background:#f1f5f9}
tbody tr:nth-child(odd) td.sc{background:#e2e8f0}
tbody tr:hover td.sc{background:#ddd6fe !important}
tbody td{padding:9px 11px;border:1px solid #94a3b8;font-size:13px;text-align:center;vertical-align:middle}
td.left{text-align:left}
td.act-cell{text-align:left;max-width:300px;white-space:normal;word-break:break-all;line-height:1.5}
tbody tr:nth-child(even) td{background:#f8fafc}
tbody tr:nth-child(odd) td{background:#fff}
tbody tr:hover td{background:#e0e7ff !important}
tfoot td{padding:10px 11px;border:1px solid #94a3b8;font-size:13px;text-align:center;font-weight:700;background:#fef3c7;color:#78350f}
th.reduce-col{min-width:100px!important;width:100px!important;max-width:100px!important;word-wrap:break-word;white-space:normal!important;font-size:10px}
th.gs{background:#3b82f6}th.gv{background:#10b981}th.gr{background:#fbbf24;color:#78350f}th.ge{background:#8b5cf6}
tr.gh .g-s{background:#2563eb}tr.gh .g-v{background:#059669}tr.gh .g-r{background:#f59e0b}tr.gh .g-e{background:#7c3aed}tr.gh .g-c{background:#5a67d8}
tr.gh th.sc{z-index:21 !important}
.footer-info{padding:12px 24px;font-size:14px;color:#64748b;background:rgba(255,255,255,0.95);border-top:2px solid #e2e8f0;font-weight:600}
.row-actions{display:flex;gap:6px;align-items:center;justify-content:center}
.icon-btn{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;cursor:pointer;border:none;background:#fff;font-size:14px;text-decoration:none;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
.icon-edit{color:#3b82f6}.icon-del{color:#ef4444}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
</head><body>
<div class="top-header">
  <h2>📊 <span class="i18n" data-ko="설비 투자비 활동 실적 조회" data-en="Investment Performance">설비 투자비 활동 실적 조회</span></h2>
  <div class="top-header-right">
    <div class="lang-toggle-list"><button class="lang-btn-list active" id="langKo2" onclick="setLang('ko')">🇰🇷 한글</button><button class="lang-btn-list" id="langEn2" onclick="setLang('en')">🇺🇸 ENG</button></div>
    <button class="excel-btn" onclick="downloadExcel()">📥 Excel</button>
    <a href="/dashboard">🏠 <span class="i18n" data-ko="대시보드" data-en="Dashboard">대시보드</span></a>
    <a href="/">◀ <span class="i18n" data-ko="입력" data-en="Entry">입력</span></a>
  </div>
</div>
<div class="filter-bar">
  <label><span class="i18n" data-ko="제품" data-en="Product">제품</span></label>
  <select id="fp" onchange="applyFilter();updateFilterCorps()"></select>
  <label><span class="i18n" data-ko="법인" data-en="Corp.">법인</span></label>
  <select id="fc" onchange="applyFilter()"></select>
  <label><span class="i18n" data-ko="투자유형" data-en="Type">투자유형</span></label>
  <select id="ft" onchange="applyFilter()"></select>
  <label><span class="i18n" data-ko="투자목적" data-en="Purpose">투자목적</span></label>
  <select id="fpu" onchange="applyFilter()"></select>
  <div class="legend">
    <div class="legend-item"><span class="sig s-g"></span><span class="i18n" data-ko="목표초과" data-en="Above">목표초과</span></div>
    <div class="legend-item"><span class="sig s-y"></span><span class="i18n" data-ko="미달" data-en="Below">미달</span></div>
    <div class="legend-item"><span class="sig s-x"></span><span class="i18n" data-ko="미입력" data-en="N/A">미입력</span></div>
  </div>
</div>
<div class="table-container"><div class="table-wrap">
  <table id="mainTable"><thead>
    <tr class="gh">
      <th class="sc c0 g-c" style="border-right:0"></th>
      <th class="sc c1 g-c" style="border-left:0;border-right:0"></th>
      <th class="sc c2 g-c" style="border-left:0;border-right:0;position:relative;overflow:visible"><span class="i18n" data-ko="투자 분류" data-en="Classification" style="position:absolute;white-space:nowrap;left:50%;top:50%;transform:translate(-50%,-50%);z-index:1">투자 분류</span></th>
      <th class="sc c3 g-c" style="border-left:0;border-right:0"></th>
      <th class="sc c4 g-c" style="border-left:0;border-right:0"></th>
      <th class="sc c5 g-c" style="border-left:0"></th>
      <th class="g-s" colspan="7">📅 <span class="i18n" data-ko="일정" data-en="Schedule">일정</span></th>
      <th class="g-v" colspan="4">💰 <span class="i18n" data-ko="투자절감" data-en="Savings">투자절감</span></th>
      <th class="g-r" colspan="11">📊 <span class="i18n" data-ko="절감활동" data-en="Activities">절감활동</span></th>
      <th class="g-e" colspan="3">🎯 <span class="i18n" data-ko="목표" data-en="Target">목표</span></th>
    </tr>
    <tr>
      <th class="sc c0"><span class="i18n" data-ko="수정" data-en="Edit">수정</span></th><th class="sc c1"><span class="i18n" data-ko="제품" data-en="Product">제품</span></th><th class="sc c2"><span class="i18n" data-ko="법인" data-en="Corp">법인</span></th><th class="sc c3"><span class="i18n" data-ko="유형" data-en="Type">유형</span></th><th class="sc c4"><span class="i18n" data-ko="투자항목" data-en="Item">투자항목</span></th><th class="sc c5"><span class="i18n" data-ko="목적" data-en="Purpose">목적</span></th>
      <th class="gs"><span class="i18n" data-ko="발주목표" data-en="Order Tgt">발주목표</span></th><th class="gs"><span class="i18n" data-ko="발주실적" data-en="Order Act">발주실적</span></th><th class="gs"><span class="i18n" data-ko="셋업목표" data-en="Setup Tgt">셋업목표</span></th><th class="gs"><span class="i18n" data-ko="셋업실적" data-en="Setup Act">셋업실적</span></th><th class="gs"><span class="i18n" data-ko="양산목표" data-en="Mass Tgt">양산목표</span></th><th class="gs"><span class="i18n" data-ko="양산실적" data-en="Mass Act">양산실적</span></th><th class="gs"><span class="i18n" data-ko="연기사유" data-en="Delay">연기사유</span></th>
      <th class="gv">Base</th><th class="gv"><span class="i18n" data-ko="발주가목표" data-en="Ord.Price Tgt">발주가목표</span></th><th class="gv"><span class="i18n" data-ko="발주가실적" data-en="Ord.Price Act">발주가실적</span></th><th class="gv"><span class="i18n" data-ko="절감목표" data-en="Save Tgt">절감목표</span></th>
      <th class="gr"><span class="i18n" data-ko="절감실적" data-en="Savings">절감실적</span></th><th class="gr reduce-col"><span class="i18n" data-ko="①신기술/신공법" data-en="①NewTech">①신기술/신공법</span></th><th class="gr reduce-col"><span class="i18n" data-ko="②염가형 부품" data-en="②LowCost">②염가형 부품</span></th><th class="gr reduce-col"><span class="i18n" data-ko="③중국/Local 설비" data-en="③China/Local">③중국/Local 설비</span></th><th class="gr reduce-col"><span class="i18n" data-ko="④중국/한국 Collabo" data-en="④CN/KR Collabo">④중국/한국 Collabo</span></th><th class="gr reduce-col"><span class="i18n" data-ko="⑤컨테이너(FR) 최소화" data-en="⑤Container Min">⑤컨테이너(FR) 최소화</span></th><th class="gr reduce-col"><span class="i18n" data-ko="⑥출장인원 최소화" data-en="⑥Travel Min">⑥출장인원 최소화</span></th><th class="gr reduce-col"><span class="i18n" data-ko="⑦유휴설비" data-en="⑦Idle">⑦유휴설비</span></th><th class="gr reduce-col"><span class="i18n" data-ko="⑧사양최적화" data-en="⑧Spec Opt">⑧사양최적화</span></th><th class="gr reduce-col"><span class="i18n" data-ko="⑨기타" data-en="⑨Others">⑨기타</span></th><th class="gr"><span class="i18n" data-ko="활동" data-en="Activity">활동</span></th>
      <th class="ge"><span class="i18n" data-ko="목표%" data-en="Tgt%">목표%</span></th><th class="ge"><span class="i18n" data-ko="실적%" data-en="Act%">실적%</span></th><th class="ge">Signal</th>
    </tr>
  </thead><tbody id="tableBody"></tbody><tfoot id="tableFoot"></tfoot></table>
</div><div class="footer-info" id="footerInfo">총 0건</div></div>
<script>
const DATA={{ processed_json | safe }};const MONTHS={{ months_json | safe }};const CORPORATIONS={{ corporations_json | safe }};const ALL_PURPOSES={{ all_purposes_json | safe }};
function f(v){return(v!=null&&v!=="")? v:"-";}
function deleteRow(id){if(!confirm("삭제?"))return;fetch("/delete/"+id,{method:"POST"}).then(r=>r.json()).then(d=>{if(d.success)location.reload();});}
function updateFilterCorps(){const p=document.getElementById('fp').value,s=document.getElementById('fc');let corps=[];if(p&&CORPORATIONS[p])corps=CORPORATIONS[p];else{const a=new Set();Object.values(CORPORATIONS).forEach(x=>x.forEach(c=>a.add(c)));corps=[...a].sort();}const cur=s.value;s.innerHTML='<option value="">'+tl('전체','All')+'</option>';corps.forEach(c=>{const o=document.createElement('option');o.value=o.textContent=c;s.appendChild(o);});if(corps.includes(cur))s.value=cur;}
function renderTable(data){
  const tb=document.getElementById("tableBody"),tf=document.getElementById("tableFoot");
  let out="",tot={base:0,opt:0,opa:0,sgt:0,sga:0,r:[0,0,0,0,0,0,0,0,0]};
  const _LP={'키친':'Kitchen','빌트인쿠킹':'Built-in Cooking','리빙':'Living','부품':'Parts','ES':'ES'};
  const _TP={'확장':'Expansion','경상':'Recurring'};
  const _PP={'신규라인':'New Line','자동화':'Automation','라인 개조':'Line Remodel','Overhaul':'Overhaul','신모델 대응':'New Model','T/Time 향상':'T/Time Improve','고장 수리':'Repair','안전':'Safety','설비 이설':'Equip. Relocation','노후 교체':'Aging Replace','설비 개선':'Equip. Improve','기타':'Others'};
  const _en=localStorage.getItem('app_lang')==='en';
  function _t(v,map){return _en?(map[v]||v):(v||'-');}
  data.forEach(r=>{
    const rid=r[0],prod=r[2]||"";let h="<tr>";
    h+="<td class='sc c0'><div class='row-actions'><a href='/edit/"+rid+"' class='icon-btn icon-edit'>✏️</a><button class='icon-btn icon-del' onclick='deleteRow("+rid+")'>🗑️</button></div></td>";
    h+="<td class='sc c1'>"+_t(r[2],_LP)+"</td><td class='sc c2'>"+f(r[3])+"</td><td class='sc c3'>"+_t(r[1],_TP)+"</td><td class='sc c4 left'>"+f(r[5])+"</td><td class='sc c5'>"+_t(r[4],_PP)+"</td>";
    h+="<td>"+f(r[6])+"</td><td>"+f(r[7])+"</td><td>"+f(r[8])+"</td><td>"+f(r[9])+"</td><td>"+f(r[10])+"</td><td>"+f(r[11])+"</td><td class='left'>"+f(r[12])+"</td>";
    const base=parseFloat(r[13])||0,opt=parseFloat(r[14])||0,opa=parseFloat(r[15])||0,sgt=parseFloat(r[16])||0,sga=parseFloat(r[17])||0;
    tot.base+=base;tot.opt+=opt;tot.opa+=opa;tot.sgt+=sgt;tot.sga+=sga;
    h+="<td>"+f(r[13])+"</td><td>"+f(r[14])+"</td><td>"+f(r[15])+"</td><td>"+f(r[16])+"</td><td>"+f(r[17])+"</td>";
    for(let i=18;i<=26;i++){tot.r[i-18]+=(parseFloat(r[i])||0);h+="<td>"+f(r[i])+"</td>";}
    h+="<td class='act-cell'>"+f(r[28])+"</td>";
    const rTgt=(prod==="ES")?50:30;let rAct="-",rActNum=null;
    if(base>0&&sga>0){rActNum=(sga/base)*100;rAct=rActNum.toFixed(1);}else if(base>0){rActNum=0;rAct="0";}
    let sig="s-x";if(rActNum!==null)sig=rActNum>=rTgt?"s-g":"s-y";
    h+="<td>"+rTgt+"%</td><td>"+(rAct!=="-"?rAct+"%":"-")+"</td><td style='text-align:center'><span class='sig "+sig+"' style='display:inline-block'></span></td></tr>";
    out+=h;
  });
  tb.innerHTML=out;
  const _tl=localStorage.getItem('app_lang')==='en'?'Total':'합계';let foot="<tr><td colspan='6' style='text-align:center;background:#fef9c3;font-weight:700'>"+_tl+"</td><td colspan='7' style='background:#fef9c3'></td>";
  foot+="<td>"+tot.base.toFixed(2)+"</td><td>"+tot.opt.toFixed(2)+"</td><td>"+tot.opa.toFixed(2)+"</td><td>"+tot.sgt.toFixed(2)+"</td><td>"+tot.sga.toFixed(2)+"</td>";
  tot.r.forEach(v=>{foot+="<td>"+v.toFixed(2)+"</td>";});foot+="<td colspan='4' style='background:#fef9c3'></td></tr>";
  tf.innerHTML=foot;document.getElementById("footerInfo").textContent=(localStorage.getItem("app_lang")==="en"?"Total "+data.length+" items":"총 "+data.length+"건");
}
function applyFilter(){const fp=document.getElementById("fp").value,fc=document.getElementById("fc").value,ft=document.getElementById("ft").value,fpu=document.getElementById("fpu").value;renderTable(DATA.filter(r=>(!fp||r[2]===fp)&&(!fc||r[3]===fc)&&(!ft||r[1]===ft)&&(!fpu||r[4]===fpu)));}
function downloadExcel(){const wb=XLSX.utils.book_new();const h=[["제품","법인","유형","항목","목적","발주목표","발주실적","셋업목표","셋업실적","양산목표","양산실적","연기사유","Base","발주가목표","발주가실적","절감목표","절감실적","①","②","③","④","⑤","⑥","⑦","⑧","⑨","활동","목표%","실적%"]];const rows=DATA.map(r=>{const b=parseFloat(r[13])||0,s=parseFloat(r[17])||0,rt=(r[2]==="ES")?50:30;let ra="-";if(b>0&&s>0)ra=((s/b)*100).toFixed(1);else if(b>0)ra="0";return[r[2],r[3],r[1],r[5],r[4],r[6],r[7],r[8],r[9],r[10],r[11],r[12],r[13],r[14],r[15],r[16],r[17],r[18],r[19],r[20],r[21],r[22],r[23],r[24],r[25],r[26],r[28],rt,ra];});const ws=XLSX.utils.aoa_to_sheet([...h,...rows]);XLSX.utils.book_append_sheet(wb,ws,"투자실적");XLSX.writeFile(wb,"설비투자비_"+new Date().toISOString().slice(0,10)+".xlsx");}
function setLang(l){localStorage.setItem('app_lang',l);document.getElementById('langKo2').classList.toggle('active',l==='ko');document.getElementById('langEn2').classList.toggle('active',l==='en');applyLang();initListFilters();applyFilter();}
function applyLang(){const l=localStorage.getItem('app_lang')||'ko';document.getElementById('langKo2').classList.toggle('active',l==='ko');document.getElementById('langEn2').classList.toggle('active',l==='en');document.querySelectorAll('.i18n').forEach(el=>{const t=el.getAttribute('data-'+l);if(t)el.innerHTML=t.replace(/\n/g,'<br>');});}
const LP={'키친':'Kitchen','빌트인쿠킹':'Built-in Cooking','리빙':'Living','부품':'Parts','ES':'ES'};
function tl(ko,en){return(localStorage.getItem('app_lang')==='en')?en:ko;}
function initListFilters(){const l=localStorage.getItem('app_lang')||'ko';const fp=document.getElementById('fp'),cfp=fp.value;fp.innerHTML='<option value="">'+tl('전체','All')+'</option>';['키친','빌트인쿠킹','리빙','부품','ES'].forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=l==='en'?(LP[p]||p):p;fp.appendChild(o);});if(cfp)fp.value=cfp;const ft=document.getElementById('ft'),cft=ft.value;ft.innerHTML='<option value="">'+tl('전체','All')+'</option>';const o1=document.createElement('option');o1.value='확장';o1.textContent=tl('확장','Expansion');ft.appendChild(o1);const o2=document.createElement('option');o2.value='경상';o2.textContent=tl('경상','Recurring');ft.appendChild(o2);if(cft)ft.value=cft;updateFilterCorps();const _PP2={'신규라인':'New Line','자동화':'Automation','라인 개조':'Line Remodel','Overhaul':'Overhaul','신모델 대응':'New Model','T/Time 향상':'T/Time Improve','고장 수리':'Repair','안전':'Safety','설비 이설':'Equip. Relocation','노후 교체':'Aging Replace','설비 개선':'Equip. Improve','기타':'Others'};const fpu=document.getElementById('fpu'),cfpu=fpu.value;fpu.innerHTML='<option value="">'+tl('전체','All')+'</option>';ALL_PURPOSES.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=l==='en'?(_PP2[p]||p):p;fpu.appendChild(o);});if(cfpu)fpu.value=cfpu;}
window.onload=function(){applyLang();initListFilters();renderTable(DATA);}
</script></body></html>"""

if __name__ == "__main__":
    print("🚀 서버 시작: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)