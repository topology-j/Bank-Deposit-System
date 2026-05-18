from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "ERD 명세서"
ws.sheet_view.showGridLines = False

# ── 색상 정의 ──────────────────────────────────────────
HEADER_FILL    = PatternFill("solid", fgColor="1F4E79")
SUBHEADER_FILL = PatternFill("solid", fgColor="2E75B6")
PK_FILL        = PatternFill("solid", fgColor="FFF2CC")
FK_FILL        = PatternFill("solid", fgColor="E2EFDA")
ALT_FILL       = PatternFill("solid", fgColor="F5F5F5")
WHITE_FILL     = PatternFill("solid", fgColor="FFFFFF")

SUBHEADER_FONT = Font(name="맑은 고딕", bold=True, color="FFFFFF", size=10)
BODY_FONT      = Font(name="맑은 고딕", size=10)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT   = Alignment(horizontal="left",   vertical="center", wrap_text=True)

def thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)

def medium_border():
    s = Side(style="medium", color="2E75B6")
    return Border(left=s, right=s, top=s, bottom=s)

# ── 열 너비 (한 번만 설정) ─────────────────────────────
col_widths = [5, 22, 30, 22, 26, 42]
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

col_keys = ["no", "ko_name", "en_name", "data_type", "constraint", "description"]

AUDIT_COLUMNS = [
    {"ko_name":"최초등록일시", "en_name":"created_at", "data_type":"TIMESTAMPTZ",  "constraint":"NOT NULL DEFAULT NOW()", "description":"데이터가 최초 등록된 일시"},
    {"ko_name":"최초등록자ID", "en_name":"created_by", "data_type":"VARCHAR(100)", "constraint":"NOT NULL",               "description":"데이터를 최초 등록한 사용자/직원/시스템 식별자"},
    {"ko_name":"최종수정일시", "en_name":"updated_at", "data_type":"TIMESTAMPTZ",  "constraint":"",                       "description":"데이터가 마지막으로 수정된 일시"},
    {"ko_name":"최종수정자ID", "en_name":"updated_by", "data_type":"VARCHAR(100)", "constraint":"",                       "description":"데이터를 마지막으로 수정한 사용자/직원/시스템 식별자"},
]

AUDIT_EN_NAMES = {
    "created_at", "updated_at", "created_by", "updated_by",
    "first_registered_at", "first_registrant_identifier",
    "last_modified_at", "first_modifier_identifier",
}

def with_audit_columns(columns):
    """기존 생성/수정 일시 컬럼을 표준 감사 컬럼으로 대체."""
    base = [col for col in columns if col.get("en_name") not in AUDIT_EN_NAMES]
    numbered = []
    for idx, col in enumerate(base + AUDIT_COLUMNS, start=1):
        new_col = dict(col)
        new_col["no"] = idx
        numbered.append(new_col)
    return numbered


def write_table(start_row, table_ko, table_en, columns):
    """단일 시트에 테이블 블록 하나를 쓰고, 다음 빈 행 번호를 반환."""
    columns = with_audit_columns(columns)
    r = start_row

    # 제목 행
    ws.row_dimensions[r].height = 28
    ws.merge_cells(f"A{r}:F{r}")
    c = ws.cell(row=r, column=1, value=f"{table_ko}  ({table_en})")
    c.font      = Font(name="맑은 고딕", bold=True, color="FFFFFF", size=13)
    c.fill      = HEADER_FILL
    c.alignment = CENTER
    c.border    = medium_border()
    r += 1

    # 헤더 행
    headers = ["No", "컬럼명(한글)", "컬럼명(영문)", "데이터 타입", "제약 조건", "설명"]
    ws.row_dimensions[r].height = 22
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=r, column=ci, value=h)
        cell.font = SUBHEADER_FONT; cell.fill = SUBHEADER_FILL
        cell.alignment = CENTER; cell.border = thin_border()
    r += 1

    # 데이터 행
    for idx, col in enumerate(columns):
        ws.row_dimensions[r].height = 20
        is_pk  = "PK" in col.get("constraint", "")
        is_fk  = "FK" in col.get("constraint", "")
        is_alt = (idx % 2 == 0)
        fill = PK_FILL if is_pk else (FK_FILL if is_fk else (ALT_FILL if is_alt else WHITE_FILL))

        for ci, key in enumerate(col_keys, 1):
            cell = ws.cell(row=r, column=ci, value=col.get(key, ""))
            cell.font = BODY_FONT; cell.fill = fill; cell.border = thin_border()
            cell.alignment = CENTER if ci == 1 else LEFT
        r += 1

    # 범례
    ws.row_dimensions[r].height = 16
    for label, fgColor, ci in [("PK  기본키", "FFF2CC", 1), ("FK  외래키", "E2EFDA", 3)]:
        cell = ws.cell(row=r, column=ci, value=label)
        cell.font = Font(name="맑은 고딕", size=9)
        cell.fill = PatternFill("solid", fgColor=fgColor)
        cell.alignment = CENTER; cell.border = thin_border()
    r += 1

    return r + 2   # 테이블 사이 2행 여백


# ═══════════════════════════════════════════════════════════════════
# 테이블 순서대로 단일 시트에 작성
# ═══════════════════════════════════════════════════════════════════
row = 1

# 1. products (공통 상품)
row = write_table(row, "상품", "products", [
    {"no":1,  "ko_name":"상품 ID",            "en_name":"product_id",                 "data_type":"BIGSERIAL",     "constraint":"PK",                    "description":"상품 고유 식별자 (자동 증가)"},
    {"no":2,  "ko_name":"상품 유형",           "en_name":"product_type",               "data_type":"VARCHAR(30)",   "constraint":"NOT NULL",               "description":"DEPOSIT(예금) / SAVINGS(적금) / SUBSCRIPTION(청약)"},
    {"no":3,  "ko_name":"상품명",             "en_name":"product_name",               "data_type":"VARCHAR(200)",  "constraint":"NOT NULL",               "description":"상품 명칭"},
    {"no":4,  "ko_name":"상품 설명",           "en_name":"description",                "data_type":"TEXT",          "constraint":"",                       "description":"상품에 대한 상세 설명"},
    {"no":5,  "ko_name":"상품 담당 부서 ID",   "en_name":"department_id",              "data_type":"BIGINT",        "constraint":"FK",                     "description":"상품 담당 부서 ID (departments 테이블 FK)"},
    {"no":6,  "ko_name":"기본 금리",           "en_name":"base_interest_rate",         "data_type":"NUMERIC(5,2)", "constraint":"NOT NULL",               "description":"기본 적용 금리 (%)"},
    {"no":7,  "ko_name":"우대 금리 조건 설명", "en_name":"preferential_rate_condition","data_type":"TEXT",          "constraint":"",                       "description":"우대 금리 조건 설명 (특약·금리 테이블로 상세 관리)"},
    {"no":8,  "ko_name":"최소 가입 금액",       "en_name":"min_join_amount",            "data_type":"NUMERIC(18,2)","constraint":"",                       "description":"가입 가능 최소 금액"},
    {"no":9,  "ko_name":"최대 가입 금액",       "en_name":"max_join_amount",            "data_type":"NUMERIC(18,2)","constraint":"",                       "description":"가입 가능 최대 금액"},
    {"no":10, "ko_name":"최소 계약 기간(월)",   "en_name":"min_period_month",           "data_type":"INT",           "constraint":"",                       "description":"최소 계약 기간 (월 단위)"},
    {"no":11, "ko_name":"최대 계약 기간(월)",   "en_name":"max_period_month",           "data_type":"INT",           "constraint":"",                       "description":"최대 계약 기간 (월 단위)"},
    {"no":12, "ko_name":"중도 해지 가능 여부", "en_name":"is_early_termination_allowed","data_type":"BOOLEAN",      "constraint":"NOT NULL DEFAULT FALSE", "description":"만기 전 해지 가능 여부"},
    {"no":13, "ko_name":"세금 우대 가능 여부", "en_name":"is_tax_benefit_available",   "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE", "description":"비과세·세금우대 가능 여부"},
    {"no":14, "ko_name":"자동 재가입 가능 여부","en_name":"is_auto_renewal_available",  "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE", "description":"만기 후 자동 재가입 가능 여부"},
    {"no":15, "ko_name":"실물 통장 발행 여부", "en_name":"is_passbook_issued",         "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE", "description":"실물 통장 발행 여부"},
    {"no":16, "ko_name":"상품 출시일",         "en_name":"released_at",                "data_type":"TEXT(8)",       "constraint":"",                       "description":"실제 고객에게 판매 시작한 날짜"},
    {"no":17, "ko_name":"상품 종료일",         "en_name":"ended_at",                   "data_type":"TEXT(8)",       "constraint":"",                       "description":"판매 종료 예정일"},
    {"no":18, "ko_name":"상품 상태",           "en_name":"product_status",             "data_type":"VARCHAR(20)",   "constraint":"NOT NULL",               "description":"SELLING(판매) / SUSPENDED(중단) / EXPIRED(만료)"},
])

