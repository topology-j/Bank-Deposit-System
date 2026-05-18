"""Generate draw.io ERD XML for bank deposit system."""
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import re

_id = [2]

def nid():
    v = _id[0]; _id[0] += 1; return str(v)

ROW_H = 26
HDR_H = 30

TABLE_STYLE = (
    "shape=table;startSize=30;container=1;collapsible=0;"
    "childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;"
    "align=center;resizeLast=1;fontSize=13;"
    "fillColor=#dae8fc;strokeColor=#6c8ebf;"
)
ROW_STYLE_BASE = (
    "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;"
    "collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];"
    "portConstraint=eastwest;fontSize=11;top=0;left=0;right=0;bottom=1;"
)
KEY_STYLE = (
    "shape=partialRectangle;connectable=0;fillColor=none;"
    "top=0;left=0;bottom=0;right=0;fontStyle=1;overflow=hidden;fontSize=10;"
)
COL_STYLE_NORMAL = (
    "shape=partialRectangle;connectable=0;fillColor=none;"
    "top=0;left=0;bottom=0;right=0;overflow=hidden;fontSize=11;"
)
COL_STYLE_PK = (
    "shape=partialRectangle;connectable=0;fillColor=none;"
    "top=0;left=0;bottom=0;right=0;overflow=hidden;fontStyle=5;fontSize=11;"
)
EDGE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;html=1;fontSize=11;"
    "endArrow=ERmandOne;startArrow=ERzeroToMany;"
    "rounded=1;orthogonalLoop=1;jettySize=auto;"
)
ONE_EDGE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;html=1;fontSize=11;"
    "endArrow=ERmandOne;startArrow=ERmandOne;"
    "rounded=1;orthogonalLoop=1;jettySize=auto;"
)

ROOT_EL = None

AUDIT_COLUMNS = [
    ("", "최초등록일시", "created_at", "TIMESTAMPTZ"),
    ("", "최초등록자ID", "created_by", "VARCHAR(100)"),
    ("", "최종수정일시", "updated_at", "TIMESTAMPTZ"),
    ("", "최종수정자ID", "updated_by", "VARCHAR(100)"),
]

AUDIT_COL_NAMES = {
    "created_at", "updated_at", "created_by", "updated_by",
    "first_registered_at", "first_registrant_identifier",
    "last_modified_at", "first_modifier_identifier",
}

def with_audit_columns(columns):
    base = [col for col in columns if col[2] not in AUDIT_COL_NAMES]
    return base + AUDIT_COLUMNS

def table_height(row_count):
    return HDR_H + row_count * ROW_H

def add_table(name, columns, x, y, width=400):
    columns = with_audit_columns(columns)
    height = HDR_H + len(columns) * ROW_H
    tid = nid()

    tc = ET.SubElement(ROOT_EL, "mxCell")
    tc.set("id", tid); tc.set("value", name)
    tc.set("style", TABLE_STYLE)
    tc.set("vertex", "1"); tc.set("parent", "1")
    g = ET.SubElement(tc, "mxGeometry")
    g.set("x", str(x)); g.set("y", str(y))
    g.set("width", str(width)); g.set("height", str(height))
    g.set("as", "geometry")

    col_ids = {}
    for i, (key_type, ko_name, col_name, data_type) in enumerate(columns):
        row_y = HDR_H + i * ROW_H
        rid = nid()

        if "PK" in key_type:
            row_fill = "fillColor=#fff2cc;strokeColor=#d6b656;"
        elif "FK" in key_type:
            row_fill = "fillColor=#d5e8d4;strokeColor=#82b366;"
        else:
            row_fill = "fillColor=none;"

        rc = ET.SubElement(ROOT_EL, "mxCell")
        rc.set("id", rid); rc.set("value", "")
        rc.set("style", ROW_STYLE_BASE + row_fill)
        rc.set("vertex", "1"); rc.set("parent", tid)
        rg = ET.SubElement(rc, "mxGeometry")
        rg.set("y", str(row_y)); rg.set("width", str(width))
        rg.set("height", str(ROW_H)); rg.set("as", "geometry")

        kc = ET.SubElement(ROOT_EL, "mxCell")
        kc.set("id", nid()); kc.set("value", key_type)
        kc.set("style", KEY_STYLE)
        kc.set("vertex", "1"); kc.set("parent", rid)
        kg = ET.SubElement(kc, "mxGeometry")
        kg.set("width", "50"); kg.set("height", str(ROW_H)); kg.set("as", "geometry")
        alt = ET.SubElement(kg, "mxRectangle")
        alt.set("width", "50"); alt.set("height", str(ROW_H)); alt.set("as", "alternateBounds")

        cc = ET.SubElement(ROOT_EL, "mxCell")
        cc.set("id", nid())
        cc.set("value", f"{ko_name} / {col_name} / {data_type}")
        cc.set("style", COL_STYLE_PK if "PK" in key_type else COL_STYLE_NORMAL)
        cc.set("vertex", "1"); cc.set("parent", rid)
        cg = ET.SubElement(cc, "mxGeometry")
        cg.set("x", "50"); cg.set("width", str(width - 50))
        cg.set("height", str(ROW_H)); cg.set("as", "geometry")
        alt2 = ET.SubElement(cg, "mxRectangle")
        alt2.set("width", str(width - 50)); alt2.set("height", str(ROW_H))
        alt2.set("as", "alternateBounds")

        # (tid, prop_y): 테이블 컨테이너 외벽에서 FK 컬럼 비례 위치로 연결
        col_ids[col_name] = (tid, (row_y + ROW_H / 2) / height)

    return col_ids


NOTE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffcc;strokeColor=#d6b656;"
    "fontSize=11;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6;arcSize=4;"
)

def add_note(x, y, width, height, html_text):
    line_count = len(re.findall(r"<br>", html_text)) + 1
    min_height = line_count * 18 + 26
    height = max(height, min_height)
    nc = ET.SubElement(ROOT_EL, "mxCell")
    nc.set("id", nid()); nc.set("value", html_text)
    nc.set("style", NOTE_STYLE)
    nc.set("vertex", "1"); nc.set("parent", "1")
    ng = ET.SubElement(nc, "mxGeometry")
    ng.set("x", str(x)); ng.set("y", str(y))
    ng.set("width", str(width)); ng.set("height", str(height))
    ng.set("as", "geometry")


def add_domain_box(label, x, y, width, height, fill_color="#ffffff", stroke_color="#cccccc"):
    nc = ET.SubElement(ROOT_EL, "mxCell")
    nc.set("id", nid()); nc.set("value", f"<b>{label}</b>")
    nc.set("style",
        f"rounded=1;whiteSpace=wrap;html=1;fontSize=15;fontStyle=1;"
        f"fillColor={fill_color};strokeColor={stroke_color};"
        f"opacity=30;verticalAlign=top;align=left;"
        f"spacingTop=10;spacingLeft=14;strokeWidth=2;"
    )
    nc.set("vertex", "1"); nc.set("parent", "1")
    ng = ET.SubElement(nc, "mxGeometry")
    ng.set("x", str(x)); ng.set("y", str(y))
    ng.set("width", str(width)); ng.set("height", str(height))
    ng.set("as", "geometry")


