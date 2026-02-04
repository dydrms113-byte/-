from flask import Flask, request, redirect, url_for, render_template_string, jsonify
import os
import json
from datetime import datetime
from urllib.parse import urlparse

try:
    import psycopg2
except ImportError:
    psycopg2 = None

app = Flask(__name__)
import sqlite3

def get_db():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if psycopg2 is None:
            raise Exception("psycopg2가 설치되어 있지 않습니다")
        result = urlparse(database_url)
        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
            sslmode="require"
        )
        conn.paramstyle = 'format'
        return conn
    return sqlite3.connect(DB_NAME)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data.db")

def init_db():
    print(f"📁 DB 경로: {DB_NAME}")
    conn = get_db()
    c = conn.cursor()
    
    # PostgreSQL과 SQLite 구분
    if os.environ.get("DATABASE_URL"):
        # PostgreSQL
        c.execute("""
            CREATE TABLE IF NOT EXISTS investment (
                id SERIAL PRIMARY KEY,
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
                created_at TEXT
            )
        """)
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
    else:
        # SQLite
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
                created_at TEXT
            )
        """)
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

PRODUCTS = ["키친", "빌트인쿠킹", "리빙", "부품", "ES"]
CORPORATIONS = ["KR","AI","AT","AZ","EG","IL_N","IL_P","IN_T","MN","MX","MZ","PN","RA","SR","TA","TH","TN","TR","VH","WR"]
ALL_PURPOSES = ["신규라인", "자동화", "라인 개조", "Overhaul", "신모델 대응", "T/Time 향상", "고장 수리", "안전", "설비 이설", "노후 교체", "설비 개선", "기타"]
MONTHS = [f"{y}-{m:02d}" for y in [2026, 2027] for m in range(1, 13)]

def nz(v, default=0.0):
    if v is None or v == "":
        return default
    try:
        return float(v) if isinstance(default, float) else str(v)
    except:
        return default

@app.route("/")
@app.route("/edit/<row_id>")
def index(row_id=None):
    edit_data = None
    if row_id:
        conn = get_db()
        c = conn.cursor()
        if os.environ.get("DATABASE_URL"):
            c.execute("SELECT * FROM investment WHERE id = %s", (row_id,))
        else:
            c.execute("SELECT * FROM investment WHERE id = ?", (row_id,))
        edit_data = c.fetchone()
        conn.close()
        if not edit_data:
            return "데이터를 찾을 수 없습니다.", 404
    return render_template_string(INPUT_TPL, products=PRODUCTS, corporations=CORPORATIONS, all_purposes=ALL_PURPOSES, edit_data=edit_data, row_id=row_id)

@app.route("/save", methods=["POST"])
def save():
    try:
        f = request.form
        conn = get_db()
        c = conn.cursor()
        row_id = f.get("row_id")
        
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
        
        is_postgres = os.environ.get("DATABASE_URL") is not None
        
        if row_id:
            if is_postgres:
                c.execute("""
                    UPDATE investment SET
                        invest_type=%s,product=%s,corporation=%s,purpose=%s,invest_item=%s,
                        order_target=%s,order_actual=%s,setup_target=%s,setup_actual=%s,
                        mass_target=%s,mass_actual=%s,delay_reason=%s,
                        base_amount=%s,order_price_target=%s,order_price_actual=%s,
                        saving_target=%s,saving_actual=%s,
                        reduce_1=%s,reduce_2=%s,reduce_3=%s,reduce_4=%s,reduce_5=%s,
                        reduce_6=%s,reduce_7=%s,reduce_8=%s,reduce_9=%s,
                        saving_total=%s,activity=%s
                    WHERE id=%s
                """, values + (row_id,))
            else:
                c.execute("""
                    UPDATE investment SET
                        invest_type=?,product=?,corporation=?,purpose=?,invest_item=?,
                        order_target=?,order_actual=?,setup_target=?,setup_actual=?,
                        mass_target=?,mass_actual=?,delay_reason=?,
                        base_amount=?,order_price_target=?,order_price_actual=?,
                        saving_target=?,saving_actual=?,
                        reduce_1=?,reduce_2=?,reduce_3=?,reduce_4=?,reduce_5=?,
                        reduce_6=?,reduce_7=?,reduce_8=?,reduce_9=?,
                        saving_total=?,activity=?
                    WHERE id=?
                """, values + (row_id,))
            target_id = int(row_id)
        else:
            if is_postgres:
                c.execute("""
                    INSERT INTO investment (
                        invest_type, product, corporation, purpose, invest_item,
                        order_target, order_actual, setup_target, setup_actual,
                        mass_target, mass_actual, delay_reason,
                        base_amount, order_price_target, order_price_actual,
                        saving_target, saving_actual,
                        reduce_1, reduce_2, reduce_3, reduce_4, reduce_5,
                        reduce_6, reduce_7, reduce_8, reduce_9,
                        saving_total, activity, created_at
                    ) VALUES (
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,
                        %s,%s,%s,
                        %s,%s,
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s
                    ) RETURNING id
                """, values + (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
                target_id = c.fetchone()[0]
            else:
                c.execute("""
                    INSERT INTO investment (
                        invest_type, product, corporation, purpose, invest_item,
                        order_target, order_actual, setup_target, setup_actual,
                        mass_target, mass_actual, delay_reason,
                        base_amount, order_price_target, order_price_actual,
                        saving_target, saving_actual,
                        reduce_1, reduce_2, reduce_3, reduce_4, reduce_5,
                        reduce_6, reduce_7, reduce_8, reduce_9,
                        saving_total, activity, created_at
                    ) VALUES (
                        ?,?,?,?,?,
                        ?,?,?,?,
                        ?,?,?,
                        ?,?,?,
                        ?,?,
                        ?,?,?,?,?,
                        ?,?,?,?,
                        ?,?,?
                    )
                """, values + (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
                target_id = c.lastrowid
        
        # 월별 데이터 초기화
        if is_postgres:
            c.execute("DELETE FROM investment_monthly WHERE id=%s", (target_id,))
        else:
            c.execute("DELETE FROM investment_monthly WHERE id=?", (target_id,))
        
        for ym in MONTHS:
            if is_postgres:
                c.execute("""
                    INSERT INTO investment_monthly (id, year_month, monthly_target, monthly_actual)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (id, year_month) DO NOTHING
                """, (target_id, ym, 0, 0))
            else:
                c.execute("""
                    INSERT OR IGNORE INTO investment_monthly (id, year_month, monthly_target, monthly_actual)
                    VALUES (?,?,?,?)
                """, (target_id, ym, 0, 0))
        
        conn.commit()
        conn.close()
        return redirect("/list")
    except Exception as e:
        print("❌ 저장 오류:", e)
        import traceback
        traceback.print_exc()
        return f"저장 오류: {e}", 500

@app.route("/list")
def list_page():
    conn = get_db()
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
        
        rate_target = "-"
        rate_actual = "-"
        if base and base != 0:
            if sav_tgt:
                rate_target = round((sav_tgt/base)*100, 1)
            if sav_act:
                rate_actual = round((sav_act/base)*100, 1)
        
        r.append(rate_target)
        r.append(rate_actual)
        
        m_data = monthly_map.get(r[0], {})
        monthly_arr = []
        for ym in MONTHS:
            t, a = m_data.get(ym, (0, 0))
            monthly_arr.append(t)
            monthly_arr.append(a)
        r.append(monthly_arr)
        
        processed.append(r)
    
    print(f"   처리: {len(processed)}건")
    
    processed_json = json.dumps(processed, ensure_ascii=False)
    months_json = json.dumps(MONTHS, ensure_ascii=False)
    
    return render_template_string(LIST_TPL, processed_json=processed_json, months_json=months_json)

@app.route("/delete/<row_id>", methods=["POST"])
def delete_row(row_id):
    conn = get_db()
    c = conn.cursor()
    is_postgres = os.environ.get("DATABASE_URL") is not None
    
    if is_postgres:
        c.execute("DELETE FROM investment WHERE id=%s", (row_id,))
        c.execute("DELETE FROM investment_monthly WHERE id=%s", (row_id,))
    else:
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
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>설비투자비 한계돌파 실적 기입</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
* { 
  margin:0; 
  padding:0; 
  box-sizing:border-box; 
}

body {
  font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.dashboard-header {
  background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
  color: white;
  padding: 25px 40px;
  border-radius: 12px;
  margin-bottom: 25px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.dashboard-header .classification {
  background: rgba(255,255,255,0.2);
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.container {
  max-width: 1600px;
  margin: 0 auto;
}

.nav-link {
  display: inline-block;
  margin-bottom: 20px;
  padding: 12px 25px;
  background: linear-gradient(90deg, #2575fc 0%, #6a11cb 100%);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 4px 10px rgba(37, 117, 252, 0.3);
  transition: all 0.3s;
}

.nav-link:hover { 
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(37, 117, 252, 0.4);
}

.two-column-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.05);
  transition: all 0.3s;
  margin-bottom: 20px;
}

.section:hover {
  box-shadow: 0 8px 25px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e3c72;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 3px solid #2575fc;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, #2575fc 0%, #6a11cb 100%);
  border-radius: 2px;
}

.section-title.blue::before {
  background: linear-gradient(180deg, #2575fc 0%, #6a11cb 100%);
}
.section-title.blue {
  border-bottom-color: #2575fc;
}

.section-title.teal::before {
  background: linear-gradient(180deg, #14b8a6 0%, #0d9488 100%);
}
.section-title.teal {
  border-bottom-color: #14b8a6;
  color: #0d9488;
}

.section-title.green::before {
  background: linear-gradient(180deg, #22c55e 0%, #16a34a 100%);
}
.section-title.green {
  border-bottom-color: #22c55e;
  color: #16a34a;
}

.section-title.orange::before {
  background: linear-gradient(180deg, #f97316 0%, #ea580c 100%);
}
.section-title.orange {
  border-bottom-color: #f97316;
  color: #ea580c;
}

.section-title.purple::before {
  background: linear-gradient(180deg, #a855f7 0%, #9333ea 100%);
}
.section-title.purple {
  border-bottom-color: #a855f7;
  color: #9333ea;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 15px;
}

.form-row.three-col {
  grid-template-columns: repeat(3, 1fr);
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 8px;
  letter-spacing: -0.2px;
}

.form-label-icon {
  font-size: 16px;
}

input[type="text"],
input[type="month"],
input[type="number"],
select,
textarea {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Noto Sans KR', sans-serif;
  transition: all 0.3s;
  background: #f8fafc;
}

input[type="text"]:focus,
input[type="month"]:focus,
input[type="number"]:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: #2575fc;
  background: white;
  box-shadow: 0 0 0 3px rgba(37, 117, 252, 0.1);
}

select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 18px;
  padding-right: 40px;
}

textarea {
  min-height: 100px;
  resize: vertical;
  line-height: 1.6;
}

.card-select {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.card-select-item {
  position: relative;
  cursor: pointer;
}

.card-select-item input[type="radio"] {
  position: absolute;
  opacity: 0;
}

.card-select-item label {
  display: block;
  padding: 15px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  text-align: center;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8fafc;
}

.card-select-item input[type="radio"]:checked + label {
  border-color: #2575fc;
  background: linear-gradient(135deg, rgba(37, 117, 252, 0.1) 0%, rgba(106, 17, 203, 0.1) 100%);
  color: #2575fc;
  box-shadow: 0 0 0 3px rgba(37, 117, 252, 0.1);
}

.card-select-item label:hover {
  border-color: #2575fc;
  transform: translateY(-2px);
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-top: 15px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 0 0 1px #e2e8f0;
}

table th {
  background: linear-gradient(180deg, #f7fafc 0%, #edf2f7 100%);
  padding: 14px 10px;
  font-size: 11px;
  font-weight: 700;
  color: #2d3748;
  text-align: center;
  border-bottom: 2px solid #cbd5e0;
  line-height: 1.4;
}

table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid #e2e8f0;
  background: white;
}

table tbody tr:hover td {
  background: #f7fafc;
}

table input {
  width: 100%;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  text-align: center;
  font-size: 13px;
  background: white;
}

table input:focus {
  outline: none;
  border-color: #2575fc;
  box-shadow: 0 0 0 2px rgba(37, 117, 252, 0.1);
}

.btn-group {
  text-align: center;
  margin-top: 35px;
  padding: 25px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

button {
  padding: 14px 35px;
  margin: 0 8px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Noto Sans KR', sans-serif;
  letter-spacing: -0.3px;
}

.btn-save {
  background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3);
}

.btn-save:hover { 
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(17, 153, 142, 0.4);
}

.btn-list {
  background: linear-gradient(90deg, #2575fc 0%, #6a11cb 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(37, 117, 252, 0.3);
}

.btn-list:hover { 
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(37, 117, 252, 0.4);
}

.highlight-box {
  background: linear-gradient(135deg, rgba(37, 117, 252, 0.05) 0%, rgba(106, 17, 203, 0.05) 100%);
  border-left: 4px solid #2575fc;
  padding: 15px;
  border-radius: 8px;
  margin-top: 10px;
}

@media (max-width: 1200px) {
  .two-column-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .form-row,
  .form-row.three-col {
    grid-template-columns: 1fr;
  }
  
  .card-select {
    grid-template-columns: 1fr;
  }
  
  table {
    font-size: 11px;
  }
  
  .btn-group button {
    display: block;
    width: 100%;
    margin: 10px 0;
  }
}
</style>
</head>
<body>
<div class="container">
  <div class="dashboard-header">
    <h1>📝 설비투자비 한계돌파 실적 관리 시스템</h1>
    <div class="classification">
      {% if row_id %}데이터 수정 모드{% else %}신규 데이터 입력{% endif %}
    </div>
  </div>
  
  <a href="/list" class="nav-link">📊 대시보드 조회 →</a>
  
  <form method="POST" action="/save" onsubmit="return validateForm()">
    {% if row_id %}<input type="hidden" name="row_id" value="{{ row_id }}">{% endif %}
    
    <div class="two-column-grid">
      <div class="section">
        <div class="section-title blue">📌 투자 분류</div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">🏷️</span>
            투자 유형
          </label>
          <div class="card-select">
            <div class="card-select-item">
              <input type="radio" name="invest_type" id="type_expand" value="확장" 
                {% if not edit_data or edit_data[1]=='확장' %}checked{% endif %}>
              <label for="type_expand">확장</label>
            </div>
            <div class="card-select-item">
              <input type="radio" name="invest_type" id="type_regular" value="경상"
                {% if edit_data and edit_data[1]=='경상' %}checked{% endif %}>
              <label for="type_regular">경상</label>
            </div>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              <span class="form-label-icon">📦</span>
              제품
            </label>
            <select name="product">
              {% for p in products %}
              <option value="{{ p }}" {% if edit_data and edit_data[2]==p %}selected{% endif %}>{{ p }}</option>
              {% endfor %}
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">
              <span class="form-label-icon">🌍</span>
              법인
            </label>
            <select name="corporation">
              {% for c in corporations %}
              <option value="{{ c }}" {% if edit_data and edit_data[3]==c %}selected{% endif %}>{{ c }}</option>
              {% endfor %}
            </select>
          </div>
        </div>
      </div>
      
      <div class="section">
        <div class="section-title teal">📋 투자 항목 상세</div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">🎯</span>
            투자목적
          </label>
          <select name="purpose">
            {% for p in all_purposes %}
            <option value="{{ p }}" {% if edit_data and edit_data[4]==p %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">⚙️</span>
            투자항목
          </label>
          <input type="text" name="invest_item" 
            value="{% if edit_data %}{{ edit_data[5] or '' }}{% endif %}" 
            placeholder="예: 창원 선진화 오븐라인">
        </div>
        
        <div class="highlight-box">
          <small style="color: #64748b;">
            💡 <strong>TIP:</strong> 투자항목은 구체적으로 작성해주세요<br>
            (예: "라인 #3 자동화 설비 도입" 등)
          </small>
        </div>
      </div>
    </div>
    
    <div class="section">
      <div class="section-title orange">📅 투자 주요 일정</div>
      
      <div class="form-row three-col">
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">🎯</span>
            발주 목표
          </label>
          <input type="month" name="order_target" 
            value="{% if edit_data %}{{ edit_data[6] or '' }}{% endif %}">
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">✅</span>
            발주 실적
          </label>
          <input type="month" name="order_actual" 
            value="{% if edit_data %}{{ edit_data[7] or '' }}{% endif %}">
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">🎯</span>
            셋업 목표
          </label>
          <input type="month" name="setup_target" 
            value="{% if edit_data %}{{ edit_data[8] or '' }}{% endif %}">
        </div>
      </div>
      
      <div class="form-row three-col">
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">✅</span>
            셋업 실적
          </label>
          <input type="month" name="setup_actual" 
            value="{% if edit_data %}{{ edit_data[9] or '' }}{% endif %}">
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">🎯</span>
            양산 목표
          </label>
          <input type="month" name="mass_target" 
            value="{% if edit_data %}{{ edit_data[10] or '' }}{% endif %}">
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">✅</span>
            양산 실적
          </label>
          <input type="month" name="mass_actual" 
            value="{% if edit_data %}{{ edit_data[11] or '' }}{% endif %}">
        </div>
      </div>
      
      <div class="form-group">
        <label class="form-label">
          <span class="form-label-icon">❓</span>
          연기사유
        </label>
        <input type="text" name="delay_reason" 
          value="{% if edit_data %}{{ edit_data[12] or '' }}{% endif %}" 
          placeholder="일정 연기 시 사유를 입력하세요">
      </div>
    </div>
    
    <div class="two-column-grid">
      <div class="section">
        <div class="section-title green">💰 투자금액 (단위: 억원)</div>
        
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              <span class="form-label-icon">💵</span>
              Base 금액
            </label>
            <input type="number" step="0.01" name="base_amount" 
              value="{% if edit_data %}{{ edit_data[13] or '' }}{% endif %}" 
              placeholder="0.00">
          </div>
          
          <div class="form-group">
            <label class="form-label">
              <span class="form-label-icon">🎯</span>
              발주가 목표
            </label>
            <input type="number" step="0.01" name="order_price_target" 
              value="{% if edit_data %}{{ edit_data[14] or '' }}{% endif %}" 
              placeholder="0.00">
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <span class="form-label-icon">✅</span>
            발주가 실적
          </label>
          <input type="number" step="0.01" name="order_price_actual" 
            value="{% if edit_data %}{{ edit_data[15] or '' }}{% endif %}" 
            placeholder="0.00">
        </div>
      </div>
      
      <div class="section">
        <div class="section-title purple">📊 절감 실적 (단위: 억원)</div>
        
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              <span class="form-label-icon">🎯</span>
              절감 목표
            </label>
            <input type="number" step="0.01" name="saving_target" 
              value="{% if edit_data %}{{ edit_data[16] or '' }}{% endif %}" 
              placeholder="0.00">
          </div>
          
          <div class="form-group">
            <label class="form-label">
              <span class="form-label-icon">✅</span>
              절감 실적 (자동계산)
            </label>
            <input type="number" step="0.01" name="saving_actual" id="saving_actual"
              value="{% if edit_data %}{{ edit_data[17] or '' }}{% endif %}" 
              placeholder="0.00" readonly style="background: #f0f9ff; font-weight: 700; cursor: not-allowed;">
          </div>
        </div>
        
        <div class="highlight-box">
          <small style="color: #64748b;">
            💡 절감 실적은 아래 세부 항목의 합계가 자동 계산됩니다
          </small>
        </div>
      </div>
    </div>
    
    <div class="section">
      <div class="section-title green">📊 투자비 절감 활동 세부내역 (단위: 억원)</div>
      
      <table>
        <thead>
          <tr>
            <th style="width: 120px;">항목</th>
            <th style="width: 100px;">합계</th>
            <th>①신기술<br>신공법</th>
            <th>②염가형<br>부품</th>
            <th>③중국/<br>Local 설비</th>
            <th>④중국/한국<br>Collabo</th>
            <th>⑤컨테이너<br>최소화</th>
            <th>⑥출장 인원<br>최소화</th>
            <th>⑦유휴<br>설비</th>
            <th>⑧사양<br>최적화</th>
            <th>⑨기타</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>금액(억원)</strong></td>
            <td>
              <input type="number" step="0.01" name="saving_total" id="saving_total"
                value="{% if edit_data %}{{ edit_data[27] or '' }}{% endif %}" 
                placeholder="0.00" readonly style="background: #f0f9ff; font-weight: 700;">
            </td>
            <td><input type="number" step="0.01" name="reduce_1" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[18] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_2" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[19] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_3" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[20] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_4" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[21] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_5" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[22] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_6" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[23] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_7" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[24] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_8" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[25] or '' }}{% endif %}" placeholder="0.00"></td>
            <td><input type="number" step="0.01" name="reduce_9" class="reduce-input"
              value="{% if edit_data %}{{ edit_data[26] or '' }}{% endif %}" placeholder="0.00"></td>
          </tr>
        </tbody>
      </table>
      
      <div class="form-group" style="margin-top: 20px;">
        <label class="form-label">
          <span class="form-label-icon">📝</span>
          활동내용
        </label>
        <textarea name="activity" placeholder="절감 활동 내용을 상세히 입력하세요
예) 1) 자동화 공법 개발 및 설비 개선
    3) 중국 업체 활용
    6) 안정화 기간 단축 및 Local 업체 활용">{% if edit_data %}{{ edit_data[28] or '' }}{% endif %}</textarea>
      </div>
    </div>

    <div class="btn-group">
      <button type="submit" class="btn-save">💾 저장하기</button>
      <button type="button" class="btn-list" onclick="location.href='/list'">📊 대시보드 보기</button>
    </div>
  </form>
</div>

<script>
let manualEditAllowed = false;

function calculateTotal() {
  const inputs = document.querySelectorAll('.reduce-input');
  let total = 0;
  
  inputs.forEach(input => {
    const value = parseFloat(input.value) || 0;
    total += value;
  });
  
  const totalInput = document.querySelector('input[name="saving_total"]');
  const actualInput = document.querySelector('input[name="saving_actual"]');
  
  totalInput.value = total.toFixed(2);
  actualInput.value = total.toFixed(2);
}

document.addEventListener('DOMContentLoaded', function() {
  const inputs = document.querySelectorAll('.reduce-input');
  inputs.forEach(input => {
    input.addEventListener('input', calculateTotal);
  });
  
  calculateTotal();
});

function validateForm() {
  return true;
}
</script>
</body>
</html>
"""

