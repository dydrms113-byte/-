from flask import Flask, request, render_template_string

app = Flask(__name__)

# ======================
# 공통 데이터
# ======================
PRODUCTS = ["키친", "빌쿠", "리빙", "ES", "부품"]

CORPORATIONS = [
    "KR","TR","MN","IL_N","IN_T","IL_P","RA","VH","PN","TA",
    "TH","MZ","WR","TN","EG","MX","SR","AZ","AT","AI"
]

INVEST_PURPOSES = [
    "신규라인",
    "자동화",
    "라인 개조",
    "Overhaul",
    "신모델 대응",
    "T/Time 향상",
    "고장 수리",
    "안전"
]

YEARS = [2024, 2025, 2026, 2027]
MONTHS = list(range(1, 13))


# ======================
# 메인 화면
# ======================
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>설비투자비한계돌파 실적 기입</title>
<style>
body { font-family: Arial; margin: 20px; }
h1 { font-size: 22px; margin-bottom: 15px; }

table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #999; padding: 6px; }
th { background: #e6e6e6; text-align: left; }

.section { background: #d9d9d9; font-weight: bold; }
select, input { width: 95%; padding: 4px; }
</style>
</head>

<body>

<h1>설비투자비한계돌파 실적 기입 (확장, 경상 투자)</h1>

<form method="post">

<table>

<!-- 투자 분류 -->
<tr class="section"><td colspan="4">투자 분류</td></tr>

<tr>
<td>제품</td>
<td>
<select name="product">
{% for p in products %}
<option>{{p}}</option>
{% endfor %}
</select>
</td>

<td>법인</td>
<td>
<select name="corporation">
{% for c in corporations %}
<option>{{c}}</option>
{% endfor %}
</select>
</td>
</tr>

<tr>
<td>투자항목</td>
<td><input name="investment_item"></td>

<td>투자목적</td>
<td>
<select name="investment_purpose">
{% for p in invest_purposes %}
<option>{{p}}</option>
{% endfor %}
</select>
</td>
</tr>

<!-- 투자 주요 일정 -->
<tr class="section"><td colspan="4">투자 주요 일정</td></tr>

{% for label in ["발주 목표","발주 실적","셋업 목표","셋업 실적","양산 목표","양산 실적"] %}
<tr>
<td>{{label}}</td>
<td>
<select>
{% for y in years %}
<option>{{y}}</option>
{% endfor %}
</select>
</td>

<td>월</td>
<td>
<select>
{% for m in months %}
<option>{{m}}</option>
{% endfor %}
</select>
</td>
</tr>
{% endfor %}

<tr>
<td>연기사유</td>
<td colspan="3"><input name="delay_reason"></td>
</tr>

</table>

<br>
<button type="submit">저장</button>

</form>

</body>
</html>
""",
products=PRODUCTS,
corporations=CORPORATIONS,
invest_purposes=INVEST_PURPOSES,
years=YEARS,
months=MONTHS
)

if __name__ == "__main__":
    app.run(debug=True)