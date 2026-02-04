from flask import Flask, request, redirect, url_for, render_template_string, jsonify

import os
import json
from datetime import datetime
from urllib.parse import urlparse

try:
    import psycopg2
except ImportError:
    psycopg2 = None
from datetime import datetime
import os
import json

app = Flask(__name__)
import sqlite3

def get_db():
    database_url = os.environ.get("DATABASE_URL")

    # ✅ Render / PostgreSQL
    if database_url:
        if psycopg2 is None:
            raise Exception("psycopg2가 설치되어 있지 않습니다")

        result = urlparse(database_url)
        return psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
            sslmode="require"
        )

    # ✅ 로컬 / SQLite
    return sqlite3.connect(DB_NAME)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data.db")

def init_db():
    print(f"📁 DB 경로: {DB_NAME}")
    conn = get_db()
    c = conn.cursor()
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
    conn.commit()
    conn.close()
    print("✅ DB 초기화 완료")

if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("🚀 Flask 서버 시작")
    print("📍 주소: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)

PRODUCTS     = ["키친", "빌트인쿠킹", "리빙", "부품", "ES"]
CORPORATIONS = ["KR","AI","AT","AZ","EG","IL_N","IL_P","IN_T","MN","MX","MZ","PN","RA","SR","TA","TH","TN","TR","VH","WR"]
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
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM investment WHERE id = %s", (row_id,))
        edit_data = c.fetchone()
        conn.close()
        if not edit_data:
            return "데이터를 찾을 수 없습니다.", 404
    return render_template_string(INPUT_TPL,
        products=PRODUCTS, 
        corporations=CORPORATIONS,
        all_purposes=ALL_PURPOSES,
        edit_data=edit_data, 
        row_id=row_id)

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

        if row_id:
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
            )
            RETURNING id
            """, values + (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))

            target_id = c.fetchone()[0]
        
        # ❌ investment 삭제 제거
        # c.execute("DELETE FROM investment WHERE id=%s", (row_id,))

        # ✅ 월별 데이터만 초기화
        c.execute("DELETE FROM investment_monthly WHERE id=%s", (target_id,))
        for ym in MONTHS:
            c.execute(
                """
                INSERT INTO investment_monthly (id, year_month, monthly_target, monthly_actual)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (id, year_month)
                DO NOTHING
                """,
                (target_id, ym, 0, 0)
            )

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
    
    # JSON으로 안전하게 직렬화
    processed_json = json.dumps(processed, ensure_ascii=False)
    months_json = json.dumps(MONTHS, ensure_ascii=False)
    
    return render_template_string(LIST_TPL, 
        processed_json=processed_json,
        months_json=months_json)

@app.route("/delete/<int:row_id>", methods=["POST"])
def delete_row(row_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM investment WHERE id=%s", (row_id,))
    c.execute("DELETE FROM investment_monthly WHERE id=%s", (row_id,))
    conn.commit()
    conn.close()
    print(f"🗑️ 삭제: ID={row_id}")
    return jsonify({"success": True})

INPUT_TPL = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>설비투자비한계돌파 실적 기입</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Malgun Gothic','맑은 고딕',Arial,sans-serif;font-size:13px;background:#eef2f7;color:#2c3e50;min-height:100vh}
.top-nav{background:#1a3a5c;color:#fff;padding:11px 24px;display:flex;align-items:center;gap:20px;box-shadow:0 2px 6px rgba(0,0,0,.2)}
.top-nav h2{font-size:17px;font-weight:600}
.top-nav a{color:#a8d4f0;text-decoration:none;font-size:13px;transition:color .2s}
.top-nav a:hover{color:#fff}
.content{max-width:1340px;margin:22px auto;padding:0 20px}
.card{background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.08);margin-bottom:16px;overflow:hidden;border:1px solid #dce5ee}
.card-header{padding:9px 16px;font-weight:700;font-size:13px;color:#fff;display:flex;align-items:center;gap:8px}
.card-header.blue{background:#1a3a5c}
.card-header.teal{background:#2e6da4}
.card-header.green{background:#3d8b5e}
.card-header.gold{background:#b8860b}
.card table{width:100%;border-collapse:collapse}
.card table td,.card table th{border:1px solid #dce5ee;padding:7px 10px;vertical-align:middle}
.card table th{background:#f0f4f8;font-weight:600;color:#1a3a5c;font-size:12px;text-align:left;white-space:nowrap}
td.label{background:#eef3f8;font-weight:600;color:#1a3a5c;white-space:nowrap;text-align:left;padding-left:12px;width:105px}
input[type="text"],input[type="number"],input[type="month"],select,textarea{
    width:100%;padding:6px 9px;border:1px solid #c8d4df;border-radius:4px;
    font-size:12.5px;font-family:inherit;background:#fafcfe;
    transition:border .2s,box-shadow .2s;outline:none
}
input:focus,select:focus,textarea:focus{border-color:#2e6da4;box-shadow:0 0 0 2px rgba(46,109,164,.18);background:#fff}
textarea{resize:vertical;min-height:72px}
input[readonly]{background:#e8f0f7;font-weight:700;color:#1a3a5c;border-color:#b0c4d8}
textarea::placeholder{color:#999;font-style:italic}
textarea:not(:placeholder-shown){color:#2c3e50}
.reduce-table th{background:#fdf3dc;color:#7a5a00;font-size:11px;text-align:center;padding:5px 4px;min-width:74px}
.reduce-table td{text-align:center;padding:5px 4px}
.reduce-table input{min-width:62px;max-width:78px;text-align:center}
.rn{display:block;font-size:10px;color:#b8860b;font-weight:700;margin-bottom:1px}
td.sav-actual-cell{background:#eef3f8;font-weight:600;color:#1a3a5c;text-align:left;padding-left:12px;white-space:nowrap;width:105px}
.btn-area{max-width:1340px;margin:0 auto 28px;padding:0 20px;display:flex;gap:12px;align-items:center}
.btn-primary{background:#1a3a5c;color:#fff;border:none;padding:10px 32px;border-radius:5px;font-size:14px;font-weight:600;cursor:pointer;transition:background .2s}
.btn-primary:hover{background:#2e5a8c}
.btn-secondary{background:#fff;color:#1a3a5c;border:2px solid #1a3a5c;padding:9px 24px;border-radius:5px;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;transition:background .2s,color .2s}
.btn-secondary:hover{background:#1a3a5c;color:#fff}
</style>
</head>
<body>

<div class="top-nav">
    <h2>📝 설비투자비한계돌파 실적 기입 {% if row_id %}(수정){% endif %}</h2>
    <a href="/list">📊 조회 페이지 →</a>
</div>

<div class="content">
<form method="post" action="/save">
{% if row_id %}<input type="hidden" name="row_id" value="{{ row_id }}">{% endif %}

<div class="card">
<div class="card-header blue">📌 투자 분류</div>
<table>
<tr>
    <td class="label">투자 유형</td>
    <td style="width:120px">
        <select name="invest_type">
            <option {% if edit_data and edit_data[1]=='확장' %}selected{% endif %}>확장</option>
            <option {% if edit_data and edit_data[1]=='경상' %}selected{% endif %}>경상</option>
        </select>
    </td>
    <td class="label">제품</td>
    <td style="width:140px">
        <select name="product">
            {% for p in products %}
            <option {% if edit_data and edit_data[2]==p %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
        </select>
    </td>
    <td class="label">법인</td>
    <td style="width:110px">
        <select name="corporation">
            {% for c in corporations %}
            <option {% if edit_data and edit_data[3]==c %}selected{% endif %}>{{ c }}</option>
            {% endfor %}
        </select>
    </td>
    <td class="label">투자목적</td>
    <td style="width:160px">
        <select name="purpose">
            {% for p in all_purposes %}
            <option {% if edit_data and edit_data[4]==p %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
        </select>
    </td>
</tr>
<tr>
    <td class="label">투자항목</td>
    <td colspan="7"><input type="text" name="invest_item" value="{% if edit_data %}{{ edit_data[5] or '' }}{% endif %}" placeholder="ex) 창원 선진화 오븐라인"></td>
</tr>
</table>
</div>

<div class="card">
<div class="card-header teal">📅 투자 주요 일정</div>
<table>
<tr>
    <td class="label">발주 목표</td><td style="width:170px"><input type="month" name="order_target" value="{% if edit_data %}{{ edit_data[6] or '' }}{% endif %}"></td>
    <td class="label">발주 실적</td><td style="width:170px"><input type="month" name="order_actual" value="{% if edit_data %}{{ edit_data[7] or '' }}{% endif %}"></td>
</tr>
<tr>
    <td class="label">셋업 목표</td><td><input type="month" name="setup_target" value="{% if edit_data %}{{ edit_data[8] or '' }}{% endif %}"></td>
    <td class="label">셋업 실적</td><td><input type="month" name="setup_actual" value="{% if edit_data %}{{ edit_data[9] or '' }}{% endif %}"></td>
</tr>
<tr>
    <td class="label">양산 목표</td><td><input type="month" name="mass_target" value="{% if edit_data %}{{ edit_data[10] or '' }}{% endif %}"></td>
    <td class="label">양산 실적</td><td><input type="month" name="mass_actual" value="{% if edit_data %}{{ edit_data[11] or '' }}{% endif %}"></td>
</tr>
<tr>
    <td class="label">연기사유</td>
    <td colspan="3"><input type="text" name="delay_reason" value="{% if edit_data %}{{ edit_data[12] or '' }}{% endif %}" placeholder="발주·양산 연기 시 사유 기재"></td>
</tr>
</table>
</div>

<div class="card">
<div class="card-header green">💰 투자절감 실적 (단위: 억원)</div>
<table>
<tr>
    <td class="label">Base 금액</td>
    <td style="width:130px"><input type="number" name="base_amount" step="0.01" value="{% if edit_data %}{{ edit_data[13] or '' }}{% endif %}" placeholder="0.0"></td>
    <td class="label">발주가 목표</td>
    <td style="width:130px"><input type="number" name="order_price_target" step="0.01" value="{% if edit_data %}{{ edit_data[14] or '' }}{% endif %}" placeholder="0.0"></td>
    <td class="label">발주가 실적</td>
    <td style="width:130px"><input type="number" name="order_price_actual" step="0.01" value="{% if edit_data %}{{ edit_data[15] or '' }}{% endif %}" placeholder="0.0"></td>
    <td class="label">절감 목표</td>
    <td style="width:130px"><input type="number" name="saving_target" step="0.01" value="{% if edit_data %}{{ edit_data[16] or '' }}{% endif %}" placeholder="0.0"></td>
</tr>
</table>
</div>

<div class="card">
<div class="card-header gold">📊 투자비 절감 활동 및 실적 (단위: 억원)</div>
<table class="reduce-table">
<thead><tr>
    <th style="min-width:72px">항목</th>
    <th style="min-width:105px; background:#dce8f0; color:#1a3a5c;">절감 실적<br>(합계)</th>
    <th><span class="rn">①</span>신기술<br>신공법</th>
    <th><span class="rn">②</span>염가형<br>부품</th>
    <th><span class="rn">③</span>중국/<br>Local 설비</th>
    <th><span class="rn">④</span>중국/한국<br>Collabo</th>
    <th><span class="rn">⑤</span>컨테이너<br>최소화</th>
    <th><span class="rn">⑥</span>출장 인원<br>최소화</th>
    <th><span class="rn">⑦</span>유휴<br>설비</th>
    <th><span class="rn">⑧</span>사양<br>최적화</th>
    <th><span class="rn">⑨</span>기타</th>
</tr></thead>
<tbody><tr>
    <td class="sav-actual-cell">금액(억원)</td>
    <td><input id="saving_actual" name="saving_actual" readonly value="{% if edit_data %}{{ edit_data[17] or '' }}{% endif %}" placeholder="0.0" style="min-width:100px;"></td>
    <td><input class="reduce" type="number" name="reduce_1" step="0.01" value="{% if edit_data %}{{ edit_data[18] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_2" step="0.01" value="{% if edit_data %}{{ edit_data[19] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_3" step="0.01" value="{% if edit_data %}{{ edit_data[20] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_4" step="0.01" value="{% if edit_data %}{{ edit_data[21] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_5" step="0.01" value="{% if edit_data %}{{ edit_data[22] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_6" step="0.01" value="{% if edit_data %}{{ edit_data[23] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_7" step="0.01" value="{% if edit_data %}{{ edit_data[24] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_8" step="0.01" value="{% if edit_data %}{{ edit_data[25] or '' }}{% endif %}" oninput="calcTotal()"></td>
    <td><input class="reduce" type="number" name="reduce_9" step="0.01" value="{% if edit_data %}{{ edit_data[26] or '' }}{% endif %}" oninput="calcTotal()"></td>
</tr>
<tr>
    <td colspan="11" style="padding:10px; background:#fff;">
        <div style="font-weight:600; color:#1a3a5c; margin-bottom:6px; font-size:12px;">활동내용</div>
        <textarea name="activity" rows="4" placeholder="1) 자동화 공법 개발 및 설비 개선, 3) 중국 업체 활용, 6) 안정화 기간 단축 및 Local 업체 활용, 7) 사내/협력사 유휴설비 활용, 8) 생산 Issue 발생 우려 공정 자동화 제외">{% if edit_data %}{{ edit_data[28] or '' }}{% endif %}</textarea>
    </td>
</tr>
</tbody>
</table>
</div>

<input type="hidden" name="saving_total" id="saving_total" value="{% if edit_data %}{{ edit_data[27] or '' }}{% endif %}">

</div>

<div class="btn-area">
    <button type="submit" class="btn-primary">💾 저장</button>
    <a href="/list" class="btn-secondary">📊 조회 페이지</a>
</div>

<script>
function calcTotal(){
    let s=0;
    document.querySelectorAll(".reduce").forEach(e=>{ s+=Number(e.value)||0; });
    const total = s.toFixed(2);
    document.getElementById("saving_actual").value = total;
    document.getElementById("saving_total").value = total;
}
window.onload = function(){ calcTotal(); }
</script>

</body>
</html>
"""