def add_edge(src, tgt, ex=None, ey=None, nx=None, ny=None, one_to_one=False, points=None):
    """
    src/tgt: col_ids 값인 (tid, prop_y) 튜플, 또는 plain tid 문자열.
    ex/nx: 0=왼쪽, 1=오른쪽, 0.5=중앙(위아래용).
    ey/ny: 명시 시 override; None이면 튜플의 prop_y(FK 컬럼 비례 위치) 사용.
    one_to_one: True이면 양쪽 ERmandOne (1:1 관계).
    points: [(x, y), ...] 경유점. 긴 선은 테이블 사이 빈 통로로 우회시킬 때 사용.
    """
    src_id, src_py = src if isinstance(src, tuple) else (src, 0.5)
    tgt_id, tgt_py = tgt if isinstance(tgt, tuple) else (tgt, 0.5)
    actual_ey = ey if ey is not None else src_py
    actual_ny = ny if ny is not None else tgt_py

    ec = ET.SubElement(ROOT_EL, "mxCell")
    ec.set("id", nid()); ec.set("value", "")
    style = ONE_EDGE_STYLE if one_to_one else EDGE_STYLE
    if ex is not None:
        style += f"exitX={ex};exitY={actual_ey};exitDx=0;exitDy=0;"
    if nx is not None:
        style += f"entryX={nx};entryY={actual_ny};entryDx=0;entryDy=0;"
    ec.set("style", style)
    ec.set("edge", "1"); ec.set("source", src_id); ec.set("target", tgt_id)
    ec.set("parent", "1")
    eg = ET.SubElement(ec, "mxGeometry")
    eg.set("relative", "1"); eg.set("as", "geometry")
    if points:
        arr = ET.SubElement(eg, "Array")
        arr.set("as", "points")
        for x, y in points:
            p = ET.SubElement(arr, "mxPoint")
            p.set("x", str(x)); p.set("y", str(y))


# ── Build XML ─────────────────────────────────────────────────────────────
model = ET.Element("mxGraphModel")
for k, v in [("dx","1422"),("dy","762"),("grid","1"),("gridSize","10"),
             ("guides","1"),("tooltips","1"),("connect","1"),("arrows","1"),
             ("fold","1"),("page","1"),("pageScale","1"),
             ("pageWidth","3300"),("pageHeight","6000"),("math","0"),("shadow","0")]:
    model.set(k, v)

root_xml = ET.SubElement(model, "root")
ROOT_EL = root_xml

c0 = ET.SubElement(ROOT_EL, "mxCell"); c0.set("id", "0")
c1 = ET.SubElement(ROOT_EL, "mxCell"); c1.set("id", "1"); c1.set("parent", "0")


# ══════════════════════════════════════════════════════════════════════════
# 레이아웃 상수 — 5열 레이아웃: products|subproducts|pir|dc|accounts
# ══════════════════════════════════════════════════════════════════════════
GAP = 40  # 테이블 간 수직 여백

# 행 수 (base 컬럼 + 4 audit, created_at/updated_at 제거 후)
PR_ROWS     = 22  # products
DP_ROWS     =  8  # deposit_products
SP_ROWS     =  9  # savings_products
SUBPRD_ROWS =  9  # subscription_products (product_id PK/FK, subscription_product_id 없음)
PJC_ROWS    =  7  # product_join_channels
PIR_ROWS    = 17  # product_interest_rates
DC_ROWS     = 39  # contracts
TG_ROWS     =  8  # target_groups
PTG_ROWS    =  6  # product_target_groups
CAR_ROWS    =  9  # contract_applied_rates
AC_ROWS     = 33  # accounts
IH_ROWS     = 20  # interest_history
ST_ROWS     = 15  # special_terms
PST_ROWS    =  8  # product_special_terms
CSTA_ROWS   = 14  # contract_special_term_agreements
DEPT_ROWS   = 10  # departments
TR_ROWS     = 52  # transactions
SPRH_ROWS   = 11  # subscription_payment_recognition_history

# 노트 높이 (add_note 자동 계산: line_count*18+26, 여유분 포함)
DP_NOTE_H   = 116  # brs=4
PR_NOTE_H   = 320  # brs=14 → min=296, 여유 24
PIR_NOTE_H  = 404  # brs=20
SP_NOTE_H   =  62  # brs=2
PJC_NOTE_H  =  98  # brs=4
DC_NOTE_H   = 760  # brs=38 → min=728, 여유 32
AC_NOTE_H   = 360  # brs=17 → min=332, 여유 28
IH_NOTE_H   = 420  # brs=20 → min=404, 여유 16
CAR_NOTE_H  = 300  # brs=13 → min=278, 여유 22
CSTA_NOTE_H = 160  # brs=8
DEPT_NOTE_H =  98  # brs=4
TR_NOTE_H   = 620  # brs=32
SPRH_NOTE_H =  80  # brs=2

# 테이블 너비
W1 = 480  # products
W2 = 420  # deposit/savings/subscription products
W3 = 420  # product_interest_rates
W4 = 460  # contracts
W5 = 440  # accounts

# 열 X 좌표 (각 열 너비 + 60px 간격 — 선이 테이블 사이를 지날 공간 확보)
COL_GAP = 60
COL1_X = 40
COL2_X = COL1_X + W1 + COL_GAP
COL3_X = COL2_X + W2 + COL_GAP
COL4_X = COL3_X + W3 + COL_GAP
COL5_X = COL4_X + W4 + COL_GAP

# ── Col1: products + note → target_groups → product_target_groups (세로 배치) ──
TG_Y     = 40 + table_height(PR_ROWS) + 20 + PR_NOTE_H + GAP
W_TG     = W1   # target_groups 너비 (products와 동일)
W_PTG    = W1   # product_target_groups 너비
PTG_X    = COL1_X
PTG_Y    = TG_Y + table_height(TG_ROWS) + GAP
COL1_BOT = PTG_Y + table_height(PTG_ROWS)

# ── Col2: dp(+note) → sp(+note) → subprd → pjc(+note) ─────────────────────
DP_Y     = 40
SP_Y     = DP_Y + table_height(DP_ROWS) + 20 + DP_NOTE_H + GAP
SUBPRD_Y = SP_Y + table_height(SP_ROWS) + 20 + SP_NOTE_H + GAP
PJC_Y    = SUBPRD_Y + table_height(SUBPRD_ROWS) + GAP
COL2_BOT = PJC_Y + table_height(PJC_ROWS) + 20 + PJC_NOTE_H

# ── Col3: pir+note → ih+note (수직으로 쌓기, 빈 공간 활용) ───────────────
PIR_Y  = 40
IH_Y   = PIR_Y + table_height(PIR_ROWS) + 20 + PIR_NOTE_H + GAP
COL3_BOT = IH_Y + table_height(IH_ROWS) + 20 + IH_NOTE_H  # IH_NOTE_H updated to 224

# ── Col4: deposit_contracts + note ────────────────────────────────────────
DC_Y     = 40
COL4_BOT = DC_Y + table_height(DC_ROWS) + 20 + DC_NOTE_H

# ── Col5: accounts + note ─────────────────────────────────────────────────
AC_Y     = 40
COL5_BOT = AC_Y + table_height(AC_ROWS) + 20 + AC_NOTE_H

# ── Row2 시작 Y ───────────────────────────────────────────────────────────
ROW2_Y = max(COL1_BOT, COL2_BOT, COL3_BOT, COL4_BOT, COL5_BOT) + GAP

# ── Row2: st(col1)+pst(col2)+csta(col3)+car(col4)+dept(col5) ──────────────
CAR_Y  = ROW2_Y
SPRH_Y = ROW2_Y + table_height(DEPT_ROWS) + 20 + DEPT_NOTE_H + GAP

ROW2_H = max(
    table_height(ST_ROWS),
    table_height(PST_ROWS),
    table_height(CSTA_ROWS) + 20 + CSTA_NOTE_H,
    table_height(CAR_ROWS) + 20 + CAR_NOTE_H,
    table_height(DEPT_ROWS) + 20 + DEPT_NOTE_H + GAP + table_height(SPRH_ROWS) + 20 + SPRH_NOTE_H,
)

# ── 거래 내역: accounts 오른쪽(Col6)에 Row1과 같은 높이로 배치 ───────────
TR_X = COL5_X + W5 + COL_GAP   # 2060 + 440 + 60 = 2560
TR_Y = 40

# ══════════════════════════════════════════════════════════════════════════
# 컬럼 형식: (key_type, 한글명, english_name, DATA_TYPE)
# ══════════════════════════════════════════════════════════════════════════

# ── 상품 (Col1) ───────────────────────────────────────────────────────────
pr = add_table("products  (상품)", [
    ("PK", "상품 ID",              "product_id",                   "BIGSERIAL"),
    ("",   "상품 유형",             "product_type",                 "VARCHAR(30)"),
    ("",   "상품명",               "product_name",                 "VARCHAR(200)"),
    ("",   "상품 설명",             "description",                  "TEXT"),
    ("FK", "상품 담당 부서 ID",     "department_id",                "BIGINT"),
    ("",   "기본 금리",             "base_interest_rate",           "NUMERIC(5,2)"),
    ("",   "우대 금리 조건 설명",    "preferential_rate_condition",  "TEXT"),
    ("",   "최소 가입 금액",         "min_join_amount",              "NUMERIC(18,2)"),
    ("",   "최대 가입 금액",         "max_join_amount",              "NUMERIC(18,2)"),
    ("",   "최소 계약 기간(월)",     "min_period_month",             "INT"),
    ("",   "최대 계약 기간(월)",     "max_period_month",             "INT"),
    ("",   "중도 해지 가능 여부",    "is_early_termination_allowed", "BOOLEAN"),
    ("",   "세금 우대 가능 여부",    "is_tax_benefit_available",     "BOOLEAN"),
    ("",   "자동 재가입 가능 여부",  "is_auto_renewal_available",    "BOOLEAN"),
    ("",   "실물 통장 발행 여부",    "is_passbook_issued",           "BOOLEAN"),
    ("",   "상품 출시일",           "released_at",                  "TEXT(8)"),
    ("",   "상품 종료일",           "ended_at",                     "TEXT(8)"),
    ("",   "상품 상태",             "product_status",               "VARCHAR(20)"),
    ("",   "생성 일시",             "created_at",                   "TIMESTAMPTZ"),
    ("",   "수정 일시",             "updated_at",                   "TIMESTAMPTZ"),
], x=COL1_X, y=40, width=W1)

add_note(COL1_X, 40 + table_height(PR_ROWS) + 20, W1, PR_NOTE_H,
    "<b>📌 product_type (상품 유형)</b><br>"
    "DEPOSIT: 예금 | SAVINGS: 적금 | SUBSCRIPTION: 청약<br>"
    "──────────────────────<br>"
    "<b>product_status (상품 상태)</b><br>"
    "SELLING: 판매 | SUSPENDED: 중단 | EXPIRED: 만료<br>"
    "──────────────────────<br>"
    "<b>가입 대상 그룹</b><br>"
    "target_groups ↔ product_target_groups (N:M) 참조<br>"
    "──────────────────────<br>"
    "※ 최고 금리 = 기본 금리 + SUM(product_interest_rates PREFERENTIAL)<br>"
    "※ 실제 고객 적용 우대 금리는 계약의 우대 금리 합산 (total_preferential_rate) 참조<br>"
    "──────────────────────<br>"
    "<b>is_auto_renewal_available (자동 재가입 가능 여부)</b><br>"
    "만기 후 자동 재가입 지원 여부. TRUE인 상품에 가입한 고객만 자동 재가입 신청 가능.<br>"
    "예금·적금 상품만 해당; 청약 상품은 항상 FALSE."
)

# ── 예금 상품 (Col2) ──────────────────────────────────────────────────────
dp = add_table("deposit_products  (예금 상품)", [
    ("PK", "예금 상품 ID",          "deposit_product_id",            "BIGSERIAL"),
    ("FK", "상품 ID",               "product_id",                    "BIGINT"),
    ("",   "예금 유형",             "deposit_type",                  "VARCHAR(20)"),
    ("",   "복리 여부",             "is_compound_interest",          "BOOLEAN"),
], x=COL2_X, y=DP_Y, width=W2)

add_note(COL2_X, DP_Y + table_height(DP_ROWS) + 20, W2, DP_NOTE_H,
    "<b>📌 deposit_type (예금 유형)</b><br>"
    "TERM: 정기예금 | DEMAND: 입출금예금<br>"
    "──────────────────────<br>"
    "<b>is_compound_interest (복리 여부)</b><br>"
    "TRUE: 복리 상품 | FALSE: 단리 상품"
)

# ── 적금 상품 (Col2) ──────────────────────────────────────────────────────
sp = add_table("savings_products  (적금 상품)", [
    ("PK", "적금 상품 ID",           "savings_product_id",            "BIGSERIAL"),
    ("FK", "상품 ID",               "product_id",                    "BIGINT"),
    ("",   "적금 유형",              "saving_type",                   "VARCHAR(20)"),
    ("",   "월 납입 최소 금액",       "monthly_payment_min_amount",    "NUMERIC(18,2)"),
    ("",   "월 납입 최대 금액",       "monthly_payment_max_amount",    "NUMERIC(18,2)"),
], x=COL2_X, y=SP_Y, width=W2)

add_note(COL2_X, SP_Y + table_height(SP_ROWS) + 20, W2, 62,
    "<b>📌 saving_type (적금 유형)</b><br>"
    "REGULAR: 정기 납입식 | FREE: 자유 납입식"
)

# ── 청약 상품 (Col2) ──────────────────────────────────────────────────────
subprd = add_table("subscription_products  (청약 상품)", [
    ("PK/FK", "상품 ID",            "product_id",                    "BIGINT"),
    ("",   "월 납입 금액",           "monthly_payment_amount",        "NUMERIC(18,2)"),
    ("",   "월 납입 최소 금액",       "min_monthly_payment",           "NUMERIC(18,2)"),
    ("",   "월 납입 최대 금액",       "max_monthly_payment",           "NUMERIC(18,2)"),
    ("",   "납입인정최대금액",        "max_recognized_payment_amount", "NUMERIC(18,2)"),
], x=COL2_X, y=SUBPRD_Y, width=W2)

# ── 상품 가입 방식 (Col2) ─────────────────────────────────────────────────
pjc = add_table("product_join_channels  (상품 가입 방식)", [
    ("PK", "상품가입방식ID", "product_join_channel_id", "BIGSERIAL"),
    ("FK", "상품ID",        "product_id",              "BIGINT"),
    ("",   "가입방식코드",   "join_channel_code",       "VARCHAR(20)"),
    ("",   "생성일시",       "created_at",              "TIMESTAMPTZ"),
], x=COL2_X, y=PJC_Y, width=W2)

add_note(COL2_X, PJC_Y + table_height(PJC_ROWS) + 20, W2, PJC_NOTE_H,
    "<b>📌 join_channel_code (가입방식코드)</b><br>"
    "BRANCH: 영업점 | WEB: 웹<br>"
    "MOBILE: 모바일 | TELL: 전화<br>"
    "ETC: 기타"
)

# ── 상품 금리 (Col3 상단) ─────────────────────────────────────────────────
pir = add_table("product_interest_rates  (상품 금리)", [
    ("PK", "금리 ID",          "rate_id",                "BIGSERIAL"),
    ("FK", "상품 ID",          "product_id",             "BIGINT"),
    ("",   "금리 유형",        "rate_type",              "VARCHAR(30)"),
    ("",   "하한 기간(월)",    "minimum_contract_period", "INT"),
    ("",   "상한 기간(월)",    "maximum_contract_period", "INT"),
    ("",   "하한 금액",        "minimum_join_amount",     "NUMERIC(18,2)"),
    ("",   "상한 금액",        "maximum_join_amount",     "NUMERIC(18,2)"),
    ("",   "금리",            "rate",                   "NUMERIC(5,2)"),
    ("",   "조건 설명",        "condition_description",  "TEXT"),
    ("",   "적용 시작일",      "effective_start_date",   "TEXT(8)"),
    ("",   "적용 종료일",      "effective_end_date",     "TEXT(8)"),
    ("",   "활성 여부",        "is_active",              "BOOLEAN"),
    ("",   "상태",            "status",                 "VARCHAR(20)"),
], x=COL3_X, y=PIR_Y, width=W3)

add_note(COL3_X, PIR_Y + table_height(PIR_ROWS) + 20, W3, 260,
    "<b>📌 rate_type (금리 유형)</b><br>"
    "BASE: 기간·금액 무관 단일 기본 금리<br>"
    "PERIOD_BASE: 가입 기간 구간별 기본 금리 (minimum/maximum_contract_period 사용)<br>"
    "PREFERENTIAL: 우대 금리<br>"
    "EARLY_TERMINATION: 중도 해지 금리 (minimum/maximum_contract_period 사용)<br>"
    "──────────────────────<br>"
    "<b>📌 minimum/maximum_contract_period (하한/상한 기간)</b><br>"
    "PERIOD_BASE: 가입 계약 기간(월) 구간 → 해당 구간 계약 시 이 금리 적용<br>"
    "EARLY_TERMINATION: 실제 보유 기간(월) 구간 → 중도 해지 시 이 금리 적용<br>"
    "예) PERIOD_BASE | 하한 12·상한 24 → 12~24개월 계약 기본 금리<br>"
    "──────────────────────<br>"
    "<b>📌 minimum/maximum_join_amount (하한/상한 금액)</b><br>"
    "금액 구간 기준 금리 적용 시 사용 (NULL이면 해당 기준 없음)<br>"
    "예) 하한 1,000,000·상한 5,000,000 → 100만~500만 원 가입 시 이 금리 적용<br>"
    "──────────────────────<br>"
    "<b>📌 effective_start_date / effective_end_date (적용 시작일/종료일)</b><br>"
    "해당 금리의 유효 기간. effective_end_date가 NULL이면 현재 유효.<br>"
    "금리 변경 시 기존 행을 수정하지 않음:<br>"
    "&nbsp;&nbsp;① 기존 행에 effective_end_date 입력 → ② 새 금리 행 추가<br>"
    "예) 기본금리 2.50% | 시작일 20260101 | 종료일 20260630<br>"
    "&nbsp;&nbsp;&nbsp;기본금리 2.80% | 시작일 20260701 | 종료일 NULL (현재 유효)"
)

# ── 계약 (Col4) ─────────────────────────────────────────────────────
dc = add_table("contracts  (계약)", [
    ("PK", "계약 ID",          "contract_id",                "BIGSERIAL"),
    ("",   "계약 번호",         "contract_number",            "VARCHAR(50)"),
    ("FK", "고객 ID",           "customer_id",                "VARCHAR(30)"),
    ("FK", "상품 ID",           "product_id",                 "BIGINT"),
    ("",   "월납 여부",         "is_monthly_payment",         "BOOLEAN"),
    ("",   "총 납입 횟수",      "payment_count_total",        "INT"),
    ("",   "매월 납입일",       "monthly_payment_day",        "VARCHAR(6)"),
    ("",   "가입 금액",         "join_amount",                "NUMERIC(18,2)"),
    ("",   "계약 기본 금리",    "contract_interest_rate",       "NUMERIC(5,2)"),
    ("",   "우대 금리 합산",    "total_preferential_rate",      "NUMERIC(5,2)"),
    ("",   "최종 적용 금리",    "final_interest_rate",          "NUMERIC(5,2)"),
    ("",   "세제 혜택 유형",    "tax_benefit_type",             "VARCHAR(30)"),
    ("",   "적용 세율",         "applied_tax_rate",             "NUMERIC(5,2)"),
    ("",   "만기 예상 이자 금액","expected_interest_amount",     "NUMERIC(18,2)"),
    ("",   "계약 기간(개월)",   "contract_period_month",        "INT"),
    ("",   "계약 시작일",       "started_at",                 "TEXT(8)"),
    ("",   "계약 만기일",       "maturity_at",                "TEXT(8)"),
    ("",   "계약 해지일",       "terminated_at",              "TEXT(8)"),
    ("",   "계약 해지 사유",    "termination_reason",         "VARCHAR(200)"),
    ("",   "자동 재가입 여부",   "is_auto_renewal",            "BOOLEAN"),
    ("",   "자동 이체 사용 여부", "auto_transfer_enabled",      "BOOLEAN"),
    ("",   "자동 이체일",       "auto_transfer_day",          "INT"),
    ("",   "계약 상태",         "contract_status",            "VARCHAR(20)"),
    ("",   "상태 변경 일시",     "status_changed_at",              "TEXT(8)"),
    ("",   "가입 채널",         "join_channel",                   "VARCHAR(20)"),
    ("FK", "가입 지점 ID",     "branch_id",                      "BIGINT"),
    ("",   "가입 지점 코드",    "branch_code",                    "VARCHAR(20)"),
    ("",   "가입 지점명",      "branch_name",                    "VARCHAR(100)"),
    ("FK", "담당자 ID",        "manager_id",                     "BIGINT"),
    ("",   "담당자명",         "manager_name",                   "VARCHAR(100)"),
    ("",   "대리 가입 여부",    "is_proxy_joined",                "BOOLEAN"),
    ("",   "위임장 확인 여부",  "is_power_of_attorney_verified",  "BOOLEAN"),
    ("",   "위임장 파일 URL",  "power_of_attorney_file_url",     "VARCHAR(500)"),
    ("",   "약관 파일 URL",   "terms_file_url",                 "VARCHAR(500)"),
    ("",   "계약서 파일 URL", "contract_file_url",              "VARCHAR(500)"),
    ("",   "생성 일시",         "created_at",                     "TIMESTAMPTZ"),
    ("",   "수정 일시",         "updated_at",                     "TIMESTAMPTZ"),
], x=COL4_X, y=DC_Y, width=W4)

add_note(COL4_X, DC_Y + table_height(DC_ROWS) + 20, W4, DC_NOTE_H,
    "<b>📌 contracts (구 deposit_contracts) — 예금·적금·청약 계약 통합 관리</b><br>"
    "product_type(DEPOSIT/SAVINGS/SUBSCRIPTION)으로 유형 구분; 테이블 통합.<br>"
    "──────────────────────<br>"
    "<b>📌 contract_id vs contract_number</b><br>"
    "contract_id: DB 내부 PK/FK 연결용 (시스템 내부 식별자)<br>"
    "contract_number: 실제 업무/고객 조회용<br>"
    "&nbsp;&nbsp;→ 예금 가입 증서, 고객센터, 인터넷뱅킹<br>"
    "──────────────────────<br>"
    "<b>join_channel (가입 채널)</b><br>"
    "BRANCH: 영업점 | WEB: 웹 | MOBILE: 모바일<br>"
    "TELL: 전화 | ETC: 기타<br>"
    "product_join_channels.join_channel_code와 동일한 값 체계<br>"
    "&nbsp;&nbsp;→ BRANCH일 때 branch_id, branch_code, branch_name 값 존재<br>"
    "──────────────────────<br>"
    "<b>contract_status (계약 상태)</b><br>"
    "ACTIVE: 정상 유지 | MATURED: 만기 완료<br>"
    "TERMINATED: 중도 해지 | SUSPENDED: 거래 정지<br>"
    "──────────────────────<br>"
    "<b>세제 혜택 유형 (tax_benefit_type)</b><br>"
    "GENERAL: 일반과세 15.4% | NON_TAXABLE: 비과세 0%<br>"
    "REDUCED_TAX: 세금우대 9.9%<br>"
    "──────────────────────<br>"
    "<b>금리 구조</b><br>"
    "계약 기본 금리 (contract_interest_rate): 가입 당시 확정 기본 금리 (%)<br>"
    "우대 금리 합산 (total_preferential_rate): contract_applied_rates.applied_rate 합산 (%)<br>"
    "&nbsp;&nbsp;→ 우대 금리 적용 여부는 contract_applied_rates 행 존재 여부로 확인<br>"
    "최종 적용 금리 (final_interest_rate): 기본 금리 + 우대 금리 합산 최종 금리 (%)<br>"
    "──────────────────────<br>"
    "<b>자동 재가입 (is_auto_renewal)</b><br>"
    "만기 도래 시 고객 별도 신청 없이 동일 금액·기간으로 새 계약 자동 생성<br>"
    "※ 재가입 시점의 금리가 새로 적용됨 (최초 계약 금리와 다를 수 있음)<br>"
    "※ 예금·적금만 해당, 청약은 자동 재가입 불가<br>"
    "──────────────────────<br>"
    "<b>📌 청약 상품 1인 1계좌 제한 (업무 규칙)</b><br>"
    "SUBSCRIPTION 상품은 고객당 1개만 가입 가능.<br>"
    "DB 제약이 아닌 앱 레벨 검증으로 처리:<br>"
    "계약 생성 시 customer_id 기준으로 products 조인 후<br>"
    "product_type = SUBSCRIPTION 계약 존재 여부 확인 → 존재 시 가입 거부.<br>"
    "※ product_type은 products 테이블에서 조인으로 확인; 계약 테이블에 중복 저장 안 함"
)

# ── 계좌 (Col4) ───────────────────────────────────────────────────────────
ac = add_table("accounts  (계좌)", [
    ("PK", "계좌 ID",          "account_id",                "BIGSERIAL"),
    ("",   "계좌 번호",         "account_number",            "VARCHAR(30)"),
    ("FK", "고객 ID",           "customer_id",               "VARCHAR(30)"),
    ("FK", "계약 ID",           "contract_id",               "BIGINT"),
    ("",   "계좌 유형",         "account_type",              "VARCHAR(30)"),
    ("",   "적금 유형",         "saving_type",               "VARCHAR(20)"),
    ("",   "은행 코드",         "bank_code",                 "VARCHAR(10)"),
    ("",   "계좌 별명",         "account_alias",             "VARCHAR(100)"),
    ("",   "잔액",             "balance",                   "NUMERIC(18,2)"),
    ("",   "누적 납입 금액",    "total_paid_amount",         "NUMERIC(18,2)"),
    ("",   "총 이자 금액",      "total_interest_amount",     "NUMERIC(18,2)"),
    ("",   "마지막 거래 일시", "last_transaction_at",       "TIMESTAMPTZ"),
    ("",   "마지막 이자 지급 일시","last_interest_paid_at",  "TIMESTAMPTZ"),
    ("",   "통화",             "currency",                  "CHAR(3)"),
    ("",   "계좌 비밀번호",     "account_password",          "VARCHAR(255)"),
    ("",   "1일 출금 한도액",    "daily_withdraw_limit",      "NUMERIC(18,2)"),
    ("",   "1일 출금 횟수",      "daily_withdraw_count_limit","INT"),
    ("",   "ATM 출금 한도",     "atm_withdraw_limit",        "NUMERIC(18,2)"),
    ("",   "출금 가능 여부",    "is_withdrawable",           "BOOLEAN"),
    ("",   "인터넷 뱅킹 여부", "is_online_banking_enabled",  "BOOLEAN"),
    ("",   "모바일 뱅킹 여부", "is_mobile_banking_enabled",  "BOOLEAN"),
    ("",   "폰뱅킹 여부",     "is_phone_banking_enabled",   "BOOLEAN"),
    ("",   "계좌 상태",         "account_status",            "VARCHAR(20)"),
    ("",   "개설 일시",         "opened_at",                 "TEXT(8)"),
    ("",   "만기 일시",         "maturity_at",               "TEXT(8)"),
    ("",   "휴면 전환 일시",     "dormant_at",                "TEXT(8)"),
    ("",   "휴면 해제 일시",    "dormant_released_at",       "TEXT(8)"),
    ("",   "해지 일시",         "closed_at",                 "TEXT(8)"),
    ("",   "상태 변경 일시",     "status_changed_at",         "TEXT(8)"),
    ("",   "생성 일시",         "created_at",                "TIMESTAMPTZ"),
    ("",   "수정 일시",         "updated_at",                "TIMESTAMPTZ"),
], x=COL5_X, y=AC_Y, width=W5)

add_note(COL5_X, AC_Y + table_height(AC_ROWS) + 20, W5, 278,
    "<b>📌 account_type (계좌 유형)</b><br>"
    "DEPOSIT: 예금 계좌 | SAVINGS: 적금 계좌 | SUBSCRIPTION: 청약 계좌<br>"
    "contracts.product_type과 동일한 값 체계 (계약 생성 시 자동 설정)<br>"
    "──────────────────────<br>"
    "<b>saving_type (적금 유형 — account_type=SAVINGS일 때만 유효)</b><br>"
    "REGULAR: 정기 납입식 | FREE: 자유 납입식 | 그 외 NULL<br>"
    "──────────────────────<br>"
    "<b>account_status (계좌 상태)</b><br>"
    "ACTIVE: 정상 운영 중<br>"
    "DORMANT: 휴면 (장기 미사용)<br>"
    "SUSPENDED: 거래 정지 (이상 감지 등)<br>"
    "CLOSED: 해지 완료<br>"
    "──────────────────────<br>"
    "<b>opened_at (계좌 개설 일시) vs created_at (DB 등록 일시)</b><br>"
    "opened_at: 실제 계좌 개설 업무 시각 (고객/업무 기준)<br>"
    "created_at: DB 저장 시스템 시각<br>"
    "&nbsp;&nbsp;→ 배치/이관 시 opened_at과 다를 수 있음"
)

# ── 이자 내역 (Row2, Col1) ────────────────────────────────────────────────
ih = add_table("interest_history  (이자 내역)", [
    ("PK", "이자 ID",          "interest_id",                     "BIGSERIAL"),
    ("FK", "계약 ID",          "contract_id",                     "BIGINT"),
    ("FK", "계좌 ID",          "account_id",                      "BIGINT"),
    ("",   "적용 금리",        "applied_interest_rate",           "NUMERIC(5,2)"),  # 지급 시점 금리 스냅샷
    ("",   "이자 계산 시작일",  "interest_calculation_start_date", "TEXT(8)"),
    ("",   "이자 계산 종료일",  "interest_calculation_end_date",   "TEXT(8)"),
    ("",   "이자 발생 일시",    "interest_occurred_at",            "TIMESTAMPTZ"),  # TEXT(8)→TIMESTAMPTZ
    ("",   "이자 금액",        "interest_amount",                 "NUMERIC(18,2)"),
    ("",   "세제 혜택 유형",    "tax_benefit_type",                "VARCHAR(30)"),
    ("",   "적용 세율",        "applied_tax_rate",                "NUMERIC(5,4)"),
    ("",   "세전 이자 금액",    "interest_before_tax",             "NUMERIC(18,2)"),
    ("",   "이자소득세 금액",   "interest_tax_amount",             "NUMERIC(18,2)"),
    ("",   "지방소득세 금액",   "local_income_tax_amount",         "NUMERIC(18,2)"),
    ("",   "세후 이자 금액",    "interest_after_tax",              "NUMERIC(18,2)"),
    ("",   "이자 발생 사유",    "interest_reason",                 "VARCHAR(30)"),
    ("",   "이자 지급 일시",    "interest_paid_at",                "TIMESTAMPTZ"),  # TEXT(8)→TIMESTAMPTZ
], x=COL3_X, y=IH_Y, width=W3)

add_note(COL3_X, IH_Y + table_height(IH_ROWS) + 20, W3, 224,
    "<b>📌 interest_history — Source of Truth: 이자 지급</b><br>"
    "1행 = 1회 이자 지급 이벤트. 지급 후 불변.<br>"
    "──────────────────────<br>"
    "<b>interest_reason (이자 발생 사유)</b><br>"
    "REGULAR_INTEREST: 정기 이자 (월별 지급)<br>"
    "MATURITY_INTEREST: 만기 이자 (만기 시 일괄 지급)<br>"
    "BONUS_INTEREST: 우대 금리 이자 (조건 충족 시 추가)<br>"
    "──────────────────────<br>"
    "<b>세제 처리 흐름</b><br>"
    "interest_before_tax: 세전 이자<br>"
    "interest_tax_amount: 이자소득세 (세전×14%)<br>"
    "local_income_tax_amount: 지방소득세 (이자소득세×10%)<br>"
    "interest_after_tax: 실제 지급액 (source of truth)<br>"
    "──────────────────────<br>"
    "<b>누적 이자 조회</b><br>"
    "SUM(interest_after_tax) WHERE contract_id = ?<br>"
    "total_interest_amount 컬럼 없음 — 계산으로 도출<br>"
    "──────────────────────<br>"
    "<b>applied_interest_rate (적용 금리)</b><br>"
    "지급 시점 확정 금리 스냅샷 (contracts.final_interest_rate와<br>"
    "동일하나 이자 건별 독립 보관 — 재계산 없이 검증 가능)"
)

# ── 수신 특약 (Row2, Col1) ────────────────────────────────────────────────
st = add_table("special_terms  (수신 특약)", [
    ("PK", "특약 ID",          "special_term_id",       "BIGSERIAL"),
    ("",   "특약명",           "special_term_name",     "VARCHAR(200)"),
    ("",   "특약 내용",         "special_term_content",  "TEXT"),
    ("",   "특약 요약",         "special_term_summary",  "TEXT"),
    ("",   "필수 여부",         "is_required",           "BOOLEAN"),
    ("",   "전자 동의 가능 여부","is_electronic_agreement_allowed","BOOLEAN"),
    ("",   "특약 버전",         "special_term_version",  "VARCHAR(20)"),
    ("",   "특약 시작일",       "started_at",            "TEXT(8)"),
    ("",   "특약 종료일",       "ended_at",              "TEXT(8)"),
    ("",   "상태",             "status",                "VARCHAR(20)"),
    ("",   "상태 변경 일시",     "status_changed_at",     "TEXT(8)"),
], x=COL1_X, y=ROW2_Y, width=W1)

# ── 상품 특약 연결 (Row2, Col3) ───────────────────────────────────────────
pst = add_table("product_special_terms  (수신 상품 특약 연결)", [
    ("PK", "연결 ID",   "product_special_term_id", "BIGSERIAL"),
    ("FK", "상품 ID",   "product_id",              "BIGINT"),
    ("FK", "특약 ID",   "special_term_id",         "BIGINT"),
    ("",   "필수 여부", "is_required",             "BOOLEAN"),
], x=COL2_X, y=ROW2_Y, width=W2)

# ── 특약 동의 (Row2, Col3) ────────────────────────────────────────────────
csta = add_table("contract_special_term_agreements  (수신 특약 동의)", [
    ("PK", "동의 ID",       "special_agreement_id",     "BIGSERIAL"),
    ("FK", "계약 ID",       "contract_id",              "BIGINT"),
    ("FK", "특약 ID",       "special_term_id",          "BIGINT"),
    ("",   "동의 여부",     "is_agreed",                "BOOLEAN"),
    ("",   "동의 일시",     "agreed_at",                "TEXT(8)"),
    ("",   "동의 IP 주소",   "agreement_ip_address",     "VARCHAR(45)"),
    ("",   "동의 기기 정보", "agreement_device_info",    "VARCHAR(255)"),
    ("",   "전자 서명 여부", "is_electronic_signed",     "BOOLEAN"),
    ("",   "동의 철회 여부", "is_agreement_withdrawn",   "BOOLEAN"),
    ("",   "동의 철회 일시", "agreement_withdrawn_at",   "TEXT(8)"),
], x=COL3_X, y=ROW2_Y, width=W3)

add_note(COL3_X, ROW2_Y + table_height(CSTA_ROWS) + 20, W3, 160,
    "<b>📌 동의 IP 주소 (agreement_ip_address) / 동의 기기 정보 (agreement_device_info)</b><br>"
    "수신 특약 동의 테이블에만 IP·기기 정보를 저장하는 이유:<br>"
    "특약 동의는 개인정보처리방침·약관 등 법적 효력이 있는 동의 행위로,<br>"
    "전자서명법·금융소비자보호법에 따라 동의 사실을 입증할 수 있어야 함.<br>"
    "동의 시점의 IP 주소와 기기 정보를 기록해 부인 방지(non-repudiation) 근거 확보.<br>"
    "일반 거래(계약 생성·이자 지급 등)는 이 같은 법적 증명 요건이 없으므로 불필요."
)

# ── 계약 우대 금리 적용 내역 (Row2, Col4) ────────────────────────────────
car = add_table("contract_applied_rates  (계약 우대 금리 적용 내역)", [
    ("PK", "적용 내역 ID",   "applied_rate_id",       "BIGSERIAL"),
    ("FK", "계약 ID",        "contract_id",           "BIGINT"),
    ("FK", "금리 정책 ID",   "rate_id",               "BIGINT"),        # → product_interest_rates
    ("",   "적용 금리",      "applied_rate",          "NUMERIC(5,2)"),  # 계약 체결 시 확정 스냅샷 (불변)
    ("",   "조건 달성 여부", "condition_verified_yn", "BOOLEAN"),       # 우대 금리 조건 충족 확인
], x=COL4_X, y=CAR_Y, width=W4)

add_note(COL4_X, CAR_Y + table_height(CAR_ROWS) + 20, W4, 152,
    "<b>📌 contract_applied_rates — 우대 금리 스냅샷</b><br>"
    "계약 체결 시 적용된 우대 금리를 건별로 기록. 이후 불변.<br>"
    "──────────────────────<br>"
    "<b>금리 계산 구조</b><br>"
    "contracts.contract_interest_rate: 기본 금리 (확정)<br>"
    "SUM(applied_rate) 이 테이블: 우대 금리 합산<br>"
    "contracts.final_interest_rate = 기본 + 우대 합산<br>"
    "──────────────────────<br>"
    "<b>rate_id FK 용도</b><br>"
    "product_interest_rates 금리 정책 참조 (어떤 조건의 우대였는지)<br>"
    "applied_rate는 계약 시점 스냅샷 — PIR 변경에 영향 없음<br>"
    "──────────────────────<br>"
    "<b>condition_verified_yn (조건 달성 여부)</b><br>"
    "우대 금리 조건을 실제로 충족했는지 확인 여부"
)

# ── 부서 (Row2, Col5) ─────────────────────────────────────────────────────
dept = add_table("departments  (부서)", [
    ("PK", "부서 ID",       "department_id",        "BIGSERIAL"),
    ("",   "부서 코드",     "department_code",      "VARCHAR(50)"),
    ("",   "부서명",       "department_name",      "VARCHAR(100)"),
    ("FK", "상위 부서 ID",   "parent_department_id", "BIGINT"),
    ("",   "부서 유형",     "department_type",      "VARCHAR(30)"),
    ("",   "사용 여부",     "is_active",            "BOOLEAN"),
    ("",   "생성 일시",     "created_at",           "TIMESTAMPTZ"),
    ("",   "수정 일시",     "updated_at",           "TIMESTAMPTZ"),
], x=COL5_X, y=ROW2_Y, width=W5)

add_note(COL5_X, ROW2_Y + table_height(DEPT_ROWS) + 20, W5, 98,
    "<b>📌 department_type (부서 유형)</b><br>"
    "PRODUCT: 상품(수신/청약) | SALES: 영업<br>"
    "OPERATION: 운영 | RISK: 리스크 | IT: IT"
)

# ── 청약 납입 인정 이력 (Row2, Col5 하단) ────────────────────────────────
sprh = add_table("subscription_payment_recognition_history  (청약 납입 인정 이력)", [
    ("PK", "인정이력ID",   "recognition_id",     "BIGSERIAL"),
    ("FK", "계약ID",       "contract_id",         "BIGINT"),
    ("",   "실제납입금액",  "payment_amount",      "NUMERIC(18,2)"),
    ("",   "인정금액",     "recognized_amount",   "NUMERIC(18,2)"),
    ("",   "납입월",       "payment_month",       "VARCHAR(6)"),
    ("",   "인정일시",     "recognized_at",       "TIMESTAMPTZ"),
    ("",   "인정상태",     "recognition_status",  "VARCHAR(20)"),
    ("",   "생성일시",     "created_at",          "TIMESTAMPTZ"),
], x=COL5_X, y=SPRH_Y, width=W5)

add_note(COL5_X, SPRH_Y + table_height(SPRH_ROWS) + 20, W5, SPRH_NOTE_H,
    "<b>📌 recognition_status (인정상태)</b><br>"
    "RECOGNIZED: 인정 완료 | PARTIAL: 일부 인정<br>"
    "REJECTED: 인정 거부 | PENDING: 검토 중"
)


# ── 가입 대상 그룹 (Col1 아래, products 노트 바로 아래) ──────────────────────
tg = add_table("target_groups  (가입 대상 그룹)", [
    ("PK", "대상 그룹 ID",   "target_group_id",   "BIGSERIAL"),
    ("",   "대상 그룹명",     "target_group_name", "VARCHAR(100)"),
    ("",   "설명",           "description",       "TEXT"),
    ("",   "활성 여부",       "is_active",         "BOOLEAN"),
    ("",   "생성 일시",       "created_at",        "TIMESTAMPTZ"),
    ("",   "수정 일시",       "updated_at",        "TIMESTAMPTZ"),
], x=COL1_X, y=TG_Y, width=W_TG)

ptg = add_table("product_target_groups  (상품 가입 대상)", [
    ("FK", "상품 ID",       "product_id",      "BIGINT"),
    ("FK", "대상 그룹 ID",  "target_group_id", "BIGINT"),
    ("",   "생성 일시",      "created_at",      "TIMESTAMPTZ"),
], x=PTG_X, y=PTG_Y, width=W_PTG)

# ── FK 관계 엣지 ──────────────────────────────────────────────────────────
# 세부상품 → 상품 (Col2→Col1: 세부상품 왼쪽 출발 → 상품 오른쪽 진입)
add_edge(dp["product_id"],     pr["product_id"],   ex=0, nx=1)
add_edge(sp["product_id"],     pr["product_id"],   ex=0, nx=1)
add_edge(subprd["product_id"], pr["product_id"],   ex=0, nx=1, one_to_one=True)
add_edge(pjc["product_id"],    pr["product_id"],   ex=0, nx=1)
# 금리 → 상품 (Col3→Col1: 왼쪽 출발 → 오른쪽 진입)
add_edge(pir["product_id"],    pr["product_id"],   ex=0, nx=1)
# 계약 → 상품 (Col4→Col1: 왼쪽 출발 → 오른쪽 진입)
add_edge(dc["product_id"],     pr["product_id"],   ex=0, nx=1)
# 계좌 → 계약 (Col5→Col4: 계좌 왼쪽 출발 → 계약 오른쪽 진입)
add_edge(ac["contract_id"],    dc["contract_id"],  ex=0, nx=1)
# 계약 우대 금리 → 계약 (Row2Col4 ↑ Row1Col4: 위 출발 → 아래 진입, 동일 열)
add_edge(car["contract_id"],   dc["contract_id"],  ex=0.5, ey=0, nx=0.5, ny=1)
# 계약 우대 금리 → 금리 (Row2Col4→Row1Col3: 왼쪽 출발 → 오른쪽 진입)
add_edge(car["rate_id"],       pir["rate_id"],     ex=0, nx=1)
# 이자 내역 → 계약 (Col3→Col4: 오른쪽 출발 → 왼쪽 진입)
add_edge(ih["contract_id"],    dc["contract_id"],  ex=1, nx=0)
# 이자 내역 → 계좌 (Col3→Col5: 오른쪽 출발 → 왼쪽 진입)
add_edge(
    ih["account_id"], ac["account_id"], ex=1, nx=0,
    points=[
        (COL3_X + W3 + COL_GAP / 2, ROW2_Y - 20),
        (COL5_X - COL_GAP / 2, ROW2_Y - 20),
    ],
)
# 상품 특약 연결 → 상품 (Row2Col2→Row1Col1: 왼쪽 출발 → 오른쪽 진입)
add_edge(pst["product_id"],        pr["product_id"],       ex=0, nx=1)
# 상품 특약 연결 → 특약 (Row2Col2→Row2Col1: 왼쪽 출발 → 오른쪽 진입)
add_edge(pst["special_term_id"],   st["special_term_id"],  ex=0, nx=1)
# 특약 동의 → 계약 (Row2Col3→Row1Col4: 오른쪽 출발 → 왼쪽 진입)
add_edge(csta["contract_id"],      dc["contract_id"],      ex=1, nx=0)
# 특약 동의 → 특약 (Row2Col3→Row2Col1: 왼쪽 출발 → 오른쪽 진입)
add_edge(csta["special_term_id"],  st["special_term_id"],  ex=0, nx=1)
# 부서 자기 참조 (오른쪽 우회)
add_edge(dept["parent_department_id"], dept["department_id"], ex=1, nx=1)
# 상품 → 부서 (Row1Col1→Row2Col5: 오른쪽 출발 → 왼쪽 진입)
add_edge(
    pr["department_id"], dept["department_id"], ex=1, nx=0,
    points=[
        (COL1_X + W1 + COL_GAP / 2, ROW2_Y - 20),
        (COL5_X - COL_GAP / 2, ROW2_Y - 20),
    ],
)
# 상품 가입 대상 → 상품 (위 출발 → 아래 진입)
add_edge(ptg["product_id"],      pr["product_id"],           ex=0.5, ey=0, nx=0.5, ny=1)
# 상품 가입 대상 → 대상 그룹 (위 출발 → 아래 진입, 세로 배치)
add_edge(ptg["target_group_id"], tg["target_group_id"],      ex=0.5, ey=0, nx=0.5, ny=1)


# ── 거래 내역 (Row3, Col1~2) ──────────────────────────────────────────
tr = add_table("transactions  (거래 내역)", [
    # ── 공통 ──────────────────────────────────────────────────────────────
    ("PK", "거래 ID",              "transaction_id",              "BIGSERIAL"),
    ("",   "거래 번호",             "transaction_number",          "VARCHAR(50)"),
    ("FK", "계좌 ID",              "account_id",                  "BIGINT"),       # NOT NULL
    ("FK", "계약 ID",              "contract_id",                 "BIGINT"),       # NULL 허용
    ("",   "거래 유형",             "transaction_type",            "VARCHAR(30)"),  # NOT NULL
    ("",   "입출금 구분",           "direction_type",              "VARCHAR(10)"),  # NOT NULL IN/OUT
    ("",   "거래 금액",             "amount",                      "NUMERIC(18,2)"),
    ("",   "거래 전 잔액",          "balance_before",              "NUMERIC(18,2)"),
    ("",   "거래 후 잔액",          "balance_after",               "NUMERIC(18,2)"),
    ("",   "가용 잔액",             "available_balance_after",     "NUMERIC(18,2)"),
    ("",   "수수료 금액",           "fee_amount",                  "NUMERIC(18,2)"),
    ("",   "거래 통화",             "currency",                    "CHAR(3)"),
    ("",   "거래 상태",             "status",                      "VARCHAR(20)"),  # NOT NULL
    ("",   "거래 채널",             "channel_type",                "VARCHAR(30)"),
    ("",   "접속 IP",               "ip_address",                  "VARCHAR(45)"),
    ("",   "단말기 ID",             "terminal_id",                 "VARCHAR(50)"),
    ("",   "거래 위치",             "transaction_location",        "VARCHAR(100)"),
    ("",   "거래 메모",             "transaction_memo",            "VARCHAR(255)"),
    ("",   "거래 요약",             "transaction_summary",         "VARCHAR(100)"),
    ("",   "거래 일시",             "transaction_at",              "TIMESTAMPTZ"),  # NOT NULL
    ("",   "원장 게시 일시",        "posted_at",                   "TIMESTAMPTZ"),
    ("",   "취소 일시",             "canceled_at",                 "TIMESTAMPTZ"),
    ("",   "입금자 ID",             "depositor_customer_id",       "VARCHAR(30)"),  # NULL 외부 고객 ID
    ("",   "입금자명",              "depositor_name",              "VARCHAR(100)"), # NULL
    ("",   "위임받은 사람 ID",      "delegate_customer_id",        "VARCHAR(30)"),  # NULL 외부 고객 ID
    ("",   "위임받은 사람명",       "delegate_customer_name",      "VARCHAR(100)"), # NULL
    # ── 이체 전용 (TRANSFER) ──────────────────────────────────────────────
    ("",   "이체 유형",             "transfer_type",               "VARCHAR(30)"),  # NULL
    ("",   "상대 은행 코드",        "counterparty_bank_code",      "VARCHAR(10)"),  # NULL
    ("",   "상대 은행명",           "counterparty_bank_name",      "VARCHAR(100)"), # NULL
    ("",   "상대 계좌 번호",        "counterparty_account_no",     "VARCHAR(30)"),  # NULL
    ("FK", "상대 계좌 ID",          "counterparty_account_id",     "BIGINT"),       # NULL 내부이체
    ("",   "상대 고객 ID (외부)",   "counterparty_customer_id",    "VARCHAR(30)"),  # NULL FK없음
    ("",   "상대 이름",             "counterparty_name",           "VARCHAR(100)"), # NULL
    ("",   "상대 이름 확인 여부",   "counterparty_name_verified_yn","BOOLEAN"),     # NULL
    ("",   "이체 요청 일시",        "transfer_requested_at",       "TIMESTAMPTZ"),  # NULL
    ("",   "이체 완료 일시",        "transfer_completed_at",       "TIMESTAMPTZ"),  # NULL
    # ── 결제 전용 (PAYMENT) ───────────────────────────────────────────────
    ("",   "결제 방법",             "payment_method",              "VARCHAR(30)"),  # NULL
    ("",   "가맹점 번호",           "merchant_id",                 "VARCHAR(50)"),  # NULL
    ("",   "가맹점명",              "merchant_name",               "VARCHAR(100)"), # NULL
    ("",   "승인 번호",             "approval_number",             "VARCHAR(50)"),  # NULL
    ("",   "외부 거래 번호",        "external_transaction_no",     "VARCHAR(100)"), # NULL
    # ── 적금 납입 전용 (SAVINGS_PAYMENT) ─────────────────────────────────
    ("",   "납입 회차",             "payment_round",               "INT"),          # NULL
    # ── 취소/정정 전용 (REVERSAL) ─────────────────────────────────────────
    ("FK", "원 거래 ID",            "original_transaction_id",     "BIGINT"),       # NULL 자기참조
    # ── 실패 정보 (status=FAILED) ─────────────────────────────────────────
    ("",   "실패 유형",             "failure_type",                "VARCHAR(30)"),  # NULL
    ("",   "실패 코드",             "failure_code",                "VARCHAR(50)"),  # NULL
    ("",   "실패 원인 코드",        "failure_reason_code",         "VARCHAR(50)"),  # NULL
    ("",   "실패 일시",             "failure_at",                  "TIMESTAMPTZ"),  # NULL
    ("",   "재시도 횟수",           "retry_count",                 "INTEGER"),
], x=TR_X, y=TR_Y, width=560)

add_note(TR_X, TR_Y + table_height(TR_ROWS) + 20, 560, TR_NOTE_H,
    "<b>📌 transaction_type (거래 유형)</b><br>"
    "DEPOSIT: 입금 | WITHDRAW: 출금 | TRANSFER: 이체<br>"
    "INTEREST: 이자 지급 | SAVINGS_PAYMENT: 적금 납입<br>"
    "PAYMENT: 결제 | REVERSAL: 취소/정정<br>"
    "──────────────────────<br>"
    "<b>contract_id nullable 규칙</b><br>"
    "INTEREST·SAVINGS_PAYMENT → NOT NULL (계약 기반)<br>"
    "그 외 (DEPOSIT·WITHDRAW·TRANSFER·PAYMENT·REVERSAL) → NULL<br>"
    "──────────────────────<br>"
    "<b>direction_type (거래 방향)</b>: IN 입금성 | OUT 출금성<br>"
    "<b>status (거래 상태)</b>: SUCCESS | FAILED | CANCELED | PENDING<br>"
    "──────────────────────<br>"
    "<b>channel_type (거래 채널)</b><br>"
    "BRANCH: 창구 | ATM | INTERNET | MOBILE | SYSTEM<br>"
    "──────────────────────<br>"
    "<b>[이체 전용] transfer_type (이체 유형)</b><br>"
    "INTERNAL: 내부이체 | EXTERNAL: 타행이체<br>"
    "AUTO: 자동이체 | SCHEDULED: 예약이체<br>"
    "counterparty_customer_id: VARCHAR(30), FK 없음 (외부 시스템)<br>"
    "──────────────────────<br>"
    "<b>[결제 전용] payment_method (결제 방법)</b><br>"
    "CARD | ACCOUNT_TRANSFER | EASY_PAY<br>"
    "merchant_id: 카드사·PG사가 부여한 가맹점 고유번호<br>"
    "merchant_name: 카드사·PG사로부터 수신한 가맹점명<br>"
    "&nbsp;&nbsp;(영수증에 표시되는 상호명. PAYMENT 거래에만 유효, 그 외 NULL)<br>"
    "──────────────────────<br>"
    "<b>[취소 전용] original_transaction_id (원 거래ID)</b><br>"
    "REVERSAL 거래가 참조하는 원 거래 ID (자기 참조 FK)<br>"
    "──────────────────────<br>"
    "<b>[실패] failure_type (실패 유형)</b><br>"
    "TRANSFER / CARD_PAYMENT / AUTH / LIMIT / SYSTEM<br>"
    "failure_reason_code (실패 원인 코드): INSUFFICIENT_BALANCE / LIMIT_EXCEEDED<br>"
    "&nbsp;&nbsp;INVALID_ACCOUNT / CARD_DECLINED / AUTH_FAILED / SYSTEM_ERROR"
)

# 청약 납입 인정 이력 → 계약 (Row2Col5→Row1Col4: 왼쪽 출발 → 오른쪽 진입)
add_edge(sprh["contract_id"],          dc["contract_id"],       ex=0, nx=1)

# 거래 내역 엣지
add_edge(tr["account_id"],             ac["account_id"],        ex=0, nx=1)  # TR 왼쪽 → AC 오른쪽
add_edge(
    tr["contract_id"], dc["contract_id"], ex=0, nx=1,
    points=[
        (TR_X - COL_GAP / 2, 20),
        (COL4_X + W4 + COL_GAP / 2, 20),
    ],
)  # TR → DC: accounts 위쪽 빈 통로로 우회
add_edge(tr["counterparty_account_id"],ac["account_id"],        ex=0, nx=1)  # TR 왼쪽 → AC 오른쪽
add_edge(tr["original_transaction_id"],tr["transaction_id"],    ex=1, nx=1)  # 자기 참조 (오른쪽)


# ── 저장 ─────────────────────────────────────────────────────────────────
xml_str = ET.tostring(model, encoding="unicode")
pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
lines = pretty.split("\n")
if lines[0].startswith("<?xml"):
    lines = lines[1:]
pretty = "\n".join(lines)

out = r"C:\Users\green\Desktop\teamproject\teamproject.drawio"
with open(out, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(pretty)

print(f"저장 완료: {out}")