# 2. deposit_products (예금 상품)
row = write_table(row, "예금 상품", "deposit_products", [
    {"no":1, "ko_name":"예금 상품 ID", "en_name":"deposit_product_id",    "data_type":"BIGSERIAL",    "constraint":"PK",                    "description":"예금 상품 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"상품 ID",      "en_name":"product_id",            "data_type":"BIGINT",       "constraint":"FK NOT NULL",           "description":"공통 상품 ID (products 테이블 FK)"},
    {"no":3, "ko_name":"예금 유형",    "en_name":"deposit_type",          "data_type":"VARCHAR(20)",  "constraint":"NOT NULL",              "description":"TERM(정기예금) / DEMAND(입출금예금)"},
    {"no":4, "ko_name":"복리 여부",    "en_name":"is_compound_interest",  "data_type":"BOOLEAN",      "constraint":"NOT NULL DEFAULT FALSE", "description":"TRUE: 복리 상품 / FALSE: 단리 상품"},
])

# 3. savings_products (적금 상품)
row = write_table(row, "적금 상품", "savings_products", [
    {"no":1, "ko_name":"적금 상품 ID",       "en_name":"savings_product_id",         "data_type":"BIGSERIAL",     "constraint":"PK",                    "description":"적금 상품 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"상품 ID",           "en_name":"product_id",                 "data_type":"BIGINT",        "constraint":"FK NOT NULL",            "description":"공통 상품 ID (products 테이블 FK)"},
    {"no":3, "ko_name":"적금 유형",          "en_name":"saving_type",                "data_type":"VARCHAR(20)",   "constraint":"NOT NULL",               "description":"REGULAR(정기) / FREE(자유)"},
    {"no":4, "ko_name":"월 납입 최소 금액",   "en_name":"monthly_payment_min_amount", "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"월 납입 가능 최소 금액"},
    {"no":5, "ko_name":"월 납입 최대 금액",   "en_name":"monthly_payment_max_amount", "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"월 납입 가능 최대 금액"},
])

# 4. subscription_products (청약 상품)
row = write_table(row, "청약 상품", "subscription_products", [
    {"no":1,  "ko_name":"상품 ID",              "en_name":"product_id",                  "data_type":"BIGINT",        "constraint":"PK FK NOT NULL",         "description":"상품 ID (products PK 공유, 1:1 FK). subscription_product_id 별도 없음"},
    {"no":2,  "ko_name":"월 납입 금액",          "en_name":"monthly_payment_amount",      "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL",               "description":"기준 월 납입 금액"},
    {"no":3,  "ko_name":"월 납입 최소 금액",      "en_name":"min_monthly_payment",         "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"월 납입 가능 최소 금액"},
    {"no":4,  "ko_name":"월 납입 최대 금액",      "en_name":"max_monthly_payment",         "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"월 납입 가능 최대 금액"},
    {"no":5,  "ko_name":"납입인정최대금액",        "en_name":"max_recognized_payment_amount","data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"청약 산정 시 인정되는 최대 납입 금액 (max_monthly_payment와 의미 다름)"},
])

# 4-1. product_join_channels (상품 가입 방식)
row = write_table(row, "상품 가입 방식", "product_join_channels", [
    {"no":1, "ko_name":"상품가입방식ID", "en_name":"product_join_channel_id", "data_type":"BIGSERIAL",    "constraint":"PK",          "description":"상품 가입 방식 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"상품ID",        "en_name":"product_id",              "data_type":"BIGINT",       "constraint":"FK NOT NULL", "description":"상품 ID (products 테이블 FK)"},
    {"no":3, "ko_name":"가입방식코드",   "en_name":"join_channel_code",       "data_type":"VARCHAR(20)",  "constraint":"NOT NULL",    "description":"BRANCH(영업점) / WEB(웹) / MOBILE(모바일) / TELL(전화) / RECRUITER(모집인) / ETC(기타)"},
])

# 5. product_interest_rates (상품 금리)
row = write_table(row, "상품 금리", "product_interest_rates", [
    {"no":1,  "ko_name":"금리 ID",          "en_name":"rate_id",                "data_type":"BIGSERIAL",     "constraint":"PK",                    "description":"금리 레코드 고유 식별자 (자동 증가)"},
    {"no":2,  "ko_name":"상품 ID",          "en_name":"product_id",             "data_type":"BIGINT",        "constraint":"FK NOT NULL",            "description":"상품 ID (products 테이블 FK)"},
    {"no":3,  "ko_name":"금리 유형",        "en_name":"rate_type",              "data_type":"VARCHAR(30)",   "constraint":"NOT NULL",               "description":"BASE(기간 무관 단일 기본 금리) / PERIOD_BASE(가입 기간 구간별 기본 금리) / PREFERENTIAL(우대 금리) / EARLY_TERMINATION(중도 해지 금리)"},
    {"no":4,  "ko_name":"하한 기간(월)",    "en_name":"minimum_contract_period", "data_type":"INT",            "constraint":"",                       "description":"기간 기준 금리 구간의 최소 계약 기간(월). PERIOD_BASE·EARLY_TERMINATION 유형에서 사용 (NULL이면 하한 없음)"},
    {"no":5,  "ko_name":"상한 기간(월)",    "en_name":"maximum_contract_period", "data_type":"INT",            "constraint":"",                       "description":"기간 기준 금리 구간의 최대 계약 기간(월). PERIOD_BASE·EARLY_TERMINATION 유형에서 사용 (NULL이면 상한 없음)"},
    {"no":6,  "ko_name":"하한 금액",        "en_name":"minimum_join_amount",     "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"금액 기준 금리 구간의 최소 가입 금액. 금액 구간별 금리 적용 시 사용 (NULL이면 하한 없음)"},
    {"no":7,  "ko_name":"상한 금액",        "en_name":"maximum_join_amount",     "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"금액 기준 금리 구간의 최대 가입 금액. 금액 구간별 금리 적용 시 사용 (NULL이면 상한 없음)"},
    {"no":8,  "ko_name":"금리",            "en_name":"rate",                   "data_type":"NUMERIC(5,2)",  "constraint":"NOT NULL",               "description":"해당 구간·유형에 적용되는 금리 (%)"},
    {"no":9,  "ko_name":"조건 설명",        "en_name":"condition_description",  "data_type":"TEXT",          "constraint":"",                       "description":"금리 조건 상세 설명 (우대 금리 충족 조건, 중도 해지 구간 설명 등)"},
    {"no":10, "ko_name":"적용 시작일",      "en_name":"effective_start_date",   "data_type":"TEXT(8)",       "constraint":"NOT NULL",               "description":"해당 금리 적용 시작 날짜"},
    {"no":11, "ko_name":"적용 종료일",      "en_name":"effective_end_date",     "data_type":"TEXT(8)",       "constraint":"",                       "description":"해당 금리 적용 종료 날짜. NULL이면 현재 유효. 금리 변경 시 기존 행의 effective_end_date를 입력하고 새 행 추가"},
    {"no":12, "ko_name":"활성 여부",        "en_name":"is_active",              "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT TRUE",  "description":"현재 유효한 금리 레코드 여부"},
    {"no":13, "ko_name":"상태",            "en_name":"status",                 "data_type":"VARCHAR(20)",   "constraint":"NOT NULL DEFAULT 'ACTIVE'", "description":"금리 레코드 상태 (ACTIVE / SUSPENDED / EXPIRED)"},
])

# 2. deposit_contracts
row = write_table(row, "계약", "deposit_contracts", [
    {"no":1,  "ko_name":"계약 ID",          "en_name":"contract_id",                 "data_type":"BIGSERIAL",     "constraint":"PK",                    "description":"DB 내부 연결용 계약 고유 식별자 (자동 증가)"},
    {"no":2,  "ko_name":"계약 번호",         "en_name":"contract_number",             "data_type":"VARCHAR(50)",   "constraint":"UNIQUE NOT NULL",        "description":"실제 업무/고객 조회용 계약 번호"},
    {"no":3,  "ko_name":"고객 ID",           "en_name":"customer_id",                 "data_type":"VARCHAR(30)",   "constraint":"FK NOT NULL",            "description":"고객 식별자 (customers 테이블 FK)"},
    {"no":4,  "ko_name":"상품 ID",           "en_name":"product_id",                  "data_type":"BIGINT",        "constraint":"FK NOT NULL",            "description":"가입 상품 ID (products 테이블 FK)"},
    {"no":5,  "ko_name":"월납 여부",         "en_name":"is_monthly_payment",          "data_type":"BOOLEAN",        "constraint":"NOT NULL",               "description":"월 납입 방식 여부"},
    {"no":6,  "ko_name":"총 납입 횟수",      "en_name":"payment_count_total",         "data_type":"INT",            "constraint":"",                       "description":"약정 총 납입 횟수. 적금·청약에서 사용, 예금은 NULL"},
    {"no":7,  "ko_name":"매월 납입일",       "en_name":"monthly_payment_day",         "data_type":"VARCHAR(6)",     "constraint":"",                       "description":"매월 납입 기준일 (1~31). 월납 여부가 TRUE인 경우 사용"},
    {"no":8,  "ko_name":"가입 금액",         "en_name":"join_amount",                 "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL",               "description":"예금 가입 시 최초 납입 금액"},
    {"no":7,  "ko_name":"계약 기본 금리",    "en_name":"contract_interest_rate",       "data_type":"NUMERIC(5,2)",   "constraint":"NOT NULL",               "description":"가입 당시 확정된 기본 금리 (%)"},
    {"no":9,  "ko_name":"우대 금리 합산",    "en_name":"total_preferential_rate",      "data_type":"NUMERIC(5,2)",   "constraint":"NOT NULL DEFAULT 0",     "description":"contract_applied_rates.applied_rate 합산 우대 금리 (%)"},
    {"no":10, "ko_name":"최종 적용 금리",    "en_name":"final_interest_rate",          "data_type":"NUMERIC(5,2)",   "constraint":"NOT NULL",               "description":"계약적용금리 + 우대적용금리 합산 최종 금리 (%)"},
    {"no":11, "ko_name":"세제 혜택 유형",    "en_name":"tax_benefit_type",             "data_type":"VARCHAR(30)",    "constraint":"NOT NULL DEFAULT 'GENERAL'", "description":"GENERAL(일반과세 15.4%) / NON_TAXABLE(비과세 0%) / REDUCED_TAX(세금우대 9.9%)"},
    {"no":12, "ko_name":"적용 세율",         "en_name":"applied_tax_rate",             "data_type":"NUMERIC(5,2)",   "constraint":"NOT NULL DEFAULT 15.40", "description":"가입 당시 확정된 이자소득세율 (예: 15.40 = 15.4%)"},
    {"no":12, "ko_name":"만기 예상 이자 금액","en_name":"expected_interest_amount",     "data_type":"NUMERIC(18,2)",  "constraint":"",                       "description":"만기 시 예상되는 이자 금액"},
    {"no":13, "ko_name":"계약 기간(개월)",   "en_name":"contract_period_month",        "data_type":"INT",            "constraint":"NOT NULL",               "description":"계약 기간 (월 단위)"},
    {"no":14, "ko_name":"계약 시작일",       "en_name":"started_at",                   "data_type":"TEXT(8)",    "constraint":"NOT NULL",               "description":"계약 시작 일시"},
    {"no":15, "ko_name":"계약 만기일",       "en_name":"maturity_at",                  "data_type":"TEXT(8)",    "constraint":"NOT NULL",               "description":"계약 만기 일시"},
    {"no":16, "ko_name":"계약 해지일",       "en_name":"terminated_at",                "data_type":"TEXT(8)",    "constraint":"",                       "description":"중도 해지 일시"},
    {"no":17, "ko_name":"계약 해지 사유",    "en_name":"termination_reason",           "data_type":"VARCHAR(200)",   "constraint":"",                       "description":"중도 해지·만기 해지 사유 기록"},
    {"no":18, "ko_name":"자동 재가입 여부",   "en_name":"is_auto_renewal",              "data_type":"BOOLEAN",        "constraint":"NOT NULL",               "description":"만기 시 자동 재가입 여부"},
    {"no":19, "ko_name":"자동 이체 사용 여부", "en_name":"auto_transfer_enabled",        "data_type":"BOOLEAN",        "constraint":"NOT NULL",               "description":"자동이체 설정 여부"},
    {"no":20, "ko_name":"자동 이체일",       "en_name":"auto_transfer_day",            "data_type":"INT",            "constraint":"",                       "description":"매월 자동이체 실행 일 (1~31)"},
    {"no":21, "ko_name":"계약 상태",         "en_name":"contract_status",              "data_type":"VARCHAR(20)",    "constraint":"NOT NULL",               "description":"ACTIVE / MATURED / TERMINATED / SUSPENDED"},
    {"no":22, "ko_name":"상태 변경 일시",     "en_name":"status_changed_at",            "data_type":"TEXT(8)",    "constraint":"",                       "description":"계약 상태가 마지막으로 변경된 일시"},
    {"no":23, "ko_name":"가입 채널",         "en_name":"join_channel",                 "data_type":"VARCHAR(20)",    "constraint":"NOT NULL",               "description":"고객이 상품에 가입한 채널. BRANCH(창구) / ONLINE(인터넷뱅킹) / MOBILE(앱) / ATM"},
    {"no":24, "ko_name":"가입 지점 ID",     "en_name":"branch_id",                    "data_type":"BIGINT",         "constraint":"FK",                     "description":"창구(BRANCH) 가입 시 해당 지점 ID (branches 테이블 FK). 비창구 채널은 NULL"},
    {"no":25, "ko_name":"가입 지점 코드",    "en_name":"branch_code",                  "data_type":"VARCHAR(20)",    "constraint":"",                       "description":"가입 지점 코드 스냅샷"},
    {"no":26, "ko_name":"가입 지점명",      "en_name":"branch_name",                  "data_type":"VARCHAR(100)",   "constraint":"",                       "description":"가입 지점명 스냅샷"},
    {"no":26, "ko_name":"담당자 ID",        "en_name":"manager_id",                   "data_type":"BIGINT",         "constraint":"FK",                     "description":"계약 담당 직원 ID (employees 테이블 FK)"},
    {"no":27, "ko_name":"담당자명",         "en_name":"manager_name",                 "data_type":"VARCHAR(100)",   "constraint":"",                       "description":"담당 직원명 스냅샷"},
    {"no":28, "ko_name":"대리 가입 여부",    "en_name":"is_proxy_joined",              "data_type":"BOOLEAN",        "constraint":"NOT NULL DEFAULT FALSE", "description":"대리인 가입 여부"},
    {"no":26, "ko_name":"위임장 확인 여부",  "en_name":"is_power_of_attorney_verified","data_type":"BOOLEAN",        "constraint":"NOT NULL DEFAULT FALSE", "description":"대리 가입 시 위임장 확인 여부"},
    {"no":27, "ko_name":"위임장 파일 URL",  "en_name":"power_of_attorney_file_url",   "data_type":"VARCHAR(500)",   "constraint":"",                       "description":"대리 가입 시 위임장 스캔 파일 URL (비창구 채널은 NULL)"},
    {"no":28, "ko_name":"약관 파일 URL",   "en_name":"terms_file_url",               "data_type":"VARCHAR(500)",   "constraint":"",                       "description":"계약 당시 적용된 약관 파일 URL (스냅샷)"},
    {"no":29, "ko_name":"계약서 파일 URL", "en_name":"contract_file_url",            "data_type":"VARCHAR(500)",   "constraint":"",                       "description":"고객 서명이 완료된 계약서 파일 URL"},
    {"no":28, "ko_name":"생성 일시",         "en_name":"created_at",                   "data_type":"TIMESTAMPTZ",    "constraint":"NOT NULL DEFAULT NOW()", "description":"DB 등록 시각"},
    {"no":29, "ko_name":"수정 일시",         "en_name":"updated_at",                   "data_type":"TIMESTAMPTZ",    "constraint":"",                       "description":"마지막 수정 시각"},
])

# 3. accounts
row = write_table(row, "계좌", "accounts", [
    {"no":1,  "ko_name":"계좌 ID",          "en_name":"account_id",                "data_type":"BIGSERIAL",     "constraint":"PK",                    "description":"DB 내부 대리키 (자동 증가)"},
    {"no":2,  "ko_name":"계좌 번호",         "en_name":"account_number",            "data_type":"VARCHAR(30)",   "constraint":"UNIQUE NOT NULL",        "description":"실제 업무용 계좌 번호"},
    {"no":3,  "ko_name":"고객 ID",           "en_name":"customer_id",               "data_type":"VARCHAR(30)",   "constraint":"FK NOT NULL",            "description":"고객 식별자 (customers 테이블 FK)"},
    {"no":4,  "ko_name":"계약 ID",           "en_name":"contract_id",               "data_type":"BIGINT",        "constraint":"FK NOT NULL",            "description":"연결 계약 ID (deposit_contracts 테이블 FK)"},
    {"no":4,  "ko_name":"계좌 유형",         "en_name":"account_type",              "data_type":"VARCHAR(30)",   "constraint":"NOT NULL",               "description":"DEPOSIT(예금) / SAVINGS(적금) / SUBSCRIPTION(청약)"},
    {"no":5,  "ko_name":"적금 유형",         "en_name":"saving_type",               "data_type":"VARCHAR(20)",   "constraint":"",                       "description":"REGULAR(정기) / FREE(자유)"},
    {"no":6,  "ko_name":"은행 코드",         "en_name":"bank_code",                 "data_type":"VARCHAR(10)",   "constraint":"NOT NULL",               "description":"은행 식별 코드"},
    {"no":7,  "ko_name":"계좌 별명",         "en_name":"account_alias",             "data_type":"VARCHAR(100)",  "constraint":"",                       "description":"고객이 설정한 계좌 별명"},
    {"no":8,  "ko_name":"잔액",             "en_name":"balance",                   "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL",               "description":"현재 계좌 잔액"},
    {"no":9,  "ko_name":"누적 납입 금액",    "en_name":"total_paid_amount",         "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL DEFAULT 0",     "description":"실제 누적 납입된 총 금액 (적금 월납 합산)"},
    {"no":10, "ko_name":"총 이자 금액",       "en_name":"total_interest_amount",     "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL DEFAULT 0",     "description":"누적 지급 이자 총액 (interest_history 개별 기록과 구분되는 빠른 조회용)"},
    {"no":11, "ko_name":"마지막 거래 일시",  "en_name":"last_transaction_at",       "data_type":"TEXT(8)",   "constraint":"",                       "description":"최근 거래 발생 시각"},
    {"no":12, "ko_name":"마지막 이자 지급 일시","en_name":"last_interest_paid_at",   "data_type":"TEXT(8)",   "constraint":"",                       "description":"최근 이자 지급 시각"},
    {"no":13, "ko_name":"통화",             "en_name":"currency",                  "data_type":"CHAR(3)",       "constraint":"NOT NULL",               "description":"통화 코드 (예: KRW, USD)"},
    {"no":14, "ko_name":"계좌 비밀번호",     "en_name":"account_password",          "data_type":"VARCHAR(255)",  "constraint":"NOT NULL",               "description":"해시 저장된 계좌 비밀번호"},
    {"no":15, "ko_name":"1일 출금 한도액",    "en_name":"daily_withdraw_limit",      "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"하루 최대 출금 가능 금액"},
    {"no":16, "ko_name":"1일 출금 횟수",      "en_name":"daily_withdraw_count_limit","data_type":"INT",           "constraint":"",                       "description":"하루 최대 출금 가능 횟수"},
    {"no":17, "ko_name":"ATM 출금 한도",     "en_name":"atm_withdraw_limit",        "data_type":"NUMERIC(18,2)", "constraint":"",                       "description":"ATM 1일 출금 한도"},
    {"no":18, "ko_name":"출금 가능 여부",    "en_name":"is_withdrawable",           "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT TRUE",  "description":"지급정지·사고계좌 여부 (FALSE = 출금 불가)"},
    {"no":19, "ko_name":"인터넷 뱅킹 여부", "en_name":"is_online_banking_enabled",  "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE", "description":"인터넷뱅킹 사용 여부"},
    {"no":20, "ko_name":"모바일 뱅킹 여부", "en_name":"is_mobile_banking_enabled",  "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE", "description":"모바일앱 뱅킹 사용 여부"},
    {"no":21, "ko_name":"폰뱅킹 여부",     "en_name":"is_phone_banking_enabled",   "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE", "description":"폰뱅킹 사용 여부"},
    {"no":21, "ko_name":"계좌 상태",         "en_name":"account_status",            "data_type":"VARCHAR(20)",   "constraint":"NOT NULL",               "description":"ACTIVE / DORMANT / SUSPENDED / CLOSED"},
    {"no":22, "ko_name":"개설 일시",         "en_name":"opened_at",                 "data_type":"TEXT(8)",   "constraint":"NOT NULL",               "description":"실제 계좌가 개설된 업무 시각 (고객/업무 기준)"},
    {"no":23, "ko_name":"만기 일시",         "en_name":"maturity_at",               "data_type":"TEXT(8)",   "constraint":"",                       "description":"계좌 만기 일시"},
    {"no":24, "ko_name":"휴면 전환 일시",     "en_name":"dormant_at",                "data_type":"TEXT(8)",   "constraint":"",                       "description":"휴면 계좌로 전환된 일시"},
    {"no":25, "ko_name":"휴면 해제 일시",     "en_name":"dormant_released_at",       "data_type":"TEXT(8)",   "constraint":"",                       "description":"휴면 계좌가 해제된 일시"},
    {"no":26, "ko_name":"해지 일시",         "en_name":"closed_at",                 "data_type":"TEXT(8)",   "constraint":"",                       "description":"계좌 해지 일시"},
    {"no":27, "ko_name":"상태 변경 일시",     "en_name":"status_changed_at",         "data_type":"TEXT(8)",   "constraint":"",                       "description":"계좌 상태가 마지막으로 변경된 일시"},
    {"no":28, "ko_name":"생성 일시",         "en_name":"created_at",                "data_type":"TIMESTAMPTZ",   "constraint":"NOT NULL DEFAULT NOW()", "description":"DB에 데이터가 저장된 시스템 시각 (이관·배치 시 개설 일시와 다를 수 있음)"},
    {"no":29, "ko_name":"수정 일시",         "en_name":"updated_at",                "data_type":"TIMESTAMPTZ",   "constraint":"",                       "description":"마지막 수정 시각"},
])

# 5. interest_history
row = write_table(row, "이자 내역", "interest_history", [
    {"no":1,  "ko_name":"이자 ID",          "en_name":"interest_id",                     "data_type":"BIGSERIAL",      "constraint":"PK",                        "description":"이자 내역 고유 식별자 (자동 증가)"},
    {"no":2,  "ko_name":"계약 ID",          "en_name":"contract_id",                     "data_type":"BIGINT",         "constraint":"FK NOT NULL",                "description":"연결 계약 ID (deposit_contracts 테이블 FK)"},
    {"no":3,  "ko_name":"계좌 ID",          "en_name":"account_id",                      "data_type":"BIGINT",         "constraint":"FK NOT NULL",                "description":"이자 입금 계좌 ID (accounts 테이블 FK)"},
    {"no":4,  "ko_name":"적용 금리",        "en_name":"applied_interest_rate",           "data_type":"NUMERIC(5,2)",   "constraint":"NOT NULL",                   "description":"이자 계산에 적용된 금리 (%)"},
    {"no":6,  "ko_name":"이자 계산 시작일",  "en_name":"interest_calculation_start_date", "data_type":"TEXT(8)",           "constraint":"NOT NULL",                   "description":"이자 계산 대상 기간 시작일"},
    {"no":7,  "ko_name":"이자 계산 종료일",  "en_name":"interest_calculation_end_date",   "data_type":"TEXT(8)",           "constraint":"NOT NULL",                   "description":"이자 계산 대상 기간 종료일"},
    {"no":8,  "ko_name":"이자 발생 일시",    "en_name":"interest_occurred_at",            "data_type":"TEXT(8)",    "constraint":"",                           "description":"이자가 실제 발생·확정된 일시 (계산 완료 후 원장 반영 시각)"},
    {"no":9,  "ko_name":"이자 금액",        "en_name":"interest_amount",                 "data_type":"NUMERIC(18,2)",  "constraint":"NOT NULL",                   "description":"회차별 이자 금액"},
    {"no":10, "ko_name":"세제 혜택 유형",    "en_name":"tax_benefit_type",                "data_type":"VARCHAR(30)",    "constraint":"NOT NULL DEFAULT 'GENERAL'", "description":"GENERAL(일반과세 15.4%) / NON_TAXABLE(비과세 0%) / REDUCED_TAX(세금우대 9%)"},
    {"no":11, "ko_name":"적용 세율",        "en_name":"applied_tax_rate",                "data_type":"NUMERIC(5,4)",   "constraint":"NOT NULL",                   "description":"실제 적용된 이자소득세율 (예: 0.1540 = 15.4%)"},
    {"no":12, "ko_name":"세전 이자 금액",    "en_name":"interest_before_tax",             "data_type":"NUMERIC(18,2)",  "constraint":"NOT NULL",                   "description":"세금 차감 전 이자 금액"},
    {"no":13, "ko_name":"이자소득세 금액",   "en_name":"interest_tax_amount",             "data_type":"NUMERIC(18,2)",  "constraint":"NOT NULL DEFAULT 0",         "description":"이자소득세 금액 (이자소득 × 세율 14%)"},
    {"no":14, "ko_name":"지방소득세 금액",   "en_name":"local_income_tax_amount",         "data_type":"NUMERIC(18,2)",  "constraint":"NOT NULL DEFAULT 0",         "description":"지방소득세 금액 (이자소득세의 10%)"},
    {"no":15, "ko_name":"세후 이자 금액",    "en_name":"interest_after_tax",              "data_type":"NUMERIC(18,2)",  "constraint":"NOT NULL",                   "description":"세금 차감 후 실제 지급 이자 금액"},
    {"no":16, "ko_name":"이자 발생 사유",    "en_name":"interest_reason",                 "data_type":"VARCHAR(255)",   "constraint":"",                           "description":"REGULAR_INTEREST(정기 이자) / MATURITY_INTEREST(만기 이자) / BONUS_INTEREST(우대 금리 이자)"},
    {"no":17, "ko_name":"총 이자 금액",      "en_name":"total_interest_amount",           "data_type":"DECIMAL(15,2)",  "constraint":"NOT NULL",                   "description":"누적 총 이자 금액"},
    {"no":18, "ko_name":"이자 지급 일시",    "en_name":"interest_paid_at",                "data_type":"TEXT(8)",    "constraint":"NOT NULL",                   "description":"이자가 실제 지급된 일시"},
])

# 5-1. contract_applied_rates (계약 우대 금리 적용 내역)
row = write_table(row, "계약 우대 금리 적용 내역", "contract_applied_rates", [
    {"no":1, "ko_name":"적용 내역 ID", "en_name":"applied_rate_id", "data_type":"BIGSERIAL",      "constraint":"PK",                    "description":"우대 금리 적용 내역 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"계약 ID",     "en_name":"contract_id",     "data_type":"BIGINT",          "constraint":"FK NOT NULL",            "description":"연결 계약 ID (deposit_contracts 테이블 FK)"},
    {"no":3, "ko_name":"금리 ID",     "en_name":"rate_id",         "data_type":"BIGINT",          "constraint":"FK NOT NULL",            "description":"적용된 우대 금리 항목 ID (product_interest_rates 테이블 FK)"},
    {"no":4, "ko_name":"적용 금리",   "en_name":"applied_rate",    "data_type":"NUMERIC(5,2)",    "constraint":"NOT NULL",               "description":"계약 시점 확정된 우대 금리 수치 스냅샷 (%)"},
    {"no":5, "ko_name":"생성 일시",   "en_name":"created_at",      "data_type":"TIMESTAMPTZ",     "constraint":"NOT NULL DEFAULT NOW()", "description":"DB에 데이터가 저장된 시스템 시각"},
])

# 6. special_terms (수신 특약)
row = write_table(row, "수신 특약", "special_terms", [
    {"no":1,  "ko_name":"특약 ID",          "en_name":"special_term_id",       "data_type":"BIGSERIAL",    "constraint":"PK",                    "description":"특약 고유 식별자 (자동 증가)"},
    {"no":2,  "ko_name":"특약명",           "en_name":"special_term_name",     "data_type":"VARCHAR(200)", "constraint":"NOT NULL",               "description":"특약 명칭"},
    {"no":3,  "ko_name":"특약 내용",         "en_name":"special_term_content",  "data_type":"TEXT",         "constraint":"NOT NULL",               "description":"특약 상세 내용"},
    {"no":4,  "ko_name":"특약 요약",         "en_name":"special_term_summary",  "data_type":"TEXT",         "constraint":"",                       "description":"특약 핵심 내용 요약"},
    {"no":5,  "ko_name":"필수 여부",         "en_name":"is_required",           "data_type":"BOOLEAN",      "constraint":"NOT NULL DEFAULT FALSE", "description":"상품 가입 시 필수 적용 특약 여부"},
    {"no":6,  "ko_name":"전자 동의 가능 여부","en_name":"is_electronic_agreement_allowed","data_type":"BOOLEAN","constraint":"NOT NULL DEFAULT TRUE","description":"전자서명·전자동의 가능 여부"},
    {"no":7,  "ko_name":"특약 버전",         "en_name":"special_term_version",  "data_type":"VARCHAR(20)",  "constraint":"NOT NULL",               "description":"특약 버전 식별자"},
    {"no":8,  "ko_name":"특약 시작일",       "en_name":"started_at",            "data_type":"TEXT(8)",  "constraint":"",                       "description":"특약 적용 시작일"},
    {"no":9,  "ko_name":"특약 종료일",       "en_name":"ended_at",              "data_type":"TEXT(8)",  "constraint":"",                       "description":"특약 적용 종료일"},
    {"no":10, "ko_name":"상태",             "en_name":"status",                "data_type":"VARCHAR(20)",  "constraint":"NOT NULL",               "description":"ACTIVE / INACTIVE / EXPIRED"},
    {"no":11, "ko_name":"상태 변경 일시",     "en_name":"status_changed_at",     "data_type":"TEXT(8)",  "constraint":"",                       "description":"특약 상태가 마지막으로 변경된 일시"},
])

# 7. product_special_terms
row = write_table(row, "수신 상품 특약 연결", "product_special_terms", [
    {"no":1, "ko_name":"연결 ID",   "en_name":"product_special_term_id", "data_type":"BIGSERIAL", "constraint":"PK",         "description":"상품-특약 연결 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"상품 ID",   "en_name":"product_id",              "data_type":"BIGINT",    "constraint":"FK NOT NULL", "description":"연결 상품 ID (products 테이블 FK)"},
    {"no":3, "ko_name":"특약 ID",   "en_name":"special_term_id",         "data_type":"BIGINT",    "constraint":"FK NOT NULL", "description":"연결 특약 ID (special_terms 테이블 FK)"},
    {"no":4, "ko_name":"필수 여부", "en_name":"is_required",             "data_type":"BOOLEAN",   "constraint":"NOT NULL",    "description":"필수 적용 여부 (TRUE: 필수, FALSE: 선택)"},
])

# 8. contract_special_term_agreements
row = write_table(row, "수신 특약 동의", "contract_special_term_agreements", [
    {"no":1, "ko_name":"동의 ID",       "en_name":"special_agreement_id",      "data_type":"BIGSERIAL",  "constraint":"PK",          "description":"특약 동의 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"계약 ID",       "en_name":"contract_id",               "data_type":"BIGINT",     "constraint":"FK NOT NULL", "description":"계약 ID (deposit_contracts 테이블 FK)"},
    {"no":3, "ko_name":"특약 ID",       "en_name":"special_term_id",           "data_type":"BIGINT",     "constraint":"FK NOT NULL", "description":"동의 특약 ID (special_terms 테이블 FK)"},
    {"no":4, "ko_name":"동의 여부",     "en_name":"is_agreed",                 "data_type":"BOOLEAN",    "constraint":"NOT NULL",    "description":"특약 동의 여부 (TRUE: 동의, FALSE: 미동의)"},
    {"no":5, "ko_name":"동의 일시",     "en_name":"agreed_at",                 "data_type":"TEXT(8)","constraint":"",            "description":"특약에 동의한 일시"},
    {"no":6, "ko_name":"동의 IP 주소",   "en_name":"agreement_ip_address",      "data_type":"VARCHAR(45)", "constraint":"",           "description":"특약 동의 시 접속 IP 주소"},
    {"no":7, "ko_name":"동의 기기 정보", "en_name":"agreement_device_info",     "data_type":"VARCHAR(255)","constraint":"",           "description":"동의 시 사용 기기 정보 (모바일/PC/앱 등)"},
    {"no":8, "ko_name":"전자 서명 여부", "en_name":"is_electronic_signed",      "data_type":"BOOLEAN",    "constraint":"NOT NULL DEFAULT FALSE", "description":"전자서명 완료 여부"},
    {"no":9, "ko_name":"동의 철회 여부", "en_name":"is_agreement_withdrawn",    "data_type":"BOOLEAN",    "constraint":"NOT NULL DEFAULT FALSE", "description":"특약 동의 철회 여부"},
    {"no":10,"ko_name":"동의 철회 일시", "en_name":"agreement_withdrawn_at",    "data_type":"TEXT(8)","constraint":"",            "description":"특약 동의 철회 일시"},
])

# 9. special_term_history (수신 특약 이력)
row = write_table(row, "수신 특약 이력", "special_term_history", [
    {"no":1, "ko_name":"이력 ID",    "en_name":"history_id",               "data_type":"BIGSERIAL",   "constraint":"PK",                    "description":"특약 이력 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"특약 ID",    "en_name":"special_term_id",          "data_type":"BIGINT",      "constraint":"FK NOT NULL",            "description":"대상 특약 ID (special_terms 테이블 FK)"},
    {"no":3, "ko_name":"이전 버전",  "en_name":"previous_version",         "data_type":"VARCHAR(20)", "constraint":"",                       "description":"변경 전 특약 버전"},
    {"no":4, "ko_name":"변경 버전",  "en_name":"changed_version",          "data_type":"VARCHAR(20)", "constraint":"NOT NULL",               "description":"변경 후 특약 버전"},
    {"no":5, "ko_name":"변경 사유",  "en_name":"change_reason",            "data_type":"TEXT",        "constraint":"",                       "description":"특약 변경 사유 설명"},
    {"no":6, "ko_name":"변경 일시",  "en_name":"changed_at",               "data_type":"TEXT(8)", "constraint":"NOT NULL",               "description":"특약이 변경된 일시"},
    {"no":7, "ko_name":"생성 일시",  "en_name":"created_at",               "data_type":"TIMESTAMPTZ", "constraint":"NOT NULL DEFAULT NOW()", "description":"DB 등록 시각"},
])

# 10. departments
row = write_table(row, "부서", "departments", [
    {"no":1, "ko_name":"부서 ID",       "en_name":"department_id",        "data_type":"BIGSERIAL",    "constraint":"PK",                    "description":"부서 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"부서 코드",     "en_name":"department_code",      "data_type":"VARCHAR(50)",  "constraint":"UNIQUE NOT NULL",        "description":"사내 부서 코드"},
    {"no":3, "ko_name":"부서명",       "en_name":"department_name",      "data_type":"VARCHAR(100)", "constraint":"NOT NULL",               "description":"부서명"},
    {"no":4, "ko_name":"상위 부서 ID",   "en_name":"parent_department_id", "data_type":"BIGINT",       "constraint":"FK",                     "description":"상위 부서 ID (departments 자기참조 FK)"},
    {"no":5, "ko_name":"부서 유형",     "en_name":"department_type",      "data_type":"VARCHAR(30)",  "constraint":"",                       "description":"PRODUCT / SALES / OPERATION / RISK / IT 등 부서 분류"},
    {"no":6, "ko_name":"사용 여부",     "en_name":"is_active",            "data_type":"BOOLEAN",      "constraint":"NOT NULL DEFAULT TRUE",  "description":"부서 사용 여부"},
    {"no":7, "ko_name":"생성 일시",     "en_name":"created_at",           "data_type":"TIMESTAMPTZ",  "constraint":"NOT NULL DEFAULT NOW()", "description":"DB 등록 시각"},
    {"no":8, "ko_name":"수정 일시",     "en_name":"updated_at",           "data_type":"TIMESTAMPTZ",  "constraint":"",                       "description":"마지막 수정 시각"},
])


# 10-1. subscription_payment_recognition_history (청약 납입 인정 이력)
row = write_table(row, "청약 납입 인정 이력", "subscription_payment_recognition_history", [
    {"no":1, "ko_name":"인정이력ID",   "en_name":"recognition_id",    "data_type":"BIGSERIAL",    "constraint":"PK",                    "description":"청약 납입 인정 이력 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"계약ID",       "en_name":"contract_id",        "data_type":"BIGINT",       "constraint":"FK NOT NULL",           "description":"연결 계약 ID (deposit_contracts 테이블 FK)"},
    {"no":3, "ko_name":"실제납입금액",  "en_name":"payment_amount",     "data_type":"NUMERIC(18,2)","constraint":"NOT NULL",             "description":"실제 납입한 금액"},
    {"no":4, "ko_name":"인정금액",     "en_name":"recognized_amount",  "data_type":"NUMERIC(18,2)","constraint":"NOT NULL",             "description":"청약 산정 시 인정되는 금액 (max_recognized_payment_amount 기준)"},
    {"no":5, "ko_name":"납입월",       "en_name":"payment_month",      "data_type":"VARCHAR(6)",   "constraint":"NOT NULL",             "description":"해당 납입이 속하는 월 (YYYYMM 형식)"},
    {"no":6, "ko_name":"인정일시",     "en_name":"recognized_at",      "data_type":"TIMESTAMPTZ",  "constraint":"",                     "description":"납입 인정 처리 일시"},
    {"no":7, "ko_name":"인정상태",     "en_name":"recognition_status", "data_type":"VARCHAR(20)",  "constraint":"",                     "description":"RECOGNIZED(인정완료) / PARTIAL(일부인정) / REJECTED(인정거부) / PENDING(검토중)"},
    {"no":8, "ko_name":"생성일시",     "en_name":"created_at",         "data_type":"TIMESTAMPTZ",  "constraint":"NOT NULL DEFAULT NOW()","description":"DB 등록 시각"},
])

# 9-1. target_groups (가입 대상 그룹)
row = write_table(row, "가입 대상 그룹", "target_groups", [
    {"no":1, "ko_name":"대상 그룹 ID",  "en_name":"target_group_id",  "data_type":"BIGSERIAL",    "constraint":"PK",         "description":"가입 대상 그룹 고유 식별자 (자동 증가)"},
    {"no":2, "ko_name":"대상 그룹명",   "en_name":"target_group_name","data_type":"VARCHAR(100)", "constraint":"NOT NULL",   "description":"가입 대상 그룹명 (예: 청년, 장애인, 기초수급자, 신규고객 등)"},
    {"no":3, "ko_name":"설명",         "en_name":"description",      "data_type":"TEXT",         "constraint":"",           "description":"대상 그룹의 조건 또는 자격 요건 설명"},
    {"no":4, "ko_name":"활성 여부",    "en_name":"is_active",        "data_type":"BOOLEAN",      "constraint":"NOT NULL DEFAULT TRUE", "description":"현재 사용 중인 대상 그룹 여부"},
])

# 9-2. product_target_groups (상품 가입 대상 연결)
row = write_table(row, "상품 가입 대상 연결", "product_target_groups", [
    {"no":1, "ko_name":"상품 ID",      "en_name":"product_id",      "data_type":"BIGINT",       "constraint":"FK NOT NULL", "description":"상품 ID (products 테이블 FK)"},
    {"no":2, "ko_name":"대상 그룹 ID", "en_name":"target_group_id", "data_type":"BIGINT",       "constraint":"FK NOT NULL", "description":"대상 그룹 ID (target_groups 테이블 FK)"},
])

# 11. transactions (거래 내역)
row = write_table(row, "거래 내역", "transactions", [
    {"no":1,  "ko_name":"거래 ID",            "en_name":"transaction_id",            "data_type":"BIGSERIAL",     "constraint":"PK",                     "description":"거래 고유 식별자 (자동 증가)"},
    {"no":2,  "ko_name":"거래 번호",           "en_name":"transaction_number",        "data_type":"VARCHAR(50)",   "constraint":"UNIQUE NOT NULL",         "description":"업무/고객 조회용 거래 번호"},
    {"no":3,  "ko_name":"계좌 ID",            "en_name":"account_id",                "data_type":"BIGINT",        "constraint":"FK NOT NULL",             "description":"거래 발생 계좌 ID (accounts FK)"},
    {"no":4,  "ko_name":"계약 ID",            "en_name":"contract_id",               "data_type":"BIGINT",        "constraint":"FK",                      "description":"이자·중도해지 등 계약 연관 거래 시 참조 ID"},
    {"no":5,  "ko_name":"거래 유형",           "en_name":"transaction_type",          "data_type":"VARCHAR(30)",   "constraint":"NOT NULL",                "description":"DEPOSIT / WITHDRAW / TRANSFER / INTEREST / AUTO_TRANSFER / EARLY_TERMINATION / REVERSAL / SAVINGS_PAYMENT"},
    {"no":6,  "ko_name":"납입 회차",           "en_name":"payment_round",             "data_type":"INT",           "constraint":"",                        "description":"적금 납입 회차 순번 (transaction_type=SAVINGS_PAYMENT일 때 사용; 다른 거래 유형은 NULL)"},
    {"no":7,  "ko_name":"입출금 구분",         "en_name":"direction_type",            "data_type":"VARCHAR(10)",   "constraint":"NOT NULL",                "description":"IN(입금성 거래) / OUT(출금성 거래)"},
    {"no":7,  "ko_name":"거래 금액",           "en_name":"amount",                    "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL",                "description":"거래 금액"},
    {"no":8,  "ko_name":"거래 전 잔액",        "en_name":"balance_before",            "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL",                "description":"거래 처리 전 계좌 잔액"},
    {"no":9,  "ko_name":"거래 후 잔액",        "en_name":"balance_after",             "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL",                "description":"거래 처리 후 계좌 잔액"},
    {"no":10, "ko_name":"수수료 금액",         "en_name":"fee_amount",                "data_type":"NUMERIC(18,2)", "constraint":"NOT NULL DEFAULT 0",      "description":"거래 수수료 금액"},
    {"no":11, "ko_name":"거래 채널",           "en_name":"channel_type",              "data_type":"VARCHAR(30)",   "constraint":"NOT NULL",                "description":"BRANCH / ATM / INTERNET / MOBILE / SYSTEM"},
    {"no":12, "ko_name":"상대 은행 코드",      "en_name":"counterparty_bank_code",    "data_type":"VARCHAR(10)",   "constraint":"",                        "description":"타행 거래 또는 외부 상대 은행 코드"},
    {"no":13, "ko_name":"상대 은행명",         "en_name":"counterparty_bank_name",    "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"거래 상대방의 은행 이름 스냅샷"},
    {"no":14, "ko_name":"상대 계좌 번호",      "en_name":"counterparty_account_no",   "data_type":"VARCHAR(30)",   "constraint":"",                        "description":"타행/당행 상대 계좌 번호"},
    {"no":15, "ko_name":"상대 이름",           "en_name":"counterparty_name",         "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"거래 상대방 이름 또는 사업자명 스냅샷"},
    {"no":16, "ko_name":"상대 고객 ID",        "en_name":"counterparty_customer_id",  "data_type":"BIGINT",        "constraint":"FK",                      "description":"당행 내 거래 시 상대 고객 ID"},
    {"no":17, "ko_name":"상대 계좌 ID",        "en_name":"counterparty_account_id",   "data_type":"BIGINT",        "constraint":"FK",                      "description":"당행 내 거래 시 상대 계좌 ID (accounts FK)"},
    {"no":18, "ko_name":"상대 이름 확인 여부", "en_name":"counterparty_name_verified_yn","data_type":"BOOLEAN",    "constraint":"NOT NULL DEFAULT FALSE",  "description":"상대 이름/사업자명 검증 완료 여부"},
    {"no":19, "ko_name":"원 거래 ID",          "en_name":"original_transaction_id",   "data_type":"BIGINT",        "constraint":"FK",                      "description":"취소/정정/환불 거래가 참조하는 원 거래 ID (자기 참조)"},
    {"no":20, "ko_name":"거래 메모",           "en_name":"transaction_memo",          "data_type":"VARCHAR(255)",  "constraint":"",                        "description":"거래에 첨부된 메모 또는 적요"},
    {"no":21, "ko_name":"거래 상태",           "en_name":"status",                    "data_type":"VARCHAR(20)",   "constraint":"NOT NULL",                "description":"SUCCESS / FAILED / CANCELED / PENDING"},
    {"no":22, "ko_name":"거래 일시",           "en_name":"transaction_at",            "data_type":"TIMESTAMPTZ",   "constraint":"NOT NULL",                "description":"실제 거래가 발생한 일시"},
    {"no":23, "ko_name":"거래 통화",           "en_name":"currency",                  "data_type":"CHAR(3)",       "constraint":"NOT NULL DEFAULT 'KRW'",  "description":"거래 통화 코드 (예: KRW, USD)"},
    {"no":24, "ko_name":"가용 잔액",           "en_name":"available_balance_after",   "data_type":"NUMERIC(18,2)", "constraint":"",                        "description":"거래 후 인출 가능한 가용 잔액"},
    {"no":25, "ko_name":"거래 요약",           "en_name":"transaction_summary",       "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"통장 인쇄·화면 표시용 거래 요약 문구"},
    {"no":26, "ko_name":"이체 유형",           "en_name":"transfer_type",             "data_type":"VARCHAR(30)",   "constraint":"",                        "description":"INTERNAL(당행) / EXTERNAL(타행) / AUTO(자동) / SCHEDULED(예약)"},
    {"no":27, "ko_name":"이체 요청 일시",      "en_name":"transfer_requested_at",     "data_type":"TIMESTAMPTZ",   "constraint":"",                        "description":"이체 요청이 접수된 일시"},
    {"no":28, "ko_name":"이체 완료 일시",      "en_name":"transfer_completed_at",     "data_type":"TIMESTAMPTZ",   "constraint":"",                        "description":"이체 처리가 완료된 일시"},
    {"no":29, "ko_name":"이체 실패 여부",      "en_name":"transfer_failed_yn",        "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE",  "description":"이체 실패 여부"},
    {"no":30, "ko_name":"결제 방법",           "en_name":"payment_method",            "data_type":"VARCHAR(30)",   "constraint":"",                        "description":"CARD / ACCOUNT_TRANSFER / EASY_PAY"},
    {"no":31, "ko_name":"카드 결제 여부",      "en_name":"card_payment_yn",           "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE",  "description":"카드 결제 거래 여부"},
    {"no":32, "ko_name":"결제 실패 여부",      "en_name":"payment_failed_yn",         "data_type":"BOOLEAN",       "constraint":"NOT NULL DEFAULT FALSE",  "description":"카드 또는 간편 결제 실패 여부"},
    {"no":33, "ko_name":"가맹점 번호",         "en_name":"merchant_id",               "data_type":"VARCHAR(50)",   "constraint":"",                        "description":"카드 결제 가맹점 식별 번호"},
    {"no":34, "ko_name":"가맹점명",            "en_name":"merchant_name",             "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"카드 결제 가맹점 이름"},
    {"no":35, "ko_name":"실패 유형",           "en_name":"failure_type",              "data_type":"VARCHAR(30)",   "constraint":"",                        "description":"TRANSFER / CARD_PAYMENT / AUTH / LIMIT / SYSTEM"},
    {"no":36, "ko_name":"실패 코드",           "en_name":"failure_code",              "data_type":"VARCHAR(50)",   "constraint":"",                        "description":"카드사·외부 시스템 원본 오류 코드"},
    {"no":37, "ko_name":"실패 원인 코드",      "en_name":"failure_reason_code",       "data_type":"VARCHAR(50)",   "constraint":"",                        "description":"INSUFFICIENT_BALANCE / LIMIT_EXCEEDED / INVALID_ACCOUNT / CARD_DECLINED / AUTH_FAILED 등"},
    {"no":38, "ko_name":"실패 일시",           "en_name":"failure_at",                "data_type":"TIMESTAMPTZ",   "constraint":"",                        "description":"거래 실패가 발생한 일시"},
    {"no":39, "ko_name":"재시도 횟수",         "en_name":"retry_count",               "data_type":"INTEGER",       "constraint":"NOT NULL DEFAULT 0",      "description":"실패 후 재시도 횟수"},
    {"no":40, "ko_name":"승인 번호",           "en_name":"approval_number",           "data_type":"VARCHAR(50)",   "constraint":"",                        "description":"거래 승인 번호"},
    {"no":41, "ko_name":"외부 거래 번호",      "en_name":"external_transaction_no",   "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"카드사·금융결제원 등 외부 거래 번호"},
    {"no":42, "ko_name":"단말기 ID",           "en_name":"terminal_id",               "data_type":"VARCHAR(50)",   "constraint":"",                        "description":"ATM·POS 단말기 고유 ID"},
    {"no":43, "ko_name":"접속 IP",             "en_name":"ip_address",                "data_type":"VARCHAR(45)",   "constraint":"",                        "description":"인터넷·모바일 거래 시 접속 IP 주소"},
    {"no":44, "ko_name":"거래 위치",           "en_name":"transaction_location",      "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"ATM·창구 거래 시 위치 정보"},
    {"no":45, "ko_name":"원장 게시 일시",      "en_name":"posted_at",                 "data_type":"TIMESTAMPTZ",   "constraint":"",                        "description":"원장에 최종 반영·게시된 일시"},
    {"no":46, "ko_name":"취소 일시",           "en_name":"canceled_at",               "data_type":"TIMESTAMPTZ",   "constraint":"",                        "description":"거래 취소 처리가 완료된 일시"},
    {"no":47, "ko_name":"입금자 ID",           "en_name":"depositor_customer_id",     "data_type":"VARCHAR(30)",   "constraint":"",                        "description":"입금 거래 시 입금자 외부 고객 ID"},
    {"no":48, "ko_name":"입금자명",            "en_name":"depositor_name",            "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"입금 거래 시 입금자명"},
    {"no":49, "ko_name":"위임받은 사람 ID",    "en_name":"delegate_customer_id",      "data_type":"VARCHAR(30)",   "constraint":"",                        "description":"대리/위임 거래 시 위임받은 사람 외부 고객 ID"},
    {"no":50, "ko_name":"위임받은 사람명",     "en_name":"delegate_customer_name",    "data_type":"VARCHAR(100)",  "constraint":"",                        "description":"대리/위임 거래 시 위임받은 사람명"},
])


# ═══════════════════════════════════════════════════════════════════
# 샘플 데이터 시트
# ═══════════════════════════════════════════════════════════════════
ws2 = wb.create_sheet("샘플 데이터")
ws2.sheet_view.showGridLines = False

SAMPLE_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
SAMPLE_COL_FILL    = PatternFill("solid", fgColor="2E75B6")
SAMPLE_ROW_FILLS   = [
    PatternFill("solid", fgColor="FFFFFF"),
    PatternFill("solid", fgColor="F5F5F5"),
]

def write_sample_table(ws, start_row, table_ko, table_en, columns, rows):
    r = start_row
    # 테이블 제목
    end_col = len(columns)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=end_col)
    c = ws.cell(row=r, column=1, value=f"{table_ko}  ({table_en})")
    c.font = Font(name="맑은 고딕", bold=True, color="FFFFFF", size=12)
    c.fill = SAMPLE_HEADER_FILL
    c.alignment = CENTER
    c.border = medium_border()
    ws.row_dimensions[r].height = 26
    for ci in range(2, end_col + 1):
        cell = ws.cell(row=r, column=ci)
        cell.fill = SAMPLE_HEADER_FILL
        cell.border = medium_border()
    r += 1
    # 컬럼명 행 — (한글명, 영문명) 튜플 or 문자열 모두 지원
    ws.row_dimensions[r].height = 32
    for ci, col in enumerate(columns, 1):
        if isinstance(col, tuple):
            header_val = f"{col[0]}\n{col[1]}"
        else:
            header_val = col
        cell = ws.cell(row=r, column=ci, value=header_val)
        cell.font = SUBHEADER_FONT
        cell.fill = SAMPLE_COL_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border()
    r += 1
    # 데이터 행
    for ri, row_data in enumerate(rows):
        ws.row_dimensions[r].height = 18
        fill = SAMPLE_ROW_FILLS[ri % 2]
        for ci, val in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=ci, value=val)
            cell.font = BODY_FONT
            cell.fill = fill
            cell.alignment = LEFT
            cell.border = thin_border()
        r += 1
    return r + 2

sr = 1

# 열 너비 설정
for ci in range(1, 50):
    ws2.column_dimensions[get_column_letter(ci)].width = 22

# ── 1. products ──────────────────────────────────────────────────────
sr = write_sample_table(ws2, sr, "상품", "products",
    [("상품 ID","product_id"), ("상품 유형","product_type"), ("상품명","product_name"),
     ("담당부서 ID","department_id"),
     ("기본금리","base_interest_rate"),
     ("최소가입금액","min_join_amount"), ("최대가입금액","max_join_amount"),
     ("최소계약기간(월)","min_period_month"), ("최대계약기간(월)","max_period_month"),
     ("중도해지가능","is_early_termination_allowed"),
     ("세금우대가능","is_tax_benefit_available"), ("자동재가입가능","is_auto_renewal_available"),
     ("실물통장발행","is_passbook_issued"),
     ("상품상태","product_status"), ("출시일","released_at")],
    [
        [1,"DEPOSIT",      "KR 정기예금 12M",    1, 3.50,1000000, 100000000,12,12, True, 1.50,True, True, False,"SELLING", "20240102"],
        [2,"DEPOSIT",      "KR 시니어 정기예금", 1, 4.00,500000,  50000000, 6, 24, True, 2.00,True, True, True, "SELLING", "20240301"],
        [3,"SAVINGS",      "KR 자유적금",         1, 3.00,10000,   1000000,  6, 36, True, 1.50,True, False,False,"SELLING", "20240102"],
        [4,"SAVINGS",      "KR 청년 우대적금",    1, 3.50,10000,   500000,   6, 24, True, 1.00,True, True, False,"SELLING", "20240601"],
        [5,"SUBSCRIPTION", "주택청약종합저축",    2, 2.50,2000,    200000,   6, None,False,None,False,False,False,"SELLING", "20240102"],
    ]
)

# ── 2. deposit_products ───────────────────────────────────────────────
sr = write_sample_table(ws2, sr, "예금 상품", "deposit_products",
    [("예금상품 ID","deposit_product_id"), ("상품 ID","product_id")],
    [
        [1, 1],
        [2, 2],
    ]
)

# ── 2-1. target_groups ───────────────────────────────────────────────────
sr = write_sample_table(ws2, sr, "가입 대상 그룹", "target_groups",
    [("그룹 ID","target_group_id"), ("그룹명","target_group_name"),
     ("설명","description"), ("활성여부","is_active")],
    [
        [1, "일반",       "누구나 가입 가능",                    True],
        [2, "청년",       "만 19~34세 이하 청년",                True],
        [3, "직장인",     "재직 중인 직장인",                    True],
        [4, "장애인",     "장애인복지법에 따른 등록 장애인",      True],
        [5, "기초수급자", "국민기초생활보장법상 수급자",          True],
        [6, "신규고객",   "당행 최초 가입 고객",                  True],
    ]
)

# ── 2-2. product_target_groups ───────────────────────────────────────────
sr = write_sample_table(ws2, sr, "상품 가입 대상 연결", "product_target_groups",
    [("상품 ID","product_id"), ("대상 그룹 ID","target_group_id")],
    [
        [1, 1],  # 정기예금 → 일반
        [2, 1],  # 시니어 정기예금 → 일반
        [3, 1],  # 자유적금 → 일반
        [4, 2],  # 청년 우대적금 → 청년
        [4, 3],  # 청년 우대적금 → 직장인 (복수 대상)
        [5, 1],  # 주택청약 → 일반
    ]
)

# ── 3. savings_products ───────────────────────────────────────────────
sr = write_sample_table(ws2, sr, "적금 상품", "savings_products",
    [("적금상품 ID","savings_product_id"), ("상품 ID","product_id"),
     ("적금유형","saving_type"),
     ("월납최소금액","monthly_payment_min_amount"), ("월납최대금액","monthly_payment_max_amount")],
    [
        [1, 3, "FREE",    10000, 1000000],
        [2, 4, "REGULAR", 10000, 500000],
    ]
)

# ── 4. subscription_products ──────────────────────────────────────────
sr = write_sample_table(ws2, sr, "청약 상품", "subscription_products",
    [("상품 ID","product_id"),
     ("월납입금액","monthly_payment_amount"), ("월납최소금액","min_monthly_payment"),
     ("월납최대금액","max_monthly_payment")],
    [
        [5, 20000, 2000, 200000],
    ]
)

# ── 4-1. product_join_channels ───────────────────────────────────────
sr = write_sample_table(ws2, sr, "상품 가입 방식", "product_join_channels",
    [("가입방식ID","product_join_channel_id"), ("상품 ID","product_id"),
     ("가입방식코드","join_channel_code")],
    [
        [1, 1, "BRANCH"],
        [2, 1, "WEB"],
        [3, 2, "MOBILE"],
        [4, 2, "WEB"],
    ]
)

# ── 5. product_interest_rates ─────────────────────────────────────────
sr = write_sample_table(ws2, sr, "상품 금리", "product_interest_rates",
    [("금리 ID","rate_id"), ("상품 ID","product_id"), ("금리유형","rate_type"),
     ("하한기간(월)","minimum_contract_period"), ("상한기간(월)","maximum_contract_period"),
     ("하한금액","minimum_join_amount"), ("상한금액","maximum_join_amount"),
     ("금리","rate"), ("조건설명","condition_description"),
     ("적용시작일","effective_start_date"), ("적용종료일","effective_end_date"), ("활성여부","is_active")],
    [
        # 상품 1 (예금): 가입 기간별 금리 다름 → PERIOD_BASE
        [ 1, 1,"PERIOD_BASE",       6,    12,   None, None, 2.80, "6~12개월 계약 기본 금리",      "20240101", None, True],
        [ 2, 1,"PERIOD_BASE",       12,   24,   None, None, 3.20, "12~24개월 계약 기본 금리",     "20240101", None, True],
        [ 3, 1,"PERIOD_BASE",       24,   None, None, None, 3.50, "24개월 이상 계약 기본 금리",   "20240101", None, True],
        [ 4, 1,"PREFERENTIAL",      None, None, None, None, 0.50, "급여이체 +0.5%",               "20240101", None, True],
        [ 5, 1,"PREFERENTIAL",      None, None, None, None, 0.30, "자동이체 +0.3%",               "20240101", None, True],
        [ 6, 1,"EARLY_TERMINATION", 0,    6,    None, None, 1.00, "6개월 미만 해지 시 적용",      "20240101", None, True],
        [ 7, 1,"EARLY_TERMINATION", 6,    12,   None, None, 2.00, "6~12개월 내 해지 시 적용",     "20240101", None, True],
        # 상품 3 (적금): 기간 무관 단일 기본 금리 → BASE
        [ 8, 3,"BASE",              None, None, None, None, 3.00, "기간 무관 단일 기본 금리",     "20240101", None, True],
        [ 9, 3,"PREFERENTIAL",      None, None, None, None, 1.00, "청년(만 19~34세) +1.0%",       "20240101", None, True],
        [10, 3,"PREFERENTIAL",      None, None, None, None, 0.50, "급여이체 +0.5%",               "20240101", None, True],
        # 상품 4 (청약): 기간 무관 단일 기본 금리 → BASE
        [11, 4,"BASE",              None, None, None, None, 3.50, "기간 무관 단일 기본 금리",     "20240601", None, True],
        [12, 4,"PREFERENTIAL",      None, None, None, None, 1.50, "청년 +1.0%, 급여이체 +0.5%",  "20240601", None, True],
    ]
)

# ── 6. deposit_contracts (계약) ───────────────────────────────────────
sr = write_sample_table(ws2, sr, "계약", "deposit_contracts",
    [("계약 ID","contract_id"), ("계약번호","contract_number"), ("고객 ID","customer_id"),
     ("상품 ID","product_id"), ("상품유형","product_type"),
     ("가입금액","join_amount"), ("기본금리","base_interest_rate"),
     ("우대금리","preferential_interest_rate"),
     ("자동이체충족","is_auto_transfer"), ("급여이체충족","is_salary_transfer"),
     ("최종금리","final_interest_rate"),
     ("세제혜택유형","tax_benefit_type"), ("적용세율","applied_tax_rate"),
     ("계약기간(월)","contract_period_month"),
     ("계약 시작일","started_at"), ("계약 만기일","maturity_at"), ("계약상태","contract_status"),
     ("가입채널","join_channel"), ("가입지점코드","branch_code")],
    [
        [1,"CTR-20240102-0001","CUST-001",1,"DEPOSIT",    10000000,3.50,1.50,True, True, 5.00,"GENERAL",    0.154,12,"2024-01-02","2025-01-02","MATURED","BRANCH","BR-001"],
        [2,"CTR-20240301-0002","CUST-002",2,"DEPOSIT",    5000000, 4.00,1.50,True, False,5.50,"NON_TAXABLE", 0,   12,"2024-03-01","2025-03-01","ACTIVE", "ONLINE", None],
        [3,"CTR-20240115-0003","CUST-003",3,"SAVINGS",    None,    3.00,1.50,True, False,4.50,"GENERAL",    0.154,24,"2024-01-15","2026-01-15","ACTIVE", "MOBILE", None],
        [4,"CTR-20240601-0004","CUST-004",4,"SAVINGS",    None,    3.50,2.50,True, True, 6.00,"REDUCED_TAX",0.099,24,"2024-06-01","2026-06-01","ACTIVE", "BRANCH","BR-002"],
        [5,"CTR-20240201-0005","CUST-005",5,"SUBSCRIPTION",None,  2.50,0,   False,False,2.50,"GENERAL",    0.154,None,"2024-02-01",None,"ACTIVE", "BRANCH","BR-001"],
    ]
)

# ── 7. accounts (계좌) ────────────────────────────────────────────────
sr = write_sample_table(ws2, sr, "계좌", "accounts",
    [("계좌 ID","account_id"), ("계좌번호","account_number"), ("고객 ID","customer_id"),
     ("계좌유형","account_type"),
     ("잔액","balance"), ("누적납입금액","total_paid_amount"),
     ("총이자금액","total_interest_amount"), ("통화","currency"),
     ("계좌상태","account_status"), ("개설일시","opened_at")],
    [
        [1,"110-123-456789","CUST-001","DEPOSIT",    10500000,10000000,500000,"KRW","CLOSED","2024-01-02"],
        [2,"110-234-567890","CUST-002","DEPOSIT",    5000000, 5000000, 0,     "KRW","ACTIVE","2024-03-01"],
        [3,"110-456-789012","CUST-003","SAVINGS",    360000,  360000,  0,     "KRW","ACTIVE","2024-01-15"],
        [4,"110-567-890123","CUST-004","SAVINGS",    240000,  240000,  0,     "KRW","ACTIVE","2024-06-01"],
        [5,"110-678-901234","CUST-005","SUBSCRIPTION",880000,880000,   0,     "KRW","ACTIVE","2024-02-01"],
    ]
)

# ── 8. interest_history (이자 내역) ───────────────────────────────────
sr = write_sample_table(ws2, sr, "이자 내역", "interest_history",
    [("이자 ID","interest_id"), ("계약 ID","contract_id"), ("계좌 ID","account_id"),
     ("적용금리","applied_interest_rate"),
     ("세전이자","interest_before_tax"), ("이자소득세","interest_tax_amount"),
     ("지방소득세","local_income_tax_amount"), ("세후이자","interest_after_tax"),
     ("세제혜택유형","tax_benefit_type"), ("적용세율","applied_tax_rate"),
     ("이자발생사유","interest_reason"), ("이자지급일시","interest_paid_at")],
    [
        [1, 1, 1, 5.00, 500000, 70000, 7000, 423000, "GENERAL", 0.154, "MATURITY_INTEREST", "2025-01-02"],
    ]
)

# ── 8-1. contract_applied_rates (계약 우대 금리 적용 내역) ───────────
sr = write_sample_table(ws2, sr, "계약 우대 금리 적용 내역", "contract_applied_rates",
    [("적용 내역 ID","applied_rate_id"), ("계약 ID","contract_id"),
     ("금리 ID","rate_id"), ("적용 금리","applied_rate"), ("생성 일시","created_at")],
    [
        [1, 1, 2, 1.00, "2024-01-02"],
        [2, 1, 3, 0.50, "2024-01-02"],
        [3, 3, 7, 1.50, "2024-01-15"],
    ]
)

# ── 9. special_terms (수신 특약) ─────────────────────────────────────
sr = write_sample_table(ws2, sr, "수신 특약", "special_terms",
    [("특약 ID","special_term_id"),
     ("특약명","special_term_name"), ("필수여부","is_required"),
     ("전자동의가능","is_electronic_agreement_allowed"),
     ("특약버전","special_term_version"), ("상태","status")],
    [
        [1, "급여이체 우대 금리 특약", False, True, "v1.0", "ACTIVE"],
    ]
)

# ── 11. product_special_terms (수신 상품 특약 연결) ──────────────────
sr = write_sample_table(ws2, sr, "수신 상품 특약 연결", "product_special_terms",
    [("연결 ID","product_special_term_id"), ("상품 ID","product_id"),
     ("특약 ID","special_term_id"), ("필수여부","is_required")],
    [
        [1, 1, 1, False],
    ]
)

# ── 12. contract_special_term_agreements (수신 특약 동의) ────────────
sr = write_sample_table(ws2, sr, "수신 특약 동의", "contract_special_term_agreements",
    [("동의 ID","special_agreement_id"), ("계약 ID","contract_id"),
     ("특약 ID","special_term_id"), ("동의여부","is_agreed"),
     ("동의일시","agreed_at"), ("전자서명여부","is_electronic_signed"),
     ("동의철회여부","is_agreement_withdrawn")],
    [
        [1, 1, 1, True, "2024-01-02 10:20:00", True, False],
        [2, 1, 2, True, "2024-01-02 10:20:00", True, False],
    ]
)

# ── 13. special_term_history (수신 특약 이력) ─────────────────────────
sr = write_sample_table(ws2, sr, "수신 특약 이력", "special_term_history",
    [("이력 ID","history_id"), ("특약 ID","special_term_id"),
     ("이전버전","previous_version"), ("변경버전","changed_version"),
     ("변경사유","change_reason"), ("변경일시","changed_at")],
    [
        [1, 1, "v1.0", "v1.1", "우대 금리 조건 문구 수정", "2024-06-01 09:00:00"],
    ]
)

# ── 14. departments (부서) ────────────────────────────────────────────
sr = write_sample_table(ws2, sr, "부서", "departments",
    [("부서 ID","department_id"), ("부서코드","department_code"),
     ("부서명","department_name"), ("상위부서 ID","parent_department_id"),
     ("부서유형","department_type"), ("사용여부","is_active")],
    [
        [1,  "DEPT-001", "수신상품부",   None, "PRODUCT",    True],
        [2,  "DEPT-002", "청약사업부",   None, "PRODUCT",    True],
        [3,  "DEPT-003", "기업금융부",   None, "CORPORATE",  True],
        [4,  "DEPT-004", "펀드자산부",   None, "FUND",       True],
        [5,  "DEPT-005", "보험상품부",   None, "INSURANCE",  True],
        [6,  "DEPT-006", "개인영업부",   None, "SALES",      True],
        [7,  "DEPT-007", "기업영업부",   3,    "SALES",      True],
        [8,  "DEPT-008", "리스크관리부", None, "RISK",       True],
        [9,  "DEPT-009", "IT운영부",    None, "IT",         True],
        [10, "DEPT-010", "디지털뱅킹부", 9,    "IT",         True],
    ]
)

# ── 15. transactions (거래 내역) ─────────────────────────────────────────
sr = write_sample_table(ws2, sr, "거래 내역", "transactions",
    [("거래 ID","transaction_id"), ("거래 번호","transaction_number"),
     ("계좌 ID","account_id"), ("계약 ID","contract_id"),
     ("거래 유형","transaction_type"), ("입출금 구분","direction_type"),
     ("거래 금액","amount"), ("거래 전 잔액","balance_before"),
     ("거래 후 잔액","balance_after"), ("수수료","fee_amount"),
     ("거래 채널","channel_type"), ("거래 상태","status"),
     ("거래 일시","transaction_at"), ("입금자 ID","depositor_customer_id"),
     ("입금자명","depositor_name"), ("위임받은 사람 ID","delegate_customer_id"),
     ("위임받은 사람명","delegate_customer_name")],
    [
        [1, "TXN-20240102-000001", 1, None,   "DEPOSIT",           "IN",  10000000, 0,        10000000, 0, "BRANCH",   "SUCCESS", "2024-01-02 09:00:00", "CUST-001", "홍길동", None, None],
        [2, "TXN-20250102-000001", 1, 1,       "MATURITY_INTEREST", "IN",  500000,   10000000, 10500000, 0, "SYSTEM",   "SUCCESS", "2025-01-02 00:00:00", None, None, None, None],
        [3, "TXN-20240301-000001", 2, None,   "DEPOSIT",           "IN",  5000000,  0,        5000000,  0, "MOBILE",   "SUCCESS", "2024-03-01 10:30:00", "CUST-002", "김수신", "CUST-009", "박대리"],
        [4, "TXN-20240115-000001", 3, 3,       "DEPOSIT",           "IN",  30000,    330000,   360000,   0, "INTERNET", "SUCCESS", "2024-01-15 11:00:00", "CUST-003", "이청약", None, None],
        [5, "TXN-20240202-000001", 5, None,   "DEPOSIT",           "IN",  100000,   780000,   880000,   0, "ATM",      "SUCCESS", "2024-02-02 14:20:00", "CUST-005", "최입금", None, None],
        [6, "TXN-20240203-000001", 2, None,   "TRANSFER",          "OUT", 500000,   5000000,  4500000,  500,"INTERNET", "SUCCESS", "2024-02-03 09:15:00", None, None, "CUST-010", "정위임"],
    ]
)

# ─────────────────────────────────────────────────────────────────────────
# 시나리오 시트
# ─────────────────────────────────────────────────────────────────────────
ws3 = wb.create_sheet("유스케이스 시나리오")

# 열 너비
ws3.column_dimensions["A"].width = 6
ws3.column_dimensions["B"].width = 22
ws3.column_dimensions["C"].width = 14
ws3.column_dimensions["D"].width = 12
ws3.column_dimensions["E"].width = 32
ws3.column_dimensions["F"].width = 60
ws3.column_dimensions["G"].width = 40
ws3.column_dimensions["H"].width = 50

# 스타일
hdr_font   = Font(bold=True, size=10)
hdr_fill   = PatternFill("solid", fgColor="1F4E79")
hdr_font_w = Font(bold=True, size=10, color="FFFFFF")
sub_fill   = PatternFill("solid", fgColor="D6E4F0")
sub_font   = Font(bold=True, size=10)
thin       = Side(style="thin", color="BFBFBF")
thin_border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap_align  = Alignment(wrap_text=True, vertical="top")
center_top  = Alignment(horizontal="center", vertical="top", wrap_text=True)

def sc_cell(ws, r, c, val, font=None, fill=None, align=None, border=None):
    cell = ws.cell(row=r, column=c, value=val)
    if font:   cell.font   = font
    if fill:   cell.fill   = fill
    if align:  cell.alignment = align
    if border: cell.border = border
    return cell

# 제목 행
title_headers = ["번호","시나리오명","구분","행위자","사전 조건","단계별 흐름","예외/대안 흐름","관련 테이블"]
for ci, h in enumerate(title_headers, 1):
    c = sc_cell(ws3, 1, ci, h, font=hdr_font_w, fill=hdr_fill, align=center_top, border=thin_border)

ws3.row_dimensions[1].height = 22

SCENARIOS = [
    {
        "no": "SC-01",
        "name": "예금 상품 가입",
        "type": "정상 흐름",
        "actor": "고객",
        "precond": "- 상품 조회 완료\n- 예금 상품(product_type=DEPOSIT) 선택",
        "steps": (
            "1. 고객이 예금 상품 목록 조회\n"
            "2. 원하는 상품 선택 → products 조회\n"
            "3. 특약 목록 확인 (product_special_terms → special_terms)\n"
            "4. 특약 동의 여부 선택\n"
            "5. 가입 금액·기간 입력\n"
            "6. deposit_contracts 레코드 생성 (product_type=DEPOSIT)\n"
            "7. accounts 레코드 생성 (계좌 개설)\n"
            "8. contract_special_term_agreements 저장\n"
            "9. 가입 확인서 출력"
        ),
        "alt": (
            "- 최소 가입 금액 미달 → 오류 메시지\n"
            "- 필수 특약 미동의 → 가입 불가\n"
            "- 가입 기간 범위 초과 → 오류"
        ),
        "tables": "products, deposit_products,\ndeposit_contracts, accounts,\nspecial_terms, product_special_terms,\ncontract_special_term_agreements",
    },
    {
        "no": "SC-02",
        "name": "적금 상품 가입",
        "type": "정상 흐름",
        "actor": "고객",
        "precond": "- 적금 상품(product_type=SAVINGS) 선택\n- 자동이체 출금 계좌 보유",
        "steps": (
            "1. 적금 상품 목록 조회\n"
            "2. 납입 방식 선택 (정액/자유)\n"
            "3. 월 납입금·기간 입력\n"
            "4. savings_products 조회 → 월 한도 검증\n"
            "5. deposit_contracts 레코드 생성 (product_type=SAVINGS)\n"
            "6. accounts 레코드 생성\n"
            "7. 자동이체 사용 여부·이체일 설정 (deposit_contracts 저장)\n"
            "8. contract_special_term_agreements 저장\n"
            "9. 가입 완료 알림"
        ),
        "alt": (
            "- 월 납입 한도 초과 → 오류\n"
            "- 자유납입 상품에서 0원 납입 → 경고\n"
            "- 자동이체 계좌 잔액 부족 시 → 납입 실패 처리"
        ),
        "tables": "products, savings_products,\ndeposit_contracts, accounts,\nspecial_terms, product_special_terms,\ncontract_special_term_agreements",
    },
    {
        "no": "SC-03",
        "name": "청약 상품 가입",
        "type": "정상 흐름",
        "actor": "고객",
        "precond": "- 청약 상품(product_type=SUBSCRIPTION) 선택\n- 1인 1계좌 제한 확인",
        "steps": (
            "1. 청약 상품 조회 (subscription_products)\n"
            "2. 불입 계획 입력 (금액, 회수)\n"
            "3. 1인 1계좌 여부 검증\n"
            "4. deposit_contracts 레코드 생성 (product_type=SUBSCRIPTION)\n"
            "5. accounts 레코드 생성\n"
            "6. 특약 동의 처리\n"
            "7. 가입 완료 확인서 발급"
        ),
        "alt": (
            "- 이미 청약 계좌 보유 시 → 가입 불가\n"
            "- 최소 불입 금액 미달 → 오류\n"
            "- 최대 불입 금액 초과 → 오류"
        ),
        "tables": "products, subscription_products,\ndeposit_contracts, accounts,\ncontract_special_term_agreements",
    },
    {
        "no": "SC-04",
        "name": "금리 조회 및 우대금리 확인",
        "type": "정상 흐름",
        "actor": "고객",
        "precond": "- 상품 선택 완료",
        "steps": (
            "1. products.base_interest_rate 조회 (기본금리)\n"
            "2. product_interest_rates 조회 → 구간별 금리 확인\n"
            "   (rate_range_min ~ rate_range_max 구간에 납입금액 해당 여부)\n"
            "3. 충족된 우대 조건별 PREFERENTIAL 금리 합산 → 최고 금리 계산\n"
            "4. 계약 체결 시 deposit_contracts.final_interest_rate에 기록"
        ),
        "alt": (
            "- 우대금리 조건 미충족 → 기본금리만 적용\n"
            "- 금리 구간에 해당 없음 → 기본금리 적용"
        ),
        "tables": "products, product_interest_rates,\ndeposit_contracts",
    },
    {
        "no": "SC-05",
        "name": "이자 계산 및 지급",
        "type": "정상 흐름",
        "actor": "시스템 (배치)",
        "precond": "- 계약 상태 ACTIVE\n- 이자 지급일 도래",
        "steps": (
            "1. 배치 스케줄러가 이자 지급 대상 계약 조회\n"
            "2. deposit_contracts.final_applied_rate 기준으로 이자 계산\n"
            "3. 세금 유형 확인 (일반과세 15.4% / 비과세 / 세금우대)\n"
            "4. 세전/세후 이자 계산\n"
            "5. interest_history 레코드 생성\n"
            "6. accounts.current_balance 업데이트\n"
            "7. 이자 지급 완료 알림"
        ),
        "alt": (
            "- 계좌 동결 상태 → 이자 지급 보류\n"
            "- 계산 오류 → 이자 지급 실패 로그 기록"
        ),
        "tables": "deposit_contracts, accounts,\ninterest_history",
    },
    {
        "no": "SC-06",
        "name": "만기 처리",
        "type": "정상 흐름",
        "actor": "시스템 (배치) / 고객",
        "precond": "- 계약 상태 ACTIVE\n- 만기일(maturity_date) 도래",
        "steps": (
            "1. 배치 스케줄러가 만기 도래 계약 조회\n"
            "2. 최종 이자 계산 → interest_history 저장\n"
            "3. deposit_contracts.status → MATURED 업데이트\n"
            "4. accounts.status → CLOSED 업데이트\n"
            "5. 원금 + 세후 이자 합산 → 연결 출금 계좌로 이체\n"
            "6. accounts.closed_at 기록\n"
            "7. 만기 도래 알림 발송"
        ),
        "alt": (
            "- 자동 재예치 설정 → 신규 계약 자동 생성\n"
            "- 연결 계좌 없음 → 고객 확인 후 수동 처리\n"
            "- 만기 전 고객이 수동 해지 요청 → SC-07로 이동"
        ),
        "tables": "deposit_contracts, accounts,\ninterest_history",
    },
    {
        "no": "SC-07",
        "name": "중도 해지",
        "type": "정상 흐름",
        "actor": "고객",
        "precond": "- 계약 상태 ACTIVE\n- 만기일 이전",
        "steps": (
            "1. 고객이 중도 해지 요청\n"
            "2. 중도 해지 이율 조회 (deposit_contracts.early_termination_rate)\n"
            "3. 중도 해지 이자 계산 및 interest_history 저장\n"
            "4. deposit_contracts.status → EARLY_TERMINATED 업데이트\n"
            "5. deposit_contracts.closed_at 기록\n"
            "6. accounts.status → CLOSED 업데이트\n"
            "7. 원금 + 중도해지 이자 지급\n"
            "8. 해지 확인서 발급"
        ),
        "alt": (
            "- 질권 설정 계좌 → 해지 불가 (권리자 동의 필요)\n"
            "- 중도 해지 수수료 차감 후 지급"
        ),
        "tables": "deposit_contracts, accounts,\ninterest_history",
    },
    {
        "no": "SC-08",
        "name": "특약 동의 및 우대금리 적용",
        "type": "정상 흐름",
        "actor": "고객",
        "precond": "- 가입 진행 중 (SC-01~03 연계)\n- 우대금리 특약 존재",
        "steps": (
            "1. product_special_terms 조회 → 상품별 특약 목록 확인\n"
            "2. 고객이 특약 조건 확인\n"
            "3. 특약 동의 여부 선택 (is_agreed)\n"
            "4. contract_special_term_agreements 저장\n"
            "5. 동의한 특약의 우대금리 합산\n"
            "6. deposit_contracts.final_applied_rate에 반영\n"
            "7. 특약 이력 변경 시 → special_term_history 추가"
        ),
        "alt": (
            "- 필수 특약(is_required=true) 미동의 → 가입 불가\n"
            "- 전자 동의 불가 상품 → 서면 동의서 처리\n"
            "- 특약 버전 변경 시 → 기존 동의 무효화 여부 확인"
        ),
        "tables": "special_terms, product_special_terms,\ncontract_special_term_agreements,\nspecial_term_history, deposit_contracts",
    },
]

for i, sc in enumerate(SCENARIOS, 2):
    fill = sub_fill if i % 2 == 0 else PatternFill("solid", fgColor="FFFFFF")
    vals = [sc["no"], sc["name"], sc["type"], sc["actor"],
            sc["precond"], sc["steps"], sc["alt"], sc["tables"]]
    for ci, val in enumerate(vals, 1):
        font = sub_font if ci <= 4 else Font(size=9)
        sc_cell(ws3, i, ci, val,
                font=font,
                fill=fill,
                align=wrap_align if ci > 4 else center_top,
                border=thin_border)
    # 행 높이: 흐름 단계 수 기준
    step_lines = sc["steps"].count("\n") + 1
    ws3.row_dimensions[i].height = max(step_lines * 14, 60)

# ── 저장 ─────────────────────────────────────────────────────────────────
output_path = r"C:\Users\green\Desktop\teamproject\teamproject.xlsx"
wb.save(output_path)
print(f"저장 완료: {output_path}")