LIST_TPL = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>누적 실적 조회</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Malgun Gothic','맑은 고딕',Arial,sans-serif;font-size:12px;background:#f0f0f0;color:#333}
.top-nav{background:#1a3a5c;color:#fff;padding:10px 20px;display:flex;align-items:center;gap:24px;font-size:13px}
.top-nav h2{font-size:16px;font-weight:600;margin-right:12px}
.top-nav a{color:#a8d4f0;text-decoration:none}
.top-nav a:hover{color:#fff;text-decoration:underline}
.filter-bar{background:#fff;border-bottom:1px solid #ddd;padding:8px 20px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.filter-bar label{font-weight:600;color:#1a3a5c;font-size:12px}
.filter-bar select{padding:4px 8px;border:1px solid #ccc;border-radius:3px;font-size:12px}
.table-wrap{overflow-x:auto;overflow-y:auto;max-height:calc(100vh - 100px)}
table{border-collapse:collapse;white-space:nowrap;min-width:100%;background:#fff}
thead th{position:sticky;top:0;z-index:10;background:#1a3a5c;color:#fff;font-weight:600;font-size:11px;padding:6px 5px;border:1px solid #2a5a8c;text-align:center}
thead tr.gh th{background:#162d4a;font-size:11px;padding:4px 5px;border-bottom:2px solid #3a7ab5}
td.sc,th.sc{position:sticky;z-index:5;background:#eef3f8}
th.sc{background:#1a3a5c;z-index:15}
td.sc{border-right:2px solid #1a3a5c}
.c0{left:0;min-width:54px}
.c1{left:54px;min-width:46px}
.c2{left:100px;min-width:58px}
.c3{left:158px;min-width:230px}
tbody td{padding:5px 7px;border:1px solid #ddd;font-size:11.5px;text-align:center;vertical-align:middle}
td.left{text-align:left}
td.act-cell{text-align:left;max-width:175px;white-space:normal;word-break:break-all}
tbody tr:nth-child(even) td{background:#f7f9fc}
tbody tr:nth-child(odd)  td{background:#fff}
tbody tr:hover           td{background:#e2ecf7 !important}
tbody tr:nth-child(even) td.sc{background:#eef3f8}
tbody tr:nth-child(odd)  td.sc{background:#e4ecf5}
tbody tr:hover           td.sc{background:#d4e4f3 !important}
th.gs{background:#2e6da4}
th.gv{background:#3d8b5e}
th.gr{background:#b8860b;color:#fff}
th.ge{background:#6a5acd}
th.gmt{background:#d4935a;color:#fff;font-size:10.5px}
th.gma{background:#e8b87a;color:#5a3a00;font-size:10.5px}
tr.gh .g-s{background:#245a8c}
tr.gh .g-v{background:#2f7048}
tr.gh .g-r{background:#8a6508}
tr.gh .g-e{background:#5548b0}
tr.gh .g-m{background:#a36520}
.sig{display:inline-block;width:15px;height:15px;border-radius:50%;vertical-align:middle}
.s-g{background:#28a745;box-shadow:0 0 5px #28a74588}
.s-y{background:#ffc107;box-shadow:0 0 5px #ffc10788}
.s-r{background:#dc3545;box-shadow:0 0 5px #dc354588}
.s-x{background:#adb5bd}
.np{color:#28a745;font-weight:600}
.nn{color:#dc3545;font-weight:600}
td.mhv{background:#fffbe6 !important;font-weight:700;color:#7a5a00}
.footer-info{padding:6px 20px;font-size:11px;color:#666;background:#fff;border-top:1px solid#ddd}
.legend{display:inline-flex;gap:14px;align-items:center;margin-left:auto;font-size:11px}
.li{display:flex;align-items:center;gap:5px;color:#ccc}
.row-actions{display:flex;gap:6px;align-items:center}
.icon-btn{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:4px;cursor:pointer;transition:all .2s;border:1px solid;background:#fff;font-size:13px;text-decoration:none}
.icon-edit{color:#2e6da4;border-color:#2e6da4}
.icon-edit:hover{background:#2e6da4;color:#fff}
.icon-del{color:#dc3545;border-color:#dc3545}
.icon-del:hover{background:#dc3545;color:#fff}
</style>
</head>
<body>

<div class="top-nav">
    <h2>📊 누적 투자 실적 조회</h2>
    <a href="/">◀ 입력 페이지</a>
    <div class="legend">
        <div class="li"><span class="sig s-g"></span> 목표 초과</div>
        <div class="li"><span class="sig s-y"></span> 진행 중</div>
        <div class="li"><span class="sig s-r"></span> 미달성</div>
        <div class="li"><span class="sig s-x"></span> 미입력</div>
    </div>
</div>

<div class="filter-bar">
    <label>제품</label>
    <select id="fp" onchange="applyFilter()">
        <option value="">전체</option>
        <option>키친</option><option>빌트인쿠킹</option><option>리빙</option><option>부품</option><option>ES</option>
    </select>
    <label>법인</label>
    <select id="fc" onchange="applyFilter()">
        <option value="">전체</option>
        <option>KR</option><option>AI</option><option>AT</option><option>AZ</option><option>EG</option><option>IL_N</option><option>IL_P</option><option>IN_T</option><option>MN</option><option>MX</option><option>MZ</option><option>PN</option><option>RA</option><option>SR</option><option>TA</option><option>TH</option><option>TN</option><option>TR</option><option>VH</option><option>WR</option>
    </select>
    <label>투자유형</label>
    <select id="ft" onchange="applyFilter()">
        <option value="">전체</option><option>확장</option><option>경상</option>
    </select>
</div>

<div class="table-wrap">
<table id="mainTable">
<thead>
<tr class="gh">
    <th class="sc c0" rowspan="2" style="z-index:15"></th>
    <th class="sc c1" rowspan="2" style="z-index:15">제품</th>
    <th class="sc c2" rowspan="2" style="z-index:15">법인</th>
    <th class="sc c3" rowspan="2" style="z-index:15">투자유형</th>
    <th rowspan="2">투자항목</th>
    <th rowspan="2">투자목적</th>
    <th class="g-s" colspan="7">📅 투자 주요 일정</th>
    <th class="g-v" colspan="4">💰 투자절감</th>
    <th class="g-r" colspan="11">📊 절감 활동 및 실적</th>
    <th class="g-e" colspan="3">🎯 목표</th>
    <th class="g-m" colspan="48">📆 월별 절감 실적</th>
</tr>
<tr>
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
    <th class="gmt">26.01월<br>(목표)</th><th class="gma">26.01월<br>(실적)</th>
    <th class="gmt">26.02월<br>(목표)</th><th class="gma">26.02월<br>(실적)</th>
    <th class="gmt">26.03월<br>(목표)</th><th class="gma">26.03월<br>(실적)</th>
    <th class="gmt">26.04월<br>(목표)</th><th class="gma">26.04월<br>(실적)</th>
    <th class="gmt">26.05월<br>(목표)</th><th class="gma">26.05월<br>(실적)</th>
    <th class="gmt">26.06월<br>(목표)</th><th class="gma">26.06월<br>(실적)</th>
    <th class="gmt">26.07월<br>(목표)</th><th class="gma">26.07월<br>(실적)</th>
    <th class="gmt">26.08월<br>(목표)</th><th class="gma">26.08월<br>(실적)</th>
    <th class="gmt">26.09월<br>(목표)</th><th class="gma">26.09월<br>(실적)</th>
    <th class="gmt">26.10월<br>(목표)</th><th class="gma">26.10월<br>(실적)</th>
    <th class="gmt">26.11월<br>(목표)</th><th class="gma">26.11월<br>(실적)</th>
    <th class="gmt">26.12월<br>(목표)</th><th class="gma">26.12월<br>(실적)</th>
    <th class="gmt">27.01월<br>(목표)</th><th class="gma">27.01월<br>(실적)</th>
    <th class="gmt">27.02월<br>(목표)</th><th class="gma">27.02월<br>(실적)</th>
    <th class="gmt">27.03월<br>(목표)</th><th class="gma">27.03월<br>(실적)</th>
    <th class="gmt">27.04월<br>(목표)</th><th class="gma">27.04월<br>(실적)</th>
    <th class="gmt">27.05월<br>(목표)</th><th class="gma">27.05월<br>(실적)</th>
    <th class="gmt">27.06월<br>(목표)</th><th class="gma">27.06월<br>(실적)</th>
    <th class="gmt">27.07월<br>(목표)</th><th class="gma">27.07월<br>(실적)</th>
    <th class="gmt">27.08월<br>(목표)</th><th class="gma">27.08월<br>(실적)</th>
    <th class="gmt">27.09월<br>(목표)</th><th class="gma">27.09월<br>(실적)</th>
    <th class="gmt">27.10월<br>(목표)</th><th class="gma">27.10월<br>(실적)</th>
    <th class="gmt">27.11월<br>(목표)</th><th class="gma">27.11월<br>(실적)</th>
    <th class="gmt">27.12월<br>(목표)</th><th class="gma">27.12월<br>(실적)</th>
</tr>
</thead>
<tbody id="tableBody"></tbody>
</table>
</div>

<div class="footer-info" id="footerInfo">총 0건</div>

<script>
const DATA = {{ processed_json | safe }};
const MONTHS = {{ months_json | safe }};

console.log("데이터 로드:", DATA.length, "건");

function sig(r){
    const t=parseFloat(r[16])||0, a=parseFloat(r[17])||0;
    if(!t&&!a) return "s-x";
    if(a>=t&&a>0) return "s-g";
    if(a>0) return "s-y";
    return "s-r";
}
function nc(v){ const n=parseFloat(v); return isNaN(n)?"": n>0?"np":(n<0?"nn":""); }
function f(v){ return (v!=null&&v!=="")? v : "-"; }

function deleteRow(id){
    if(!confirm("정말 삭제하시겠습니까?")) return;
    fetch("/delete/"+id, {method:"POST"})
        .then(r=>r.json())
        .then(d=>{ if(d.success) location.reload(); });
}

function renderTable(data){
    const tb = document.getElementById("tableBody");
    let out = "";

    data.forEach(r => {
        const rid = r[0];
        const ma = r[31] || [];   // ✅ 월별 데이터
        let h = "<tr>";

        h += "<td class='sc c0'><div class='row-actions'>";
        h += "<a href='/edit/"+rid+"' class='icon-btn icon-edit' title='수정'>✏️</a>";
        h += "<button class='icon-btn icon-del' title='삭제' onclick='deleteRow("+rid+")'>🗑️</button>";
        h += "</div></td>";

        h += "<td class='sc c1'>"+f(r[2])+"</td>";
        h += "<td class='sc c2'>"+f(r[3])+"</td>";
        h += "<td class='sc c3'>"+f(r[1])+"</td>";
        h += "<td class='left'>"+f(r[5])+"</td>";
        h += "<td>"+f(r[4])+"</td>";

        h += "<td>"+f(r[6])+"</td><td>"+f(r[7])+"</td>";
        h += "<td>"+f(r[8])+"</td><td>"+f(r[9])+"</td>";
        h += "<td>"+f(r[10])+"</td><td>"+f(r[11])+"</td>";
        h += "<td class='left'>"+f(r[12])+"</td>";

        h += "<td>"+f(r[13])+"</td>";
        h += "<td>"+f(r[14])+"</td>";
        h += "<td>"+f(r[15])+"</td>";
        h += "<td>"+f(r[16])+"</td>";

        h += "<td>"+f(r[17])+"</td>";
        for(let i=18;i<=26;i++){
            h += "<td>"+f(r[i])+"</td>";
        }

        h += "<td class='act-cell'>"+f(r[28])+"</td>";

        const rt = r[29] != null && r[29] !== "-" ? r[29]+"%" : "-";
        const ra = r[30] != null && r[30] !== "-" ? r[30]+"%" : "-";
        h += "<td>"+rt+"</td>";
        h += "<td>"+ra+"</td>";
        h += "<td><span class='sig "+sig(r)+"'></span></td>";

        for(let i=0;i<ma.length;i++){
            h += "<td>"+(ma[i] || 0)+"</td>";
        }

        h += "</tr>";
        out += h;
    });

    tb.innerHTML = out;
    document.getElementById("footerInfo").textContent = "총 "+data.length+"건";
}

function applyFilter(){
    const fp=document.getElementById("fp").value;
    const fc=document.getElementById("fc").value;
    const ft=document.getElementById("ft").value;
    renderTable(DATA.filter(r=>{
        if(fp&&r[2]!==fp) return false;
        if(fc&&r[3]!==fc) return false;
        if(ft&&r[1]!==ft) return false;
        return true;
    }));
}

renderTable(DATA);
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