LIST_TPL = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>투자 실적 조회</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
* { 
  margin:0; 
  padding:0; 
  box-sizing:border-box; 
}

body {
  font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.dashboard-header {
  background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
  color: white;
  padding: 25px 40px;
  border-radius: 12px;
  margin-bottom: 25px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.container {
  max-width: 98%;
  margin: 0 auto;
}

.nav-link {
  display: inline-block;
  margin-bottom: 20px;
  padding: 12px 25px;
  background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 4px 10px rgba(17, 153, 142, 0.3);
  transition: all 0.3s;
}

.nav-link:hover { 
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(17, 153, 142, 0.4);
}

.filter-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-section select {
  padding: 10px 15px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Noto Sans KR', sans-serif;
  background: #f8fafc;
  cursor: pointer;
  font-weight: 500;
}

.filter-section select:focus {
  outline: none;
  border-color: #2575fc;
  background: white;
}

.legend {
  background: white;
  padding: 15px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 13px;
  font-weight: 500;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-box {
  width: 20px;
  height: 20px;
  border-radius: 4px;
}

.table-container {
  background: white;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  overflow: auto;
  max-height: 70vh;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

table thead {
  position: sticky;
  top: 0;
  z-index: 10;
}

table th {
  background: linear-gradient(180deg, #f7fafc 0%, #edf2f7 100%);
  padding: 14px 8px;
  font-weight: 700;
  color: #2d3748;
  text-align: center;
  border-bottom: 2px solid #cbd5e0;
  border-right: 1px solid #e2e8f0;
  line-height: 1.4;
  white-space: nowrap;
}

table td {
  padding: 12px 8px;
  text-align: center;
  border-bottom: 1px solid #e2e8f0;
  border-right: 1px solid #f7fafc;
}

table tbody tr:hover {
  background: #f7fafc;
}

table tbody tr.hidden {
  display: none;
}

.status-excellent { background-color: #c6f6d5 !important; }
.status-good { background-color: #fef3c7 !important; }
.status-poor { background-color: #fecaca !important; }
.status-empty { background-color: #f3f4f6 !important; }

.btn-edit, .btn-delete {
  padding: 6px 12px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  margin: 2px;
  transition: all 0.2s;
  display: block;
  width: 100%;
  margin-bottom: 4px;
}

.btn-edit {
  background: linear-gradient(90deg, #2575fc 0%, #6a11cb 100%);
  color: white;
}

.btn-edit:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(37, 117, 252, 0.3);
}

.btn-delete {
  background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.btn-delete:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(245, 87, 108, 0.3);
}

@media (max-width: 768px) {
  table {
    font-size: 10px;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-section select {
    width: 100%;
  }
}
</style>
</head>
<body>
<div class="container">
  <div class="dashboard-header">
    <h1>📊 설비투자비 한계돌파 누적 실적 대시보드</h1>
  </div>
  
  <a href="/" class="nav-link">◀ 데이터 입력하기</a>
  
  <div class="legend">
    <div class="legend-item">
      <div class="legend-box status-excellent"></div>
      <span>목표 초과</span>
    </div>
    <div class="legend-item">
      <div class="legend-box status-good"></div>
      <span>진행 중</span>
    </div>
    <div class="legend-item">
      <div class="legend-box status-poor"></div>
      <span>미달성</span>
    </div>
    <div class="legend-item">
      <div class="legend-box status-empty"></div>
      <span>미입력</span>
    </div>
  </div>
  
  <div class="filter-section">
    <label style="font-weight:700; color:#2d3748;">필터:</label>
    <select id="filterProduct" onchange="applyFilters()">
      <option value="">제품 전체</option>
      <option value="키친">키친</option>
      <option value="빌트인쿠킹">빌트인쿠킹</option>
      <option value="리빙">리빙</option>
      <option value="부품">부품</option>
      <option value="ES">ES</option>
    </select>
    <select id="filterCorp" onchange="applyFilters()">
      <option value="">법인 전체</option>
      <option value="KR">KR</option>
      <option value="AI">AI</option>
      <option value="AT">AT</option>
      <option value="AZ">AZ</option>
      <option value="EG">EG</option>
      <option value="IL_N">IL_N</option>
      <option value="IL_P">IL_P</option>
      <option value="IN_T">IN_T</option>
      <option value="MN">MN</option>
      <option value="MX">MX</option>
      <option value="MZ">MZ</option>
      <option value="PN">PN</option>
      <option value="RA">RA</option>
      <option value="SR">SR</option>
      <option value="TA">TA</option>
      <option value="TH">TH</option>
      <option value="TN">TN</option>
      <option value="TR">TR</option>
      <option value="VH">VH</option>
      <option value="WR">WR</option>
    </select>
    <select id="filterType" onchange="applyFilters()">
      <option value="">투자유형 전체</option>
      <option value="확장">확장</option>
      <option value="경상">경상</option>
    </select>
  </div>
  
  <div class="table-container">
    <table id="mainTable">
      <thead>
        <tr>
          <th rowspan="2" style="min-width: 90px;">수정/삭제</th>
          <th rowspan="2" style="min-width: 80px;">제품</th>
          <th rowspan="2" style="min-width: 55px;">법인</th>
          <th rowspan="2" style="min-width: 60px;">투자<br>유형</th>
          <th rowspan="2" style="min-width: 150px;">투자항목</th>
          <th rowspan="2" style="min-width: 100px;">투자목적</th>
          <th colspan="7">📅 투자 주요 일정</th>
          <th colspan="5">💰 투자절감</th>
          <th colspan="10">📊 절감 활동 및 실적</th>
          <th colspan="3">🎯 목표</th>
          <th colspan="48">📆 월별 절감 실적 (26.01~27.12)</th>
        </tr>
        <tr>
          <th>발주<br>목표</th>
          <th>발주<br>실적</th>
          <th>셋업<br>목표</th>
          <th>셋업<br>실적</th>
          <th>양산<br>목표</th>
          <th>양산<br>실적</th>
          <th>연기<br>사유</th>
          <th>Base</th>
          <th>발주가<br>목표</th>
          <th>발주가<br>실적</th>
          <th>절감<br>목표</th>
          <th>절감<br>실적<br>(합계)</th>
          <th>①신기술<br>신공법</th>
          <th>②염가형<br>부품</th>
          <th>③중국/<br>Local</th>
          <th>④중국/한국<br>Collabo</th>
          <th>⑤컨테이너<br>최소화</th>
          <th>⑥출장<br>최소화</th>
          <th>⑦유휴<br>설비</th>
          <th>⑧사양<br>최적화</th>
          <th>⑨기타</th>
          <th style="min-width: 150px;">활동내용</th>
          <th>절감률<br>목표(%)</th>
          <th>절감률<br>실적(%)</th>
          <th>Signal</th>
          <th>26.01월<br>(목표)</th><th>26.01월<br>(실적)</th>
          <th>26.02월<br>(목표)</th><th>26.02월<br>(실적)</th>
          <th>26.03월<br>(목표)</th><th>26.03월<br>(실적)</th>
          <th>26.04월<br>(목표)</th><th>26.04월<br>(실적)</th>
          <th>26.05월<br>(목표)</th><th>26.05월<br>(실적)</th>
          <th>26.06월<br>(목표)</th><th>26.06월<br>(실적)</th>
          <th>26.07월<br>(목표)</th><th>26.07월<br>(실적)</th>
          <th>26.08월<br>(목표)</th><th>26.08월<br>(실적)</th>
          <th>26.09월<br>(목표)</th><th>26.09월<br>(실적)</th>
          <th>26.10월<br>(목표)</th><th>26.10월<br>(실적)</th>
          <th>26.11월<br>(목표)</th><th>26.11월<br>(실적)</th>
          <th>26.12월<br>(목표)</th><th>26.12월<br>(실적)</th>
          <th>27.01월<br>(목표)</th><th>27.01월<br>(실적)</th>
          <th>27.02월<br>(목표)</th><th>27.02월<br>(실적)</th>
          <th>27.03월<br>(목표)</th><th>27.03월<br>(실적)</th>
          <th>27.04월<br>(목표)</th><th>27.04월<br>(실적)</th>
          <th>27.05월<br>(목표)</th><th>27.05월<br>(실적)</th>
          <th>27.06월<br>(목표)</th><th>27.06월<br>(실적)</th>
          <th>27.07월<br>(목표)</th><th>27.07월<br>(실적)</th>
          <th>27.08월<br>(목표)</th><th>27.08월<br>(실적)</th>
          <th>27.09월<br>(목표)</th><th>27.09월<br>(실적)</th>
          <th>27.10월<br>(목표)</th><th>27.10월<br>(실적)</th>
          <th>27.11월<br>(목표)</th><th>27.11월<br>(실적)</th>
          <th>27.12월<br>(목표)</th><th>27.12월<br>(실적)</th>
        </tr>
      </thead>
      <tbody id="tableBody">
      </tbody>
    </table>
  </div>
</div>

<script>
const processedData = {{ processed_json|safe }};
const months = {{ months_json|safe }};

function renderTable() {
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '';
  
  let totalCount = 0;
  
  processedData.forEach(row => {
    totalCount++;
    const tr = document.createElement('tr');
    tr.setAttribute('data-product', row[2]);
    tr.setAttribute('data-corp', row[3]);
    tr.setAttribute('data-type', row[1]);
    
    let html = '';
    
    // 수정/삭제 버튼 (제일 왼쪽)
    html += '<td style="white-space:nowrap;">';
    html += '<button class="btn-edit" onclick="location.href=\'/edit/' + row[0] + '\'">수정</button>';
    html += '<button class="btn-delete" onclick="deleteRow(' + row[0] + ')">삭제</button>';
    html += '</td>';
    
    // 제품 (줄바꿈 처리)
    let productName = row[2] || '-';
    if (productName === '빌트인쿠킹') {
      productName = '빌트인<br>쿠킹';
    }
    html += '<td>' + productName + '</td>';
    
    // 나머지 기본 정보
    html += '<td>' + (row[3] || '-') + '</td>';
    html += '<td>' + (row[1] || '-') + '</td>';
    html += '<td>' + (row[5] || '-') + '</td>';
    html += '<td>' + (row[4] || '-') + '</td>';
    html += '<td>' + (row[6] || '-') + '</td>';
    html += '<td>' + (row[7] || '-') + '</td>';
    html += '<td>' + (row[8] || '-') + '</td>';
    html += '<td>' + (row[9] || '-') + '</td>';
    html += '<td>' + (row[10] || '-') + '</td>';
    html += '<td>' + (row[11] || '-') + '</td>';
    html += '<td>' + (row[12] || '-') + '</td>';
    html += '<td>' + (row[13] || '-') + '</td>';
    html += '<td>' + (row[14] || '-') + '</td>';
    html += '<td>' + (row[15] || '-') + '</td>';
    html += '<td>' + (row[16] || '-') + '</td>';
    html += '<td>' + (row[17] || '-') + '</td>';
    html += '<td>' + (row[18] || '-') + '</td>';
    html += '<td>' + (row[19] || '-') + '</td>';
    html += '<td>' + (row[20] || '-') + '</td>';
    html += '<td>' + (row[21] || '-') + '</td>';
    html += '<td>' + (row[22] || '-') + '</td>';
    html += '<td>' + (row[23] || '-') + '</td>';
    html += '<td>' + (row[24] || '-') + '</td>';
    html += '<td>' + (row[25] || '-') + '</td>';
    html += '<td>' + (row[26] || '-') + '</td>';
    html += '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + (row[28] || '-') + '</td>';
    html += '<td>' + (row[29] || '-') + '</td>';
    html += '<td>' + (row[30] || '-') + '</td>';
    html += '<td class="' + getSignalClass(row[29], row[30]) + '">●</td>';
    
    tr.innerHTML = html;
    
    // 월별 데이터
    const monthlyData = row[31] || [];
    for (let i = 0; i < 48; i++) {
      const td = document.createElement('td');
      td.textContent = monthlyData[i] || '-';
      tr.appendChild(td);
    }
    
    tbody.appendChild(tr);
  });
  
  document.querySelector('.dashboard-header h1').textContent = 
    '📊 설비투자비 한계돌파 누적 실적 대시보드 (총 ' + totalCount + '건)';
}

function getSignalClass(target, actual) {
  if (target === '-' || actual === '-') return 'status-empty';
  const t = parseFloat(target);
  const a = parseFloat(actual);
  if (a >= t) return 'status-excellent';
  if (a >= t * 0.8) return 'status-good';
  return 'status-poor';
}

function applyFilters() {
  const product = document.getElementById('filterProduct').value;
  const corp = document.getElementById('filterCorp').value;
  const type = document.getElementById('filterType').value;
  
  const rows = document.querySelectorAll('#tableBody tr');
  let visibleCount = 0;
  
  rows.forEach(row => {
    const matchProduct = !product || row.getAttribute('data-product') === product;
    const matchCorp = !corp || row.getAttribute('data-corp') === corp;
    const matchType = !type || row.getAttribute('data-type') === type;
    
    if (matchProduct && matchCorp && matchType) {
      row.classList.remove('hidden');
      visibleCount++;
    } else {
      row.classList.add('hidden');
    }
  });
  
  document.querySelector('.dashboard-header h1').textContent = 
    '📊 설비투자비 한계돌파 누적 실적 대시보드 (총 ' + processedData.length + '건 중 ' + visibleCount + '건 표시)';
}

function deleteRow(id) {
  if (!confirm('정말 삭제하시겠습니까?')) return;
  fetch('/delete/' + id, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert('삭제되었습니다.');
        location.reload();
      }
    })
    .catch(err => alert('삭제 오류: ' + err));
}

renderTable();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("🚀 Flask 서버 시작")
    print(f"📁 DB: {DB_NAME}")
    print("📍 주소: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)