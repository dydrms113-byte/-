from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "data.db"

# ======================
# DB 초기화
# ======================
def init_db():
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
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ======================
# Page 1 : 입력 페이지
# ======================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        f = request.form
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # 🔥 컬럼 29개 / 값 29개 정확히 일치
        c.execute("""
        INSERT INTO investment (
            invest_type, product, corporation, purpose, invest_item,
            order_target, order_actual, setup_target, setup_actual,
            mass_target, mass_actual, delay_reason,
            base_amount, order_price_target, order_price_actual,
            saving_target, saving_actual,
            reduce_1, reduce_2, reduce_3, reduce_4, reduce_5,
            reduce_6, reduce_7, reduce_8, reduce_9,
            saving_total,
            activity,
            created_at
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?
        )
        """, (
            f.get("invest_type"),
            f.get("product"),
            f.get("corporation"),
            f.get("purpose"),
            f.get("invest_item"),

            f.get("order_target"),
            f.get("order_actual"),
            f.get("setup_target"),
            f.get("setup_actual"),
            f.get("mass_target"),
            f.get("mass_actual"),
            f.get("delay_reason"),

            f.get("base_amount"),
            f.get("order_price_target"),
            f.get("order_price_actual"),
            f.get("saving_target"),
            f.get("saving_actual"),

            f.get("reduce_1"),
            f.get("reduce_2"),
            f.get("reduce_3"),
            f.get("reduce_4"),
            f.get("reduce_5"),
            f.get("reduce_6"),
            f.get("reduce_7"),
            f.get("reduce_8"),
            f.get("reduce_9"),

            f.get("saving_total"),
            f.get("activity"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("list_page"))

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>설비투자비한계돌파 실적 기입</title>
<style>
body { font-family: Arial; font-size: 13px; }
table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
th, td { border: 1px solid #999; padding: 6px; }
.section { background:#d9d9d9; font-weight:bold; }
input, select, textarea { width: 95%; }
::placeholder { color:#aaa; }
.nowrap { white-space: nowrap; }
.money input { min-width: 110px; }
</style>

<script>
function calcTotal() {
    let sum = 0;
    document.querySelectorAll(".reduce").forEach(el => {
        sum += Number(el.value) || 0;
    });
    document.getElementById("saving_total").value = sum.toFixed(1);
}
</script>
</head>

<body>

<h2>설비투자비한계돌파 실적 기입 (확장, 경상 투자)</h2>

<form method="post">

<table>
<tr class="section"><td colspan="6">투자 분류</td></tr>
<tr>
<td class="nowrap">투자 유형</td>
<td>
<select name="invest_type">
<option>확장</option>
<option>경상</option>
</select>
</td>
<td>제품</td>
<td>
<select name="product">
<option>키친</option>
<option>빌쿠</option>
<option>리빙</option>
</select>
</td>
<td>법인</td>
<td>
<select name="corporation">
<option>KR</option>
<option>TR</option>
<option>MX</option>
</select>
</td>
</tr>

<tr>
<td>투자목적</td>
<td colspan="2">
<select name="purpose">
<option>신규라인</option>
<option>자동화</option>
</select>
</td>
<td>투자항목</td>
<td colspan="2">
<input name="invest_item" placeholder="ex) 창원 선진화 오븐라인">
</td>
</tr>
</table>

<table>
<tr class="section"><td colspan="4">투자 주요 일정</td></tr>
<tr>
<td>발주 목표</td><td><input type="month" name="order_target"></td>
<td>발주 실적</td><td><input type="month" name="order_actual"></td>
</tr>
<tr>
<td>셋업 목표</td><td><input type="month" name="setup_target"></td>
<td>셋업 실적</td><td><input type="month" name="setup_actual"></td>
</tr>
<tr>
<td>양산 목표</td><td><input type="month" name="mass_target"></td>
<td>양산 실적</td><td><input type="month" name="mass_actual"></td>
</tr>
<tr>
<td>연기사유(발주, 양산)</td>
<td colspan="3"><input name="delay_reason"></td>
</tr>
</table>

<table>
<tr class="section"><td colspan="11">투자절감 실적</td></tr>

<tr class="money">
<td class="nowrap">Base 금액</td><td><input name="base_amount"></td>
<td>발주가 목표</td><td><input name="order_price_target"></td>
<td>발주가 실적</td><td><input name="order_price_actual"></td>
<td>절감 목표</td><td><input name="saving_target"></td>
<td>절감 실적</td><td><input name="saving_actual"></td>
</tr>

<tr>
<td>항목</td>
<td>1.신기술/신공법</td>
<td>2.염가형 부품</td>
<td>3.중국/Local 설비</td>
<td>4.중국/한국 Collabo</td>
<td>5.컨테이너 최소화</td>
<td>6.출장 인원 최소화</td>
<td>7.유휴설비</td>
<td>8.사양 최적화</td>
<td>9.기타</td>
<td>합계</td>
</tr>

<tr class="money">
<td class="nowrap">금액(억원)</td>
<td><input class="reduce" name="reduce_1" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_2" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_3" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_4" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_5" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_6" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_7" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_8" oninput="calcTotal()"></td>
<td><input class="reduce" name="reduce_9" oninput="calcTotal()"></td>
<td><input id="saving_total" name="saving_total" readonly></td>
</tr>

<tr>
<td>활동내용</td>
<td colspan="10">
<textarea name="activity" rows="4"></textarea>
</td>
</tr>
</table>

<button type="submit">저장</button>
&nbsp;&nbsp;
<a href="/list">조회</a>

</form>

</body>
</html>
""")

# ======================
# Page 2 : 조회 페이지
# ======================
@app.route("/list")
def list_page():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM investment ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>누적 실적 조회</title></head>
<body>
<h2>누적 투자 실적</h2>
<table border="1">
{% for r in rows %}
<tr>
{% for c in r %}
<td>{{ c }}</td>
{% endfor %}
</tr>
{% endfor %}
</table>
<br>
<a href="/">◀ 입력 페이지</a>
</body>
</html>
""", rows=rows)

if __name__ == "__main__":
    app.run(debug=True)