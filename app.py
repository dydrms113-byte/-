from flask import Flask, request, redirect, render_template_string, jsonify
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS investment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    c.execute("PRAGMA table_info(investment)")
    columns = [col[1] for col in c.fetchall()]
    if 'updated_at' not in columns:
        c.execute("ALTER TABLE investment ADD COLUMN updated_at TEXT")
    c.execute("""
    CREATE TABLE IF NOT EXISTS investment_monthly (
        id INTEGER, year_month TEXT,
        monthly_target REAL DEFAULT 0, monthly_actual REAL DEFAULT 0,
        PRIMARY KEY (id, year_month),
        FOREIGN KEY (id) REFERENCES investment(id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM investment ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    processed = []
    for r in rows:
        r = list(r)
        base = r[13] if r[13] else 0
        sav_act = r[17] if r[17] else 0
        product = r[2] if r[2] else ""
        rate_target = 50 if product == "ES" else 30
        rate_actual = "-"
        if base and base != 0:
            rate_actual = round((sav_act/base)*100, 1) if sav_act else 0
        r.append(rate_target)
        r.append(rate_actual)
        timestamp = r[30] if len(r) > 30 and r[30] else (r[29] if len(r) > 29 else "")
        r.append(timestamp)
        processed.append(r)
    return processed

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
        edit_data=edit_data, row_id=row_id)

@app.route("/save", methods=["POST"])
def save():
    try:
        f = request.form
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        row_id = f.get("row_id")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        values = (
            f.get("invest_type") or "", f.get("product") or "",
            f.get("corporation") or "", f.get("purpose") or "",
            f.get("invest_item") or "", f.get("order_target") or "",
            f.get("order_actual") or "", f.get("setup_target") or "",
            f.get("setup_actual") or "", f.get("mass_target") or "",
            f.get("mass_actual") or "", f.get("delay_reason") or "",
            nz(f.get("base_amount")), nz(f.get("order_price_target")),
            nz(f.get("order_price_actual")), nz(f.get("saving_target")),
            nz(f.get("saving_actual")), nz(f.get("reduce_1")),
            nz(f.get("reduce_2")), nz(f.get("reduce_3")), nz(f.get("reduce_4")),
            nz(f.get("reduce_5")), nz(f.get("reduce_6")), nz(f.get("reduce_7")),
            nz(f.get("reduce_8")), nz(f.get("reduce_9")),
            nz(f.get("saving_total")), f.get("activity") or ""
        )
        if row_id:
            c.execute("""UPDATE investment SET
                invest_type=?,product=?,corporation=?,purpose=?,invest_item=?,
                order_target=?,order_actual=?,setup_target=?,setup_actual=?,
                mass_target=?,mass_actual=?,delay_reason=?,base_amount=?,
                order_price_target=?,order_price_actual=?,saving_target=?,saving_actual=?,
                reduce_1=?,reduce_2=?,reduce_3=?,reduce_4=?,reduce_5=?,
                reduce_6=?,reduce_7=?,reduce_8=?,reduce_9=?,
                saving_total=?,activity=?,updated_at=? WHERE id=?""", values + (now, row_id))
            c.execute("DELETE FROM investment_monthly WHERE id=?", (row_id,))
            target_id = int(row_id)
        else:
            c.execute("""INSERT INTO investment (
                invest_type,product,corporation,purpose,invest_item,
                order_target,order_actual,setup_target,setup_actual,
                mass_target,mass_actual,delay_reason,base_amount,
                order_price_target,order_price_actual,saving_target,saving_actual,
                reduce_1,reduce_2,reduce_3,reduce_4,reduce_5,
                reduce_6,reduce_7,reduce_8,reduce_9,
                saving_total,activity,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            values + (now, now))
            target_id = c.lastrowid
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
        return redirect("/list")
    except Exception as e:
        import traceback; traceback.print_exc()
        return f"저장 오류: {e}", 500

@app.route("/dashboard")
def dashboard():
    processed = get_processed_rows()
    months_2026 = [f"2026-{m:02d}" for m in range(1,13)]
    monthly_target = {m: 0.0 for m in months_2026}
    monthly_actual = {m: 0.0 for m in months_2026}
    for r in processed:
        ot = r[6] if r[6] else ""
        oa = r[7] if r[7] else ""
        st = float(r[16]) if r[16] else 0.0
        sa = float(r[17]) if r[17] else 0.0
        if ot in monthly_target:
            monthly_target[ot] += st
        if oa in monthly_actual:
            monthly_actual[oa] += sa
    monthly_json = json.dumps({
        "labels": [f"{m}월" for m in range(1,13)],
        "target": [round(monthly_target[f"2026-{m:02d}"],2) for m in range(1,13)],
        "actual": [round(monthly_actual[f"2026-{m:02d}"],2) for m in range(1,13)]
    }, ensure_ascii=False)
    return render_template_string(DASHBOARD_TPL,
        processed_json=json.dumps(processed, ensure_ascii=False),
        corporations_json=json.dumps(CORPORATIONS, ensure_ascii=False),
        monthly_json=monthly_json,
        all_purposes_json=json.dumps(ALL_PURPOSES, ensure_ascii=False))

@app.route("/list")
def list_page():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM investment ORDER BY id DESC")
    rows = c.fetchall()
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
        sav_act = r[17] if r[17] else 0
        product = r[2] if r[2] else ""
        rate_target = 50 if product == "ES" else 30
        rate_actual = "-"
        if base and base != 0:
            rate_actual = round((sav_act/base)*100, 1) if sav_act else 0
        r.append(rate_target)
        r.append(rate_actual)
        timestamp = r[30] if len(r) > 30 and r[30] else r[29]
        r.append(timestamp)
        processed.append(r)
    return render_template_string(LIST_TPL,
        processed_json=json.dumps(processed, ensure_ascii=False),
        months_json=json.dumps(MONTHS, ensure_ascii=False),
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
    return jsonify({"success": True})

# ===== TEMPLATES =====

INPUT_TPL = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>설비투자비 한계돌파 실적 관리 시스템</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans KR',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:16px;font-size:14px}
.header{background:linear-gradient(135deg,#4a5f9d 0%,#5a4a8a 100%);border-radius:12px;padding:18px 30px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 4px 12px rgba(0,0,0,0.2);max-width:1600px;margin-left:auto;margin-right:auto}
.header h1{color:white;font-size:22px;font-weight:700;display:flex;align-items:center;gap:10px}
.header-right{display:flex;gap:12px;align-items:center}
.header-btn{background:rgba(255,255,255,0.15);color:white;border:1px solid rgba(255,255,255,0.3);padding:10px 20px;border-radius:8px;font-size:14px;font-weight:500;text-decoration:none;transition:all 0.3s;display:flex;align-items:center;gap:6px}
.header-btn:hover{background:rgba(255,255,255,0.25)}
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
</style>
</head>
<body>
<div class="header">
  <h1>📋 설비투자비 한계돌파 실적 관리 시스템</h1>
  <div class="header-right">
    <a href="/dashboard" class="header-btn">🏠 대시보드</a>
    <a href="/" class="header-btn">📄 Data 입력</a>
    <a href="/list" class="header-btn">📊 투자실적 조회</a>
  </div>
</div>
<div class="container">
  <form method="post" action="/save" id="mainForm">
  {%- if row_id -%}<input type="hidden" name="row_id" value="{{ row_id }}">{%- endif -%}
  <div class="row">
    <div class="card">
      <div class="card-header pink">📌 <span class="i18n" data-ko="투자 분류" data-en="Investment Classification">투자 분류</span></div>
      <div class="card-body">
        <div class="form-group">
          <div class="form-label">💼 <span class="i18n" data-ko="투자 유형" data-en="Investment Type">투자 유형</span></div>
          <div class="toggle-group">
            <div class="toggle-btn {%- if not edit_data or edit_data[1]=='확장' %} active{%- endif -%}" onclick="selectType(this,'확장')"><span class="i18n" data-ko="확장" data-en="Expansion">확장</span></div>
            <div class="toggle-btn {%- if edit_data and edit_data[1]=='경상' %} active{%- endif -%}" onclick="selectType(this,'경상')"><span class="i18n" data-ko="경상" data-en="Recurring">경상</span></div>
          </div>
          <input type="hidden" name="invest_type" id="invest_type" value="{%- if edit_data -%}{{ edit_data[1] or '확장' }}{%- else -%}확장{%- endif -%}">
        </div>
        <div class="form-row">
          <div class="form-group">
            <div class="form-label">📦 <span class="i18n" data-ko="제품" data-en="Product">제품</span></div>
            <select name="product" id="product" onchange="updateCorporations()">
              {%- for p in products -%}<option {%- if edit_data and edit_data[2]==p %} selected{%- endif -%}>{{ p }}</option>{%- endfor -%}
            </select>
          </div>
          <div class="form-group">
            <div class="form-label">🌍 <span class="i18n" data-ko="법인" data-en="Corporation">법인</span></div>
            <select name="corporation" id="corporation"></select>
          </div>
        </div>
        <div class="info-box">
          <div class="info-box-title">💡 TIP</div>
          <div class="info-box-text">• 5천만원 미만인 경상투자 건은 Base금액을 집행가로 기입<br>• 해외 법인은 HQ 생산기술에서 검토/지원해주는 투자 건만 기입</div>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-header cyan">📋 <span class="i18n" data-ko="투자 항목 상세" data-en="Investment Item Details">투자 항목 상세</span></div>
      <div class="card-body">
        <div class="form-group">
          <div class="form-label">🎯 <span class="i18n" data-ko="투자목적" data-en="Investment Purpose">투자목적</span></div>
          <select name="purpose">
            {%- for p in all_purposes -%}<option {%- if edit_data and edit_data[4]==p %} selected{%- endif -%}>{{ p }}</option>{%- endfor -%}
          </select>
        </div>
        <div class="form-group">
          <div class="form-label">📝 <span class="i18n" data-ko="투자항목" data-en="Investment Item">투자항목</span></div>
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
    <div class="card-header amber">📅 <span class="i18n" data-ko="투자 주요 일정" data-en="Investment Schedule">투자 주요 일정</span></div>
    <div class="card-body">
      <div class="form-row">
        <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="발주 목표" data-en="Order Target">발주 목표</span></div><input type="month" name="order_target" value="{%- if edit_data -%}{{ edit_data[6] or '' }}{%- endif -%}"></div>
        <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="발주 실적" data-en="Order Actual">발주 실적</span></div><input type="month" name="order_actual" value="{%- if edit_data -%}{{ edit_data[7] or '' }}{%- endif -%}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="셋업 목표" data-en="Setup Target">셋업 목표</span></div><input type="month" name="setup_target" value="{%- if edit_data -%}{{ edit_data[8] or '' }}{%- endif -%}"></div>
        <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="셋업 실적" data-en="Setup Actual">셋업 실적</span></div><input type="month" name="setup_actual" value="{%- if edit_data -%}{{ edit_data[9] or '' }}{%- endif -%}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="양산 목표" data-en="Mass Prod. Target">양산 목표</span></div><input type="month" name="mass_target" value="{%- if edit_data -%}{{ edit_data[10] or '' }}{%- endif -%}"></div>
        <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="양산 실적" data-en="Mass Prod. Actual">양산 실적</span></div><input type="month" name="mass_actual" value="{%- if edit_data -%}{{ edit_data[11] or '' }}{%- endif -%}"></div>
      </div>
      <div class="form-group">
        <div class="form-label">❓ <span class="i18n" data-ko="연기사유" data-en="Delay Reason">연기사유</span></div>
        <input type="text" name="delay_reason" value="{%- if edit_data -%}{{ edit_data[12] or '' }}{%- endif -%}" placeholder="예: 제품개발 지연에 따른 양산 일정">
      </div>
    </div>
  </div>
  <div class="row" style="margin-top:24px">
    <div class="card">
      <div class="card-header blue">💰 <span class="i18n" data-ko="투자금액 (단위: 억원)" data-en="Investment Amount (unit: 100M KRW)">투자금액 (단위: 억원)</span></div>
      <div class="card-body">
        <div class="form-group"><div class="form-label">💵 <span class="i18n" data-ko="Base 금액" data-en="Base Amount">Base 금액</span></div><input type="number" name="base_amount" step="0.01" value="{%- if edit_data -%}{{ edit_data[13] or '' }}{%- endif -%}" placeholder="0.00"></div>
        <div class="form-row">
          <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="발주가 목표" data-en="Order Price Target">발주가 목표</span></div><input type="number" name="order_price_target" step="0.01" value="{%- if edit_data -%}{{ edit_data[14] or '' }}{%- endif -%}" placeholder="0.00"></div>
          <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="발주가 실적" data-en="Order Price Actual">발주가 실적</span></div><input type="number" name="order_price_actual" step="0.01" value="{%- if edit_data -%}{{ edit_data[15] or '' }}{%- endif -%}" placeholder="0.00"></div>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-header violet">📊 <span class="i18n" data-ko="절감 실적 (단위: 억원)" data-en="Savings Performance (unit: 100M KRW)">절감 실적 (단위: 억원)</span></div>
      <div class="card-body">
        <div class="form-row">
          <div class="form-group"><div class="form-label">🎯 <span class="i18n" data-ko="절감 목표" data-en="Savings Target">절감 목표</span></div><input type="number" name="saving_target" step="0.01" value="{%- if edit_data -%}{{ edit_data[16] or '' }}{%- endif -%}" placeholder="0.00"></div>
          <div class="form-group"><div class="form-label">✅ <span class="i18n" data-ko="절감 실적 (자동계산)" data-en="Savings Actual (auto)">절감 실적 (자동계산)</span></div><input id="saving_actual" name="saving_actual" readonly value="{%- if edit_data -%}{{ edit_data[17] or '' }}{%- endif -%}" placeholder="0.00"></div>
        </div>
        <div class="info-box"><div class="info-box-title">💡 절감 실적은 아래 세부 항목 합계가 자동 계산됩니다</div></div>
      </div>
    </div>
  </div>
  <div class="card card-full">
    <div class="card-header emerald">📊 <span class="i18n" data-ko="투자비 절감 활동 실적 (단위: 억원)" data-en="Cost Reduction Activities (unit: 100M KRW)">투자비 절감 활동 실적 (단위: 억원)</span></div>
    <div class="card-body">
      <div class="table-wrapper">
        <table class="reduce-table">
          <thead>
            <tr>
              <th style="width:110px"><span class="i18n" data-ko="항목" data-en="Item">항목</span></th>
              <th style="width:100px"><span class="i18n" data-ko="활동 합계" data-en="Total">활동 합계</span></th>
              <th><span class="reduce-number">①</span><span class="i18n" data-ko="신기술&#10;신공법" data-en="New Tech">신기술<br>신공법</span></th>
              <th><span class="reduce-number">②</span><span class="i18n" data-ko="염가형&#10;부품" data-en="Low-cost&#10;Parts">염가형<br>부품</span></th>
              <th><span class="reduce-number">③</span><span class="i18n" data-ko="중국/&#10;Local 설비" data-en="China/&#10;Local Equip">중국/<br>Local 설비</span></th>
              <th><span class="reduce-number">④</span><span class="i18n" data-ko="중국/한국&#10;Collabo" data-en="CN/KR&#10;Collabo">중국/한국<br>Collabo</span></th>
              <th><span class="reduce-number">⑤</span><span class="i18n" data-ko="컨테이너&#10;최소화" data-en="Container&#10;Min.">컨테이너<br>최소화</span></th>
              <th><span class="reduce-number">⑥</span><span class="i18n" data-ko="출장 인원&#10;최소화" data-en="Travel&#10;Min.">출장 인원<br>최소화</span></th>
              <th><span class="reduce-number">⑦</span><span class="i18n" data-ko="유휴&#10;설비" data-en="Idle&#10;Equip">유휴<br>설비</span></th>
              <th><span class="reduce-number">⑧</span><span class="i18n" data-ko="사양&#10;최적화" data-en="Spec&#10;Optimize">사양<br>최적화</span></th>
              <th><span class="reduce-number">⑨</span><span class="i18n" data-ko="기타" data-en="Others">기타</span></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="i18n" data-ko="절감 실적" data-en="Savings">절감 실적</span></td>
              <td><input id="total_display" readonly value="{%- if edit_data -%}{{ edit_data[27] or '0.00' }}{%- else -%}0.00{%- endif -%}"></td>
              {%- for i in range(18,27) -%}
              <td><input class="reduce" type="number" name="reduce_{{ i-17 }}" step="0.01" value="{%- if edit_data -%}{{ edit_data[i] or '' }}{%- endif -%}" oninput="calcTotal()"></td>
              {%- endfor -%}
            </tr>
          </tbody>
        </table>
      </div>
      <div class="activity-section">
        <div class="activity-label">📝 <span class="i18n" data-ko="활동내용" data-en="Activity Details">활동내용</span></div>
        <textarea name="activity" placeholder="절감 활동 내용을 상세히 입력하세요">{%- if edit_data -%}{{ edit_data[28] or '' }}{%- endif -%}</textarea>
      </div>
    </div>
  </div>
  <input type="hidden" name="saving_total" id="saving_total" value="{%- if edit_data -%}{{ edit_data[27] or '' }}{%- endif -%}">
  <div class="button-group">
    <button type="submit" class="btn-primary">💾 <span class="i18n" data-ko="저장하기" data-en="Save">저장하기</span></button>
    <a href="/list" class="btn-secondary">📊 <span class="i18n" data-ko="투자실적 조회" data-en="View Records">투자실적 조회</span></a>
  </div>
  </form>
</div>
<script>
const CORPORATIONS = {{ corporations_json | safe }};
const EDIT_PRODUCT = {%- if edit_data -%}"{{ edit_data[2] or '키친' }}"{%- else -%}"키친"{%- endif -%};
const EDIT_CORPORATION = {%- if edit_data -%}"{{ edit_data[3] or '' }}"{%- else -%}""{%- endif -%};
function updateCorporations(){
  const p=document.getElementById('product').value;
  const s=document.getElementById('corporation');
  s.innerHTML='';
  (CORPORATIONS[p]||[]).forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;s.appendChild(o);});
}
function selectType(btn,type){
  document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('invest_type').value=type;
}
function calcTotal(){
  let s=0;
  document.querySelectorAll(".reduce").forEach(e=>{s+=Number(e.value)||0;});
  const t=s.toFixed(2);
  document.getElementById("saving_actual").value=t;
  document.getElementById("saving_total").value=t;
  document.getElementById("total_display").value=t;
}
/* i18n: read lang from localStorage */
function applyLang(){
  const lang = localStorage.getItem('app_lang') || 'ko';
  document.querySelectorAll('.i18n').forEach(el=>{
    const txt = el.getAttribute('data-'+lang);
    if(txt) el.innerHTML = txt.replace(/\n/g,'<br>');
  });
}
window.onload=function(){updateCorporations();if(EDIT_CORPORATION)document.getElementById('corporation').value=EDIT_CORPORATION;calcTotal();applyLang();}
</script>
</body>
</html>"""


DASHBOARD_TPL = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>설비투자비 대시보드</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans KR',sans-serif;background:#eef0f4;display:flex;min-height:100vh;font-size:14px}

/* ── 사이드바 ── */
.sidebar{width:230px;min-height:100vh;background:linear-gradient(180deg,#1e2a45 0%,#0f1724 100%);display:flex;flex-direction:column;position:fixed;top:0;left:0;z-index:100;box-shadow:3px 0 15px rgba(0,0,0,0.3)}

/* ── [수정1] LG전자 로고: LG 빨간 원형 아이콘 + 회색 텍스트 (공식 로고 스타일) ── */
.logo-wrap{padding:22px 18px 18px;border-bottom:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:12px}
.logo-circle{
  width:44px;height:44px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%, #f04050 0%, #c8102e 50%, #8b0000 100%);
  display:flex;align-items:center;justify-content:center;
  box-shadow:inset -2px -2px 6px rgba(0,0,0,0.3), inset 2px 2px 6px rgba(255,255,255,0.2), 0 2px 8px rgba(0,0,0,0.3);
  position:relative;flex-shrink:0;
}
.logo-circle::after{
  content:'';position:absolute;width:22px;height:22px;border-radius:50%;
  border:2.5px solid rgba(255,255,255,0.85);border-right-color:transparent;
  transform:rotate(-30deg);top:8px;left:8px;
}
.logo-circle-letter{
  font-size:16px;font-weight:900;color:white;font-family:Arial,Helvetica,sans-serif;
  letter-spacing:-1px;position:relative;z-index:1;margin-top:2px;margin-left:1px;
  text-shadow:0 1px 2px rgba(0,0,0,0.3);
}
.logo-text-group{display:flex;align-items:baseline;gap:1px}
.logo-text-lg{font-size:26px;font-weight:900;color:#d1d5db;letter-spacing:1px;font-family:'Noto Sans KR',Arial,sans-serif;line-height:1}
.logo-text-sub{font-size:22px;font-weight:700;color:#d1d5db;font-family:'Noto Sans KR',sans-serif;line-height:1}

.menu-section{padding:16px 0;flex:1}
.menu-label{font-size:11px;font-weight:700;color:#4a5568;text-transform:uppercase;letter-spacing:1px;padding:8px 20px}
.menu-item{display:flex;align-items:center;gap:12px;padding:14px 20px;color:#a0aec0;text-decoration:none;font-size:14px;font-weight:500;transition:all 0.2s;border-left:3px solid transparent}
.menu-item:hover{background:rgba(255,255,255,0.06);color:#fff}
.menu-item.active{background:rgba(102,126,234,0.2);color:#fff;border-left-color:#667eea}
.menu-icon{font-size:17px;width:22px;text-align:center}

/* ── 메인 ── */
.main{margin-left:230px;flex:1;padding:24px;min-width:0}
.topbar{background:white;border-radius:12px;padding:16px 24px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.topbar-title{font-size:21px;font-weight:700;color:#1a202c}
.topbar-sub{font-size:14px;color:#718096;font-weight:500}

/* ── 필터 ── */
.filter-bar{background:white;border-radius:12px;padding:16px 24px;margin-bottom:20px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.filter-group{display:flex;flex-direction:column;gap:5px}
.filter-label{font-size:12px;font-weight:700;color:#718096;text-transform:uppercase}
.filter-group select{padding:9px 16px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:14px;font-family:'Noto Sans KR',sans-serif;min-width:140px;background:#f8fafc;cursor:pointer}
.filter-group select:focus{outline:none;border-color:#667eea}

/* ── [수정2] 언어 토글 버튼 ── */
.lang-toggle{
  margin-left:auto;display:flex;align-items:center;gap:8px;
  background:#f1f5f9;border-radius:24px;padding:4px;border:1.5px solid #e2e8f0;
}
.lang-btn{
  padding:7px 16px;border-radius:20px;font-size:13px;font-weight:700;
  cursor:pointer;border:none;background:transparent;color:#718096;transition:all 0.25s;
}
.lang-btn.active{background:#667eea;color:#fff;box-shadow:0 2px 8px rgba(102,126,234,0.3)}

/* ── KPI 카드 ── */
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:20px}
.kpi-card{background:white;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-top:4px solid transparent}
.kpi-card.expand{border-top-color:#667eea}
.kpi-card.normal{border-top-color:#10b981}
.kpi-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}
.kpi-label{font-size:12px;font-weight:600;color:#718096}
.kpi-badge{font-size:11px;padding:3px 9px;border-radius:20px;font-weight:700}
.kpi-badge.expand{background:#ede9fe;color:#6d28d9}
.kpi-badge.normal{background:#d1fae5;color:#047857}
.kpi-value{font-size:25px;font-weight:700;color:#1a202c}
.kpi-unit{font-size:14px;color:#718096;font-weight:500;margin-left:3px}

/* ── 차트 그리드 ── */
.chart-grid{display:grid;gap:20px}
.chart-row-2{grid-template-columns:1fr 1fr}
.chart-row-3{grid-template-columns:2fr 1fr}
.chart-row-4{grid-template-columns:1fr}
.chart-row-invest{grid-template-columns:280px 1fr}

.chart-card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.chart-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.chart-title{font-size:15px;font-weight:700;color:#2d3748;display:flex;align-items:center;gap:8px}
.chart-title span.dot{width:9px;height:9px;border-radius:50%;display:inline-block}
.chart-wrap{position:relative;height:260px}
.chart-wrap.tall{height:300px}
.chart-wrap.pie{height:260px}
.chart-wrap.monthly{height:300px}
.chart-wrap.activity{height:360px}

/* ── [수정5] 투자유형별 Total 3D/shadow 효과 ── */
.invest-type-total-wrap{
  position:relative;border-right:2px dashed #e2e8f0;padding-right:8px;height:100%;
  background:linear-gradient(145deg,#f8fafc 0%,#eef1f6 100%);
  border-radius:12px;
  box-shadow:4px 4px 12px rgba(0,0,0,0.1), -2px -2px 8px rgba(255,255,255,0.8), inset 0 1px 0 rgba(255,255,255,0.6);
}
.invest-type-total-label{
  font-size:14px;font-weight:800;color:#1e293b;text-align:center;margin-bottom:6px;padding-top:4px;
  text-shadow:1px 1px 2px rgba(0,0,0,0.08);
  letter-spacing:1px;
}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>

<!-- 사이드바 -->
<div class="sidebar">
  <!-- [수정1] LG전자 로고 - 공식 스타일 -->
  <div class="logo-wrap">
    <div class="logo-circle">
      <span class="logo-circle-letter">LG</span>
    </div>
    <div class="logo-text-group">
      <span class="logo-text-lg">LG</span>
      <span class="logo-text-sub">전자</span>
    </div>
  </div>
  <div class="menu-section">
    <div class="menu-label"><span class="i18n" data-ko="메뉴" data-en="Menu">메뉴</span></div>
    <a href="/dashboard" class="menu-item active">
      <span class="menu-icon">🏠</span><span class="i18n" data-ko="대시보드" data-en="Dashboard">대시보드</span>
    </a>
    <a href="/list" class="menu-item">
      <span class="menu-icon">📋</span><span class="i18n" data-ko="투자실적 조회" data-en="View Records">투자실적 조회</span>
    </a>
    <a href="/" class="menu-item">
      <span class="menu-icon">✏️</span><span class="i18n" data-ko="Data 입력" data-en="Data Entry">Data 입력</span>
    </a>
  </div>
</div>

<!-- 메인 콘텐츠 -->
<div class="main">
  <div class="topbar">
    <div class="topbar-title">📊 <span class="i18n" data-ko="'26년 설비 투자비 한계돌파 현황" data-en="'26 Facility Investment Breakthrough Status">'26년 설비 투자비 한계돌파 현황</span></div>
    <div class="topbar-sub"><span class="i18n" data-ko="창원생산기술실" data-en="Changwon Production Tech.">창원생산기술실</span></div>
  </div>

  <!-- 필터 [수정6] 투자목적 추가 + [수정2] 언어 토글 -->
  <div class="filter-bar">
    <div class="filter-group">
      <div class="filter-label"><span class="i18n" data-ko="제품" data-en="Product">제품</span></div>
      <select id="fProduct" onchange="onProductChange()">
        <option value=""><span class="i18n-opt" data-ko="전체" data-en="All">전체</span></option>
        <option>키친</option><option>빌트인쿠킹</option><option>리빙</option><option>부품</option><option>ES</option>
      </select>
    </div>
    <div class="filter-group">
      <div class="filter-label"><span class="i18n" data-ko="법인" data-en="Corp.">법인</span></div>
      <select id="fCorp" onchange="applyFilter()">
        <option value="">전체</option>
      </select>
    </div>
    <div class="filter-group">
      <div class="filter-label"><span class="i18n" data-ko="투자유형" data-en="Type">투자유형</span></div>
      <select id="fType" onchange="applyFilter()">
        <option value="">전체</option>
        <option>확장</option><option>경상</option>
      </select>
    </div>
    <div class="filter-group">
      <div class="filter-label"><span class="i18n" data-ko="투자목적" data-en="Purpose">투자목적</span></div>
      <select id="fPurpose" onchange="applyFilter()">
        <option value="">전체</option>
      </select>
    </div>
    <!-- [수정2] 한/영 토글 -->
    <div class="lang-toggle">
      <button class="lang-btn active" id="langKo" onclick="setLang('ko')">🇰🇷 한글</button>
      <button class="lang-btn" id="langEn" onclick="setLang('en')">🇺🇸 ENG</button>
    </div>
  </div>

  <!-- KPI 카드 6개 [수정4] 라벨 변경: '확장투자 건수' → '건수', 배지: '확장' → '확장 투자' -->
  <div class="kpi-grid">
    <div class="kpi-card expand">
      <div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="건수" data-en="Count">건수</span></div><div class="kpi-badge expand"><span class="i18n" data-ko="확장 투자" data-en="Expansion">확장 투자</span></div></div>
      <div><span class="kpi-value" id="kExpCnt">0</span><span class="kpi-unit"><span class="i18n" data-ko="건" data-en="cases">건</span></span></div>
    </div>
    <div class="kpi-card expand">
      <div class="kpi-top"><div class="kpi-label">Base</div><div class="kpi-badge expand"><span class="i18n" data-ko="확장 투자" data-en="Expansion">확장 투자</span></div></div>
      <div><span class="kpi-value" id="kExpBase">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div>
    </div>
    <div class="kpi-card expand">
      <div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="절감실적" data-en="Savings">절감실적</span></div><div class="kpi-badge expand"><span class="i18n" data-ko="확장 투자" data-en="Expansion">확장 투자</span></div></div>
      <div><span class="kpi-value" id="kExpSave">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div>
    </div>
    <div class="kpi-card normal">
      <div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="건수" data-en="Count">건수</span></div><div class="kpi-badge normal"><span class="i18n" data-ko="경상 투자" data-en="Recurring">경상 투자</span></div></div>
      <div><span class="kpi-value" id="kNorCnt">0</span><span class="kpi-unit"><span class="i18n" data-ko="건" data-en="cases">건</span></span></div>
    </div>
    <div class="kpi-card normal">
      <div class="kpi-top"><div class="kpi-label">Base</div><div class="kpi-badge normal"><span class="i18n" data-ko="경상 투자" data-en="Recurring">경상 투자</span></div></div>
      <div><span class="kpi-value" id="kNorBase">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div>
    </div>
    <div class="kpi-card normal">
      <div class="kpi-top"><div class="kpi-label"><span class="i18n" data-ko="절감실적" data-en="Savings">절감실적</span></div><div class="kpi-badge normal"><span class="i18n" data-ko="경상 투자" data-en="Recurring">경상 투자</span></div></div>
      <div><span class="kpi-value" id="kNorSave">0</span><span class="kpi-unit"><span class="i18n" data-ko="억원" data-en="100M">억원</span></span></div>
    </div>
  </div>

  <!-- 차트 행 1: Base 대비 절감 + 제품별 Base 대비 절감 -->
  <div class="chart-grid chart-row-2" style="margin-bottom:20px">
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title"><span style="font-size:17px;margin-right:2px">💰</span><span class="i18n" data-ko="전체 Base 대비 절감 실적" data-en="Total Base vs Savings">전체 Base 대비 절감 실적</span></div>
      </div>
      <div class="chart-wrap"><canvas id="cBaseTotal"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title"><span style="font-size:17px;margin-right:2px">📦</span><span class="i18n" data-ko="제품별 Base 대비 절감 실적" data-en="Product Base vs Savings">제품별 Base 대비 절감 실적</span></div>
      </div>
      <div class="chart-wrap"><canvas id="cBaseProduct"></canvas></div>
    </div>
  </div>

  <!-- 차트 행 2: 투자유형별 절감실적 -->
  <div class="chart-grid chart-row-4" style="margin-bottom:20px">
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title"><span style="font-size:17px;margin-right:2px">📊</span><span class="i18n" data-ko="투자유형별 절감 실적" data-en="Savings by Investment Type">투자유형별 절감 실적</span></div>
      </div>
      <div style="display:grid;grid-template-columns:240px 1fr;gap:0;height:320px;align-items:stretch">
        <!-- [수정5] 왼쪽: Total - 그림자/3D 효과 적용 -->
        <div class="invest-type-total-wrap">
          <div class="invest-type-total-label">Total</div>
          <div style="position:relative;height:calc(100% - 30px)">
            <canvas id="cInvestTypeTotal"></canvas>
          </div>
        </div>
        <!-- 오른쪽: 제품별 -->
        <div style="position:relative;padding-left:8px;height:100%">
          <div style="position:relative;height:100%">
            <canvas id="cInvestTypeProduct"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 차트 행 3: 절감활동 + 파이차트 -->
  <div class="chart-grid chart-row-3" style="margin-bottom:20px">
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title"><span style="font-size:17px;margin-right:2px">🔧</span><span class="i18n" data-ko="절감 활동별 절감 실적" data-en="Savings by Activity">절감 활동별 절감 실적</span></div>
      </div>
      <div class="chart-wrap activity"><canvas id="cActivity"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title"><span style="font-size:17px;margin-right:2px">🥧</span><span class="i18n" data-ko="제품별 절감 실적" data-en="Savings by Product">제품별 절감 실적</span></div>
      </div>
      <div class="chart-wrap pie"><canvas id="cPie"></canvas></div>
    </div>
  </div>

  <!-- 차트 행 4: 법인별 -->
  <div class="chart-grid chart-row-4" style="margin-bottom:20px">
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title"><span style="font-size:17px;margin-right:2px">🌍</span><span class="i18n" data-ko="법인별 절감 목표 및 실적" data-en="Corp. Savings Target vs Actual">법인별 절감 목표 및 실적</span></div>
      </div>
      <div class="chart-wrap tall"><canvas id="cCorp"></canvas></div>
    </div>
  </div>

  <!-- 차트 행 5: 월별 절감 실적 -->
  <div class="chart-grid chart-row-4" style="margin-bottom:20px">
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title"><span style="font-size:17px;margin-right:2px">📅</span><span class="i18n" data-ko="월별 절감 실적 (2026년)" data-en="Monthly Savings (2026)">월별 절감 실적 (2026년)</span></div>
      </div>
      <div class="chart-wrap monthly"><canvas id="cMonthly"></canvas></div>
    </div>
  </div>
</div>

<script>
const ALL_DATA = {{ processed_json | safe }};
const CORPS_MAP = {{ corporations_json | safe }};
const MONTHLY_DATA = {{ monthly_json | safe }};
const ALL_PURPOSES = {{ all_purposes_json | safe }};
const PRODUCTS = ['키친','빌트인쿠킹','리빙','부품','ES'];

const ALL_CORPS_ORDERED = (function(){
  const all = new Set();
  Object.values(CORPS_MAP).forEach(arr => arr.forEach(c => all.add(c)));
  const others = [...all].filter(c => c !== 'KR').sort();
  return ['KR', ...others];
})();

Chart.defaults.font.family = "'Noto Sans KR', sans-serif";
Chart.defaults.font.size = 13;

let filtered = [...ALL_DATA];
let charts = {};

/* ── [수정2] 언어 전환 ── */
function setLang(lang){
  localStorage.setItem('app_lang', lang);
  document.getElementById('langKo').classList.toggle('active', lang==='ko');
  document.getElementById('langEn').classList.toggle('active', lang==='en');
  applyLang();
}
function applyLang(){
  const lang = localStorage.getItem('app_lang') || 'ko';
  document.getElementById('langKo').classList.toggle('active', lang==='ko');
  document.getElementById('langEn').classList.toggle('active', lang==='en');
  document.querySelectorAll('.i18n').forEach(el=>{
    const txt = el.getAttribute('data-'+lang);
    if(txt) el.innerHTML = txt.replace(/\n/g,'<br>');
  });
}

/* ── [수정6] 투자목적 필터 초기화 ── */
function initPurposeFilter(){
  const sel = document.getElementById('fPurpose');
  sel.innerHTML = '<option value="">전체</option>';
  ALL_PURPOSES.forEach(p=>{
    const o = document.createElement('option');
    o.value = o.textContent = p;
    sel.appendChild(o);
  });
}

/* ── 법인 필터 초기화 ── */
function initCorpFilter(product){
  const sel = document.getElementById('fCorp');
  const cur = sel.value;
  sel.innerHTML = '<option value="">전체</option>';
  let corps;
  if(product && CORPS_MAP[product]){
    corps = CORPS_MAP[product];
  } else {
    corps = ALL_CORPS_ORDERED;
  }
  corps.forEach(c => {
    const o = document.createElement('option');
    o.value = o.textContent = c;
    sel.appendChild(o);
  });
  if([...sel.options].some(o=>o.value===cur)) sel.value = cur;
}

function onProductChange(){
  initCorpFilter(document.getElementById('fProduct').value);
  applyFilter();
}

function applyFilter(){
  const p = document.getElementById('fProduct').value;
  const c = document.getElementById('fCorp').value;
  const t = document.getElementById('fType').value;
  const pu = document.getElementById('fPurpose').value;
  filtered = ALL_DATA.filter(r =>
    (!p || r[2]===p) && (!c || r[3]===c) && (!t || r[1]===t) && (!pu || r[4]===pu)
  );
  renderAll();
}

function sum(arr, idx){ return arr.reduce((s,r)=>s+(parseFloat(r[idx])||0),0); }

/* ── KPI ── */
function updateKPI(){
  const exp = filtered.filter(r=>r[1]==='확장');
  const nor = filtered.filter(r=>r[1]==='경상');
  document.getElementById('kExpCnt').textContent  = exp.length;
  document.getElementById('kExpBase').textContent = sum(exp,13).toFixed(1);
  document.getElementById('kExpSave').textContent = sum(exp,17).toFixed(1);
  document.getElementById('kNorCnt').textContent  = nor.length;
  document.getElementById('kNorBase').textContent = sum(nor,13).toFixed(1);
  document.getElementById('kNorSave').textContent = sum(nor,17).toFixed(1);
}

const PALETTE = {
  gray:'rgba(180,180,180,0.85)',   grayL:'rgba(180,180,180,0.4)',
  red:'rgba(180,30,30,0.85)',      redL:'rgba(220,80,80,0.4)',
  purple:'rgba(102,126,234,0.85)',
  green:'rgba(16,185,129,0.85)',
  amber:'rgba(245,158,11,0.85)',
  blue:'rgba(59,130,246,0.85)',    blueL:'rgba(59,130,246,0.3)',
  teal:'rgba(20,184,166,0.85)',
  violet:'rgba(139,92,246,0.85)',
  pink:'rgba(236,72,153,0.85)',
  orange:'rgba(249,115,22,0.85)',
};

function mk(id, cfg){
  if(charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), cfg);
}

const barLabelPlugin = {
  id:'barLabel',
  afterDatasetsDraw(chart){
    const {ctx} = chart;
    chart.data.datasets.forEach((ds, di)=>{
      const meta = chart.getDatasetMeta(di);
      if(meta.hidden) return;
      meta.data.forEach((bar, idx)=>{
        const val = ds.data[idx];
        if(!val || val <= 0) return;
        const txt = parseFloat(val).toFixed(1);
        ctx.save();
        ctx.font = '600 12px "Noto Sans KR",sans-serif';
        ctx.fillStyle = '#374151';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        const isHorizontal = chart.config.options?.indexAxis === 'y';
        if(isHorizontal){
          ctx.textAlign = 'left';
          ctx.textBaseline = 'middle';
          ctx.fillText(txt, bar.x + 4, bar.y);
        } else {
          ctx.fillText(txt, bar.x, bar.y - 4);
        }
        ctx.restore();
      });
    });
  }
};
Chart.register(barLabelPlugin);

/* [수정3] 범례-그래프 간격 넓힘: legend padding 추가 */
/* 1. 전체 Base 대비 절감 */
function chart_BaseTotal(){
  const totalBase = sum(filtered,13);
  const totalSave = sum(filtered,17);
  mk('cBaseTotal',{
    type:'bar',
    data:{
      labels:['전체'],
      datasets:[
        {label:'Base 금액',data:[totalBase],backgroundColor:PALETTE.purple,borderRadius:6},
        {label:'절감 실적',data:[totalSave],backgroundColor:PALETTE.green,borderRadius:6}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,
      layout:{padding:{top:20}},
      plugins:{legend:{position:'top',labels:{font:{size:13},padding:18}},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw.toFixed(2)}억원`}}},
      scales:{y:{beginAtZero:true,title:{display:true,text:'억원',font:{size:13}},
        ticks:{font:{size:12}}}}}
  });
}

/* 2. 제품별 Base 대비 절감 */
function chart_BaseProduct(){
  const baseArr = PRODUCTS.map(p=>sum(filtered.filter(r=>r[2]===p),13));
  const saveArr = PRODUCTS.map(p=>sum(filtered.filter(r=>r[2]===p),17));
  mk('cBaseProduct',{
    type:'bar',
    data:{
      labels:PRODUCTS,
      datasets:[
        {label:'Base 금액',data:baseArr,backgroundColor:PALETTE.purple,borderRadius:5},
        {label:'절감 실적',data:saveArr,backgroundColor:PALETTE.green,borderRadius:5}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,
      layout:{padding:{top:20}},
      plugins:{legend:{position:'top',labels:{font:{size:13},padding:18}},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw.toFixed(2)}억원`}}},
      scales:{y:{beginAtZero:true,title:{display:true,text:'억원',font:{size:13}},
        ticks:{font:{size:12}}}}}
  });
}

/* 3. 투자유형별 — Total(왼쪽) */
function chart_InvestTypeTotal(){
  const expTgt = sum(filtered.filter(r=>r[1]==='확장'),16);
  const expAct = sum(filtered.filter(r=>r[1]==='확장'),17);
  const norTgt = sum(filtered.filter(r=>r[1]==='경상'),16);
  const norAct = sum(filtered.filter(r=>r[1]==='경상'),17);
  mk('cInvestTypeTotal',{
    type:'bar',
    data:{
      labels:['확장','경상'],
      datasets:[
        {label:'절감 목표',data:[expTgt,norTgt],backgroundColor:PALETTE.grayL,borderColor:PALETTE.gray,borderWidth:2,borderRadius:4},
        {label:'절감 실적',data:[expAct,norAct],backgroundColor:PALETTE.red,borderRadius:4}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw.toFixed(2)}억원`}}},
      scales:{
        x:{ticks:{font:{size:13},color:'#374151'}},
        y:{beginAtZero:true,
          max: Math.ceil(Math.max(expTgt,expAct,norTgt,norAct)*1.25) || 10,
          ticks:{font:{size:11}},
          title:{display:true,text:'억원',font:{size:12}}}
      }}
  });
}

/* 3. 투자유형별 — 제품별(오른쪽) */
function chart_InvestTypeProduct(){
  const groupLabels = PRODUCTS;
  const expTgtArr=[], expActArr=[], norTgtArr=[], norActArr=[];
  PRODUCTS.forEach(p=>{
    const expRows = filtered.filter(r=>r[2]===p && r[1]==='확장');
    const norRows = filtered.filter(r=>r[2]===p && r[1]==='경상');
    expTgtArr.push(sum(expRows,16));
    expActArr.push(sum(expRows,17));
    norTgtArr.push(sum(norRows,16));
    norActArr.push(sum(norRows,17));
  });
  mk('cInvestTypeProduct',{
    type:'bar',
    data:{
      labels: groupLabels,
      datasets:[
        {label:'확장 목표',data:expTgtArr,backgroundColor:PALETTE.grayL,borderColor:PALETTE.gray,borderWidth:2,borderRadius:3},
        {label:'확장 실적',data:expActArr,backgroundColor:PALETTE.red,borderRadius:3},
        {label:'경상 목표',data:norTgtArr,backgroundColor:'rgba(160,160,160,0.25)',borderColor:'rgba(160,160,160,0.7)',borderWidth:2,borderRadius:3},
        {label:'경상 실적',data:norActArr,backgroundColor:'rgba(180,30,30,0.5)',borderRadius:3}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:'top',labels:{font:{size:12},boxWidth:12,padding:8}},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw.toFixed(2)}억원`}}
      },
      scales:{
        x:{ticks:{font:{size:13},color:'#374151'}},
        y:{beginAtZero:true,
          max: Math.ceil(Math.max(...expTgtArr,...expActArr,...norTgtArr,...norActArr)*1.25) || 10,
          ticks:{font:{size:11}},
          title:{display:true,text:'억원',font:{size:13}}}
      }}
  });
}

/* 4. 절감 활동별 */
function chart_Activity(){
  const actLabels=['합계','①신기술신공법','②염가형부품','③중국/Local설비','④중국/한국Collabo','⑤컨테이너최소화','⑥출장최소화','⑦유휴설비','⑧사양최적화','⑨기타'];
  const totalSave = sum(filtered,17);
  const actData = [18,19,20,21,22,23,24,25,26].map(i=>sum(filtered,i));
  const colors=[PALETTE.orange,PALETTE.amber,PALETTE.green,PALETTE.teal,PALETTE.blue,PALETTE.violet,PALETTE.pink,PALETTE.purple,PALETTE.red];
  mk('cActivity',{
    type:'bar',
    data:{
      labels:actLabels,
      datasets:[{
        label:'절감 실적(억원)',
        data:[totalSave,...actData],
        backgroundColor:[PALETTE.purple,...colors],
        borderRadius:5
      }]
    },
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.raw.toFixed(2)}억원`}}},
      scales:{
        x:{beginAtZero:true,title:{display:true,text:'억원',font:{size:13}},ticks:{font:{size:12}}},
        y:{ticks:{font:{size:13},padding:6}}
      }}
  });
}

/* 5. 제품별 파이차트 */
function chart_Pie(){
  const pieData = PRODUCTS.map(p=>sum(filtered.filter(r=>r[2]===p),17));
  const pieColors=[PALETTE.purple,PALETTE.amber,PALETTE.green,PALETTE.blue,PALETTE.red];
  mk('cPie',{
    type:'doughnut',
    data:{labels:PRODUCTS,datasets:[{data:pieData,backgroundColor:pieColors,borderWidth:2,borderColor:'#fff'}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:13,padding:12,font:{size:13}}},
        tooltip:{callbacks:{label:c=>`${c.label}: ${c.raw.toFixed(2)}억원`}}}}
  });
}

/* 6. 법인별 */
function chart_Corp(){
  const corpTgt={}, corpAct={};
  ALL_CORPS_ORDERED.forEach(c=>{corpTgt[c]=0; corpAct[c]=0;});
  filtered.forEach(r=>{
    const c=r[3]; if(!c) return;
    if(corpTgt[c]!==undefined){
      corpTgt[c] += parseFloat(r[16])||0;
      corpAct[c] += parseFloat(r[17])||0;
    }
  });
  mk('cCorp',{
    type:'bar',
    data:{
      labels:ALL_CORPS_ORDERED,
      datasets:[
        {label:'절감 목표',data:ALL_CORPS_ORDERED.map(c=>corpTgt[c]),backgroundColor:PALETTE.blueL,borderColor:PALETTE.blue,borderWidth:2,borderRadius:4},
        {label:'절감 실적',data:ALL_CORPS_ORDERED.map(c=>corpAct[c]),backgroundColor:PALETTE.green,borderRadius:4}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'top',labels:{font:{size:13}}},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw.toFixed(2)}억원`}}},
      scales:{
        x:{ticks:{font:{size:12}}},
        y:{beginAtZero:true,title:{display:true,text:'억원',font:{size:13}},ticks:{font:{size:12}}}
      }}
  });
}

/* 7. 월별 절감 실적 */
function chart_Monthly(){
  const labels = MONTHLY_DATA.labels;
  const tgt = MONTHLY_DATA.target;
  const act = MONTHLY_DATA.actual;
  const cumTgt=[], cumAct=[];
  let st=0, sa=0;
  for(let i=0;i<12;i++){
    st += tgt[i]; cumTgt.push(parseFloat(st.toFixed(2)));
    sa += act[i]; cumAct.push(parseFloat(sa.toFixed(2)));
  }
  const maxBar = Math.max(...tgt, ...act, 1);
  const maxCum = Math.max(...cumTgt, ...cumAct, 1);
  mk('cMonthly',{
    type:'bar',
    data:{
      labels,
      datasets:[
        {type:'bar', label:'절감 목표', data:tgt, order:1,
          backgroundColor:PALETTE.grayL, borderColor:PALETTE.gray,
          borderWidth:2, borderRadius:4, yAxisID:'y'},
        {type:'bar', label:'절감 실적', data:act, order:2,
          backgroundColor:PALETTE.red, borderRadius:4, yAxisID:'y'},
        {type:'line', label:'누적(목표)', data:cumTgt, order:3,
          borderColor:'rgba(130,130,130,0.95)', backgroundColor:'transparent',
          borderDash:[6,3], borderWidth:2,
          pointStyle:'circle', pointRadius:5,
          pointBackgroundColor:'white', pointBorderColor:'rgba(130,130,130,0.95)',
          pointBorderWidth:2, tension:0.1, yAxisID:'y2'},
        {type:'line', label:'누적(실적)', data:cumAct, order:4,
          borderColor:PALETTE.red, backgroundColor:'transparent',
          borderWidth:2.5,
          pointStyle:'circle', pointRadius:5,
          pointBackgroundColor:'white', pointBorderColor:PALETTE.red,
          pointBorderWidth:2, tension:0.1, yAxisID:'y2'}
      ]
    },
    options:{responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{
          position:'top',
          align:'center',
          labels:{font:{size:13}, boxWidth:14, padding:20}
        },
        tooltip:{mode:'index', intersect:false,
          callbacks:{label:c=>`${c.dataset.label}: ${(c.raw||0).toFixed(2)}억원`}}
      },
      scales:{
        x:{ticks:{font:{size:13}}},
        y:{beginAtZero:true, position:'left',
          max: Math.ceil(maxBar * 3),
          title:{display:true, text:'월별(억원)', font:{size:12}},
          ticks:{font:{size:11}}},
        y2:{beginAtZero:true, position:'right',
          max: Math.ceil(maxCum * 1.3),
          title:{display:true, text:'누적(억원)', font:{size:12}},
          ticks:{font:{size:11}},
          grid:{drawOnChartArea:false}}
      }}
  });
}

function renderAll(){
  updateKPI();
  chart_BaseTotal();
  chart_BaseProduct();
  chart_InvestTypeTotal();
  chart_InvestTypeProduct();
  chart_Activity();
  chart_Pie();
  chart_Corp();
  chart_Monthly();
}

window.onload = function(){
  initCorpFilter('');
  initPurposeFilter();
  applyLang();
  renderAll();
};
</script>
</body>
</html>"""

LIST_TPL = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>설비 투자비 활동 실적 조회</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Noto Sans KR','Malgun Gothic',sans-serif;font-size:13px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#333;padding:16px}
.top-header{background:linear-gradient(135deg,#4a5f9d 0%,#5a4a8a 100%);padding:18px 28px;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.15);margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.top-header h2{font-size:22px;font-weight:700;color:#fff;display:flex;align-items:center;gap:10px}
.top-header-right{display:flex;gap:12px;align-items:center}
.top-header a,.excel-btn{background:rgba(255,255,255,0.2);color:#fff;padding:10px 20px;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px;transition:all 0.3s;border:1px solid rgba(255,255,255,0.3);cursor:pointer;display:flex;align-items:center;gap:6px}
.top-header a:hover,.excel-btn:hover{background:rgba(255,255,255,0.3);transform:translateY(-2px)}
.filter-bar{background:rgba(255,255,255,0.98);border-radius:12px;padding:16px 24px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin-bottom:16px;box-shadow:0 4px 16px rgba(0,0,0,0.08)}
.filter-bar label{font-weight:600;color:#667eea;font-size:14px}
.filter-bar select{padding:8px 32px 8px 12px;border:2px solid #e2e8f0;border-radius:8px;font-size:14px;background:#f8fafc;cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23667eea' d='M6 9L1 4h10z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center}
.filter-bar select:focus{border-color:#667eea;outline:none}
.legend{margin-left:auto;display:flex;gap:16px;align-items:center;font-size:13px}
.legend-item{display:flex;align-items:center;gap:6px;color:#64748b;font-weight:500}
.sig{width:16px;height:16px;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.2);display:inline-block}
.s-g{background:radial-gradient(circle at 40% 35%, #34d399, #059669);box-shadow:0 0 6px rgba(16,185,129,0.5)}
.s-y{background:radial-gradient(circle at 40% 35%, #fcd34d, #f59e0b);box-shadow:0 0 6px rgba(245,158,11,0.5)}
.s-x{background:radial-gradient(circle at 40% 35%, #d1d5db, #94a3b8);box-shadow:0 0 4px rgba(148,163,184,0.3)}
.table-container{background:rgba(255,255,255,0.98);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.12);overflow:hidden}
.table-wrap{overflow-x:auto;overflow-y:auto;max-height:calc(100vh - 220px)}
table{border-collapse:collapse;white-space:nowrap;min-width:100%;background:#fff}
thead th{position:sticky;top:0;z-index:10;background:#667eea;color:#fff;font-weight:600;font-size:12px;padding:11px 9px;border:1px solid #94a3b8;text-align:center}
thead tr.gh th{background:#5a67d8;font-size:13px;padding:9px;border:1px solid #94a3b8}
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
th.gs{background:#3b82f6;border:1px solid #94a3b8}
th.gv{background:#10b981;border:1px solid #94a3b8}
th.gr{background:#fbbf24;color:#78350f;border:1px solid #94a3b8}
th.ge{background:#8b5cf6;border:1px solid #94a3b8}
tr.gh .g-s{background:#2563eb;border:1px solid #94a3b8}
tr.gh .g-v{background:#059669;border:1px solid #94a3b8}
tr.gh .g-r{background:#f59e0b;border:1px solid #94a3b8}
tr.gh .g-e{background:#7c3aed;border:1px solid #94a3b8}
tr.gh .g-c{background:#5a67d8;border:1px solid #94a3b8}
.footer-info{padding:12px 24px;font-size:14px;color:#64748b;background:rgba(255,255,255,0.95);border-top:2px solid #e2e8f0;font-weight:600}
.row-actions{display:flex;gap:6px;align-items:center;justify-content:center}
.icon-btn{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;cursor:pointer;transition:all 0.3s;border:none;background:#fff;font-size:14px;text-decoration:none;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
.icon-edit{color:#3b82f6}.icon-edit:hover{background:#3b82f6;color:#fff;transform:scale(1.1)}
.icon-del{color:#ef4444}.icon-del:hover{background:#ef4444;color:#fff;transform:scale(1.1)}
/* 언어 토글 (리스트 페이지용) */
.lang-toggle-list{display:flex;align-items:center;gap:6px;background:rgba(255,255,255,0.2);border-radius:24px;padding:3px;border:1px solid rgba(255,255,255,0.3)}
.lang-btn-list{padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;cursor:pointer;border:none;background:transparent;color:rgba(255,255,255,0.7);transition:all 0.25s}
.lang-btn-list.active{background:rgba(255,255,255,0.95);color:#667eea;box-shadow:0 2px 6px rgba(0,0,0,0.15)}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
</head>
<body>
<div class="top-header">
  <h2>📊 <span class="i18n" data-ko="설비 투자비 활동 실적 조회" data-en="Facility Investment Performance">설비 투자비 활동 실적 조회</span></h2>
  <div class="top-header-right">
    <div class="lang-toggle-list">
      <button class="lang-btn-list active" id="langKo2" onclick="setLang('ko')">🇰🇷 한글</button>
      <button class="lang-btn-list" id="langEn2" onclick="setLang('en')">🇺🇸 ENG</button>
    </div>
    <button class="excel-btn" onclick="downloadExcel()">📥 Excel</button>
    <a href="/dashboard">🏠 <span class="i18n" data-ko="대시보드" data-en="Dashboard">대시보드</span></a>
    <a href="/">◀ <span class="i18n" data-ko="입력 페이지" data-en="Data Entry">입력 페이지</span></a>
  </div>
</div>
<div class="filter-bar">
  <label><span class="i18n" data-ko="제품" data-en="Product">제품</span></label>
  <select id="fp" onchange="applyFilter();updateFilterCorps()">
    <option value="">전체</option>
    <option>키친</option><option>빌트인쿠킹</option><option>리빙</option><option>부품</option><option>ES</option>
  </select>
  <label><span class="i18n" data-ko="법인" data-en="Corp.">법인</span></label>
  <select id="fc" onchange="applyFilter()"><option value="">전체</option></select>
  <label><span class="i18n" data-ko="투자유형" data-en="Type">투자유형</span></label>
  <select id="ft" onchange="applyFilter()"><option value="">전체</option><option>확장</option><option>경상</option></select>
  <label><span class="i18n" data-ko="투자목적" data-en="Purpose">투자목적</span></label>
  <select id="fpu" onchange="applyFilter()"><option value="">전체</option></select>
  <div class="legend">
    <div class="legend-item"><span class="sig s-g"></span><span class="i18n" data-ko="목표 초과 (HS≥30% / ES≥50%)" data-en="Above Target">목표 초과 (HS≥30% / ES≥50%)</span></div>
    <div class="legend-item"><span class="sig s-y"></span><span class="i18n" data-ko="목표 미달" data-en="Below Target">목표 미달</span></div>
    <div class="legend-item"><span class="sig s-x"></span><span class="i18n" data-ko="미입력" data-en="No Data">미입력</span></div>
  </div>
</div>
<div class="table-container">
  <div class="table-wrap">
    <table id="mainTable">
      <thead>
        <tr class="gh">
          <th class="sc c0 g-c" colspan="6"><span class="i18n" data-ko="투자 분류" data-en="Classification">투자 분류</span></th>
          <th class="g-s" colspan="7">📅 <span class="i18n" data-ko="투자 주요 일정" data-en="Schedule">투자 주요 일정</span></th>
          <th class="g-v" colspan="4">💰 <span class="i18n" data-ko="투자절감" data-en="Savings">투자절감</span></th>
          <th class="g-r" colspan="11">📊 <span class="i18n" data-ko="절감 활동 및 실적" data-en="Reduction Activities">절감 활동 및 실적</span></th>
          <th class="g-e" colspan="3">🎯 <span class="i18n" data-ko="목표" data-en="Target">목표</span></th>
        </tr>
        <tr>
          <th class="sc c0"><span class="i18n" data-ko="수정/삭제" data-en="Edit/Del">수정/<br>삭제</span></th>
          <th class="sc c1"><span class="i18n" data-ko="제품" data-en="Product">제품</span></th>
          <th class="sc c2"><span class="i18n" data-ko="법인" data-en="Corp.">법인</span></th>
          <th class="sc c3"><span class="i18n" data-ko="투자유형" data-en="Type">투자<br>유형</span></th>
          <th class="sc c4"><span class="i18n" data-ko="투자항목" data-en="Item">투자항목</span></th>
          <th class="sc c5"><span class="i18n" data-ko="투자목적" data-en="Purpose">투자목적</span></th>
          <th class="gs"><span class="i18n" data-ko="발주목표" data-en="Order Tgt">발주목표</span></th>
          <th class="gs"><span class="i18n" data-ko="발주실적" data-en="Order Act">발주실적</span></th>
          <th class="gs"><span class="i18n" data-ko="셋업목표" data-en="Setup Tgt">셋업목표</span></th>
          <th class="gs"><span class="i18n" data-ko="셋업실적" data-en="Setup Act">셋업실적</span></th>
          <th class="gs"><span class="i18n" data-ko="양산목표" data-en="Mass Tgt">양산목표</span></th>
          <th class="gs"><span class="i18n" data-ko="양산실적" data-en="Mass Act">양산실적</span></th>
          <th class="gs"><span class="i18n" data-ko="연기사유" data-en="Delay">연기사유</span></th>
          <th class="gv">Base</th>
          <th class="gv"><span class="i18n" data-ko="발주가 목표" data-en="Order P. Tgt">발주가<br>목표</span></th>
          <th class="gv"><span class="i18n" data-ko="발주가 실적" data-en="Order P. Act">발주가<br>실적</span></th>
          <th class="gv"><span class="i18n" data-ko="절감 목표" data-en="Save Tgt">절감<br>목표</span></th>
          <th class="gr"><span class="i18n" data-ko="절감 실적" data-en="Save Act">절감<br>실적</span></th>
          <th class="gr">①</th><th class="gr">②</th><th class="gr">③</th><th class="gr">④</th>
          <th class="gr">⑤</th><th class="gr">⑥</th><th class="gr">⑦</th><th class="gr">⑧</th>
          <th class="gr">⑨</th>
          <th class="gr"><span class="i18n" data-ko="활동내용" data-en="Activity">활동내용</span></th>
          <th class="ge"><span class="i18n" data-ko="절감률 목표(%)" data-en="Rate Tgt(%)">절감률<br>목표(%)</span></th>
          <th class="ge"><span class="i18n" data-ko="절감률 실적(%)" data-en="Rate Act(%)">절감률<br>실적(%)</span></th>
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
function f(v){return(v!=null&&v!=="")? v:"-";}
function deleteRow(id){
  if(!confirm("정말 삭제하시겠습니까?")) return;
  fetch("/delete/"+id,{method:"POST"}).then(r=>r.json()).then(d=>{if(d.success)location.reload();});
}
function updateFilterCorps(){
  const p=document.getElementById('fp').value;
  const s=document.getElementById('fc');
  let corps=[];
  if(p&&CORPORATIONS[p]) corps=CORPORATIONS[p];
  else{const all=new Set();Object.values(CORPORATIONS).forEach(a=>a.forEach(c=>all.add(c)));corps=[...all].sort();}
  const cur=s.value;
  s.innerHTML='<option value="">전체</option>';
  corps.forEach(c=>{const o=document.createElement('option');o.value=o.textContent=c;s.appendChild(o);});
  if(corps.includes(cur)) s.value=cur;
}

/* [수정7] Signal 신호등 로직 수정 */
function renderTable(data){
  const tb=document.getElementById("tableBody"),tf=document.getElementById("tableFoot");
  let out="",tot={base:0,opt:0,opa:0,sgt:0,sga:0,r:[0,0,0,0,0,0,0,0,0]};
  data.forEach(r=>{
    const rid=r[0],prod=r[2]||"";
    let h="<tr>";
    h+="<td class='sc c0'><div class='row-actions'><a href='/edit/"+rid+"' class='icon-btn icon-edit'>✏️</a><button class='icon-btn icon-del' onclick='deleteRow("+rid+")'>🗑️</button></div></td>";
    h+="<td class='sc c1'>"+f(r[2])+"</td><td class='sc c2'>"+f(r[3])+"</td>";
    h+="<td class='sc c3'>"+f(r[1])+"</td><td class='sc c4 left'>"+f(r[5])+"</td><td class='sc c5'>"+f(r[4])+"</td>";
    h+="<td>"+f(r[6])+"</td><td>"+f(r[7])+"</td><td>"+f(r[8])+"</td><td>"+f(r[9])+"</td>";
    h+="<td>"+f(r[10])+"</td><td>"+f(r[11])+"</td><td class='left'>"+f(r[12])+"</td>";
    const base=parseFloat(r[13])||0,opt=parseFloat(r[14])||0,opa=parseFloat(r[15])||0;
    const sgt=parseFloat(r[16])||0,sga=parseFloat(r[17])||0;
    tot.base+=base;tot.opt+=opt;tot.opa+=opa;tot.sgt+=sgt;tot.sga+=sga;
    h+="<td>"+f(r[13])+"</td><td>"+f(r[14])+"</td><td>"+f(r[15])+"</td><td>"+f(r[16])+"</td><td>"+f(r[17])+"</td>";
    for(let i=18;i<=26;i++){tot.r[i-18]+=(parseFloat(r[i])||0);h+="<td>"+f(r[i])+"</td>";}
    h+="<td class='act-cell'>"+f(r[28])+"</td>";

    /* [수정7] 절감률 목표/실적 및 Signal 신호등 */
    const rTgt=(prod==="ES")?50:30;
    let rAct="-",rActNum=null;
    if(base>0 && sga>0){
      rActNum=(sga/base)*100;
      rAct=rActNum.toFixed(1);
    } else if(base>0 && sga===0){
      rActNum=0;
      rAct="0";
    }
    // else: base가 0이거나 미입력 → rActNum = null (미입력)

    let sig="s-x"; // 기본: 회색 (미입력)
    if(rActNum !== null){
      // 실적이 있음 (0 포함)
      if(rActNum >= rTgt){
        sig = "s-g"; // 초록: 목표 이상
      } else {
        sig = "s-y"; // 주황: 목표 미달
      }
    }

    h+="<td>"+rTgt+"%</td><td>"+(rAct!=="-"?rAct+"%":"-")+"</td>";
    h+="<td style='text-align:center'><span class='sig "+sig+"' style='display:inline-block'></span></td></tr>";
    out+=h;
  });
  tb.innerHTML=out;
  let foot="<tr><td colspan='6' style='text-align:center;background:#fef9c3'>합 계</td>";
  foot+="<td colspan='7' style='background:#fef9c3'></td>";
  foot+="<td>"+tot.base.toFixed(2)+"</td><td>"+tot.opt.toFixed(2)+"</td><td>"+tot.opa.toFixed(2)+"</td><td>"+tot.sgt.toFixed(2)+"</td><td>"+tot.sga.toFixed(2)+"</td>";
  tot.r.forEach(v=>{foot+="<td>"+v.toFixed(2)+"</td>";});
  foot+="<td colspan='4' style='background:#fef9c3'></td></tr>";
  tf.innerHTML=foot;
  document.getElementById("footerInfo").textContent="총 "+data.length+"건";
}
function applyFilter(){
  const fp=document.getElementById("fp").value,fc=document.getElementById("fc").value;
  const ft=document.getElementById("ft").value,fpu=document.getElementById("fpu").value;
  renderTable(DATA.filter(r=>(!fp||r[2]===fp)&&(!fc||r[3]===fc)&&(!ft||r[1]===ft)&&(!fpu||r[4]===fpu)));
}
function downloadExcel(){
  const wb=XLSX.utils.book_new();
  const headers=[["제품","법인","투자유형","투자항목","투자목적","발주목표","발주실적","셋업목표","셋업실적","양산목표","양산실적","연기사유","Base","발주가목표","발주가실적","절감목표","절감실적","①신기술신공법","②염가형부품","③중국/Local","④중국/한국Collabo","⑤컨테이너최소화","⑥출장최소화","⑦유휴설비","⑧사양최적화","⑨기타","활동내용","절감률목표(%)","절감률실적(%)"]];
  const rows=DATA.map(r=>{
    const base=parseFloat(r[13])||0,sga=parseFloat(r[17])||0;
    const rTgt=(r[2]==="ES")?50:30;
    let rAct="-";if(base>0&&sga>0)rAct=((sga/base)*100).toFixed(1);else if(base>0)rAct="0";
    return[r[2],r[3],r[1],r[5],r[4],r[6],r[7],r[8],r[9],r[10],r[11],r[12],r[13],r[14],r[15],r[16],r[17],r[18],r[19],r[20],r[21],r[22],r[23],r[24],r[25],r[26],r[28],rTgt,rAct];
  });
  const ws=XLSX.utils.aoa_to_sheet([...headers,...rows]);
  XLSX.utils.book_append_sheet(wb,ws,"투자실적");
  XLSX.writeFile(wb,"설비투자비_활동실적_"+new Date().toISOString().slice(0,10)+".xlsx");
}

/* i18n */
function setLang(lang){
  localStorage.setItem('app_lang', lang);
  document.getElementById('langKo2').classList.toggle('active', lang==='ko');
  document.getElementById('langEn2').classList.toggle('active', lang==='en');
  applyLang();
}
function applyLang(){
  const lang = localStorage.getItem('app_lang') || 'ko';
  document.getElementById('langKo2').classList.toggle('active', lang==='ko');
  document.getElementById('langEn2').classList.toggle('active', lang==='en');
  document.querySelectorAll('.i18n').forEach(el=>{
    const txt = el.getAttribute('data-'+lang);
    if(txt) el.innerHTML = txt.replace(/\n/g,'<br>');
  });
}

window.onload=function(){
  updateFilterCorps();
  const ps=document.getElementById('fpu');
  ALL_PURPOSES.forEach(p=>{const o=document.createElement('option');o.value=o.textContent=p;ps.appendChild(o);});
  renderTable(DATA);
  applyLang();
}
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("🚀 서버 시작: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)