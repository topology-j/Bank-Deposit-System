import requests
import json

BASE = "http://localhost:8000"

ok = 0
fail = 0

def check(name, resp, expected_status, check_fn=None):
    global ok, fail
    passed = resp.status_code == expected_status
    if passed and check_fn:
        try:
            passed = check_fn(resp.json())
        except Exception:
            passed = False
    status = "OK" if passed else "FAIL"
    if passed:
        ok += 1
    else:
        fail += 1
    try:
        body = json.dumps(resp.json(), ensure_ascii=False)[:160]
    except Exception:
        body = resp.text[:160]
    print(f"[{status}] {name} (HTTP {resp.status_code}) {body}")
    return resp

# ── 1. 부서 생성
r = check("부서 생성", requests.post(f"{BASE}/api/deposit_departments", json={
    "department_name": "수신상품팀",
    "department_code": "DEP001",
    "department_type": "PRODUCT",
    "is_active": "Y"
}), 201, lambda d: d.get("department_id", 0) >= 1 and d.get("is_active") == "Y")
dept_id = r.json().get("department_id", 1)

# ── 2. 수신 상품(BankingProduct) 생성
r = check("수신상품 생성", requests.post(f"{BASE}/api/deposit_banking_products", json={
    "deposit_product_type": "DEPOSIT",
    "deposit_product_name": "테스트정기예금",
    "base_interest_rate": 3.5,
    "department_id": dept_id,
    "deposit_product_status": "SELLING",
    "is_early_termination_allowed": "Y",
    "is_tax_benefit_available": "N",
    "is_auto_renewal_available": "Y",
    "is_passbook_issued": "N",
    "released_at": "20240101"
}), 201, lambda d: d.get("banking_product_id", 0) >= 1
          and d.get("is_early_termination_allowed") == "Y"
          and d.get("is_passbook_issued") == "N")
bp_id = r.json().get("banking_product_id", 1)

# ── 3. 예금 상품(DepositProduct) 생성
r = check("예금상품 생성", requests.post(f"{BASE}/api/banking_deposit_products", json={
    "banking_product_id": bp_id,
    "deposit_type": "TERM",
    "is_compound_interest": "N"
}), 201, lambda d: d.get("is_compound_interest") == "N")

# ── 4. 적금용 수신상품 생성
r = check("적금수신상품 생성", requests.post(f"{BASE}/api/deposit_banking_products", json={
    "deposit_product_type": "SAVINGS",
    "deposit_product_name": "테스트자유적금",
    "base_interest_rate": 4.0,
    "deposit_product_status": "SELLING",
    "is_early_termination_allowed": "Y",
    "is_tax_benefit_available": "N",
    "is_auto_renewal_available": "N",
    "is_passbook_issued": "N"
}), 201)
bp_id2 = r.json().get("banking_product_id", 2)

# ── 5. 적금 상품(SavingsProduct) 생성
r = check("적금상품 생성", requests.post(f"{BASE}/api/deposit_savings_products", json={
    "banking_product_id": bp_id2,
    "saving_type": "FREE",
    "monthly_payment_min": 10000,
    "monthly_payment_max": 1000000
}), 201)

# ── 6. 금리 생성
r = check("금리 생성", requests.post(f"{BASE}/api/banking_deposit_product_interest_rates", json={
    "banking_product_id": bp_id,
    "rate_type": "BASE",
    "rate": 3.5,
    "effective_start_date": "2024-01-01",
    "is_active": "Y"
}), 201, lambda d: d.get("is_active") == "Y")
rate_id = r.json().get("rate_id", 1)

# ── 7. 특약 생성
r = check("특약 생성", requests.post(f"{BASE}/api/deposit_special_terms", json={
    "special_term_name": "일반약관",
    "special_term_code": "ST001",
    "is_required": "Y",
    "status": "ACTIVE"
}), 201, lambda d: d.get("is_required") == "Y")
st_id = r.json().get("special_term_id", 1)

# ── 8. 계약+계좌 동시 생성 (서비스 레이어)
r = check("계약+계좌 생성", requests.post(f"{BASE}/deposit_contracts", json={
    "customer_id": "CUST001",
    "banking_product_id": bp_id,
    "contract_period_month": 12,
    "maturity_at": "20250101",
    "started_at": "20240101",
    "join_channel": "WEB",
    "is_auto_renewal": "N",
    "is_proxy_joined": "N",
    "is_power_of_attorney_verified": "N"
}), 201, lambda d: d.get("contract_id", 0) >= 1
          and d.get("is_auto_renewal") == "N")
contract_id = r.json().get("contract_id", 1)

# ── 9. 계좌 목록 조회
r = check("계좌 목록 조회", requests.get(f"{BASE}/api/deposit_accounts"), 200,
    lambda d: len(d) >= 1)
account_id = r.json()[0]["account_id"]

# ── 10. 입금
r = check("입금 100000", requests.post(f"{BASE}/deposit_transactions/deposit", json={
    "account_id": account_id, "amount": 100000
}), 201, lambda d: float(d.get("amount", 0)) == 100000.0 and d.get("direction_type") == "IN")

# ── 11. 잔액 확인 (입금 후)
r = check("잔액 100000 확인", requests.get(f"{BASE}/api/deposit_accounts/{account_id}"), 200,
    lambda d: float(d.get("balance", -1)) == 100000.0)

# ── 12. 출금
r = check("출금 30000", requests.post(f"{BASE}/deposit_transactions/withdraw", json={
    "account_id": account_id, "amount": 30000
}), 201, lambda d: d.get("direction_type") == "OUT")
tx_id = r.json().get("transaction_id", 1)

# ── 13. 잔액 확인 (출금 후)
r = check("잔액 70000 확인", requests.get(f"{BASE}/api/deposit_accounts/{account_id}"), 200,
    lambda d: float(d.get("balance", -1)) == 70000.0)

# ── 14. 거래 취소(reversal)
r = check("거래 취소(reversal)", requests.post(f"{BASE}/deposit_transactions/{tx_id}/reversal", json={}), 201,
    lambda d: d.get("transaction_type") == "REVERSAL")

# ── 15. 잔액 확인 (취소 후 복원)
r = check("잔액 100000 복원 확인", requests.get(f"{BASE}/api/deposit_accounts/{account_id}"), 200,
    lambda d: float(d.get("balance", -1)) == 100000.0)

# ── 16. 이자 지급
r = check("이자 지급 1500", requests.post(f"{BASE}/interests/pay", json={
    "account_id": account_id,
    "contract_id": contract_id,
    "interest_amount": 1500,
    "interest_before_tax": 1769,
    "interest_tax_amount": 269,
    "applied_interest_rate": 3.5
}), 201, lambda d: float(d.get("interest_after_tax", 0)) == 1500.0)

# ── 17. 잔액 확인 (이자 후)
r = check("잔액 101500 확인", requests.get(f"{BASE}/api/deposit_accounts/{account_id}"), 200,
    lambda d: float(d.get("balance", -1)) == 101500.0)

# ── 18. 외부 이체
r = check("외부 이체 5000", requests.post(f"{BASE}/deposit_transactions/transfer", json={
    "account_id": account_id,
    "amount": 5000,
    "transfer_type": "EXTERNAL",
    "counterparty_bank_code": "020",
    "counterparty_bank_name": "우리은행",
    "counterparty_account_no": "1002-001-234567",
    "counterparty_name": "홍길동"
}), 201, lambda d: d.get("transaction_type") == "TRANSFER")

# ── 19. 상품 상태 변경
r = check("상품상태 SUSPENDED 변경", requests.patch(f"{BASE}/deposit_banking_products/{bp_id}/status", json={
    "deposit_product_status": "SUSPENDED"
}), 200, lambda d: d.get("deposit_product_status") == "SUSPENDED")

# ── 20. 약관 적용 관리 - 생성
r = check("약관적용관리 생성", requests.post(f"{BASE}/api/deposit_term_application_management", json={
    "common_term_id": 1,
    "term_target_id": bp_id,
    "business_type_code": "DEPOSIT",
    "is_required": "Y",
    "registered_at": "20240101",
    "modified_at": "20240101"
}), 201, lambda d: d.get("term_application_id", 0) >= 1 and d.get("is_required") == "Y")
tam_id = r.json().get("term_application_id", 1)

# ── 21. 약관 적용 관리 - 단건 조회
r = check("약관적용관리 단건 조회", requests.get(f"{BASE}/api/deposit_term_application_management/{tam_id}"), 200,
    lambda d: d.get("business_type_code") == "DEPOSIT" and d.get("is_required") == "Y")

# ── 22. 약관 적용 관리 - 수정
r = check("약관적용관리 수정", requests.patch(f"{BASE}/api/deposit_term_application_management/{tam_id}", json={
    "business_type_code": "SAVINGS",
    "is_required": "N",
    "modified_at": "20240601"
}), 200, lambda d: d.get("business_type_code") == "SAVINGS" and d.get("is_required") == "N")

# ── 23. 약관 적용 관리 - 목록 조회
r = check("약관적용관리 목록 조회", requests.get(f"{BASE}/api/deposit_term_application_management"), 200,
    lambda d: len(d) >= 1)

# ── 24. 약관 적용 관리 - 삭제
r = check("약관적용관리 삭제", requests.delete(f"{BASE}/api/deposit_term_application_management/{tam_id}"), 204)

# ── 25. 약관 적용 관리 - 삭제 후 404
r = check("약관적용관리 삭제 후 404", requests.get(f"{BASE}/api/deposit_term_application_management/{tam_id}"), 404)

# ── 26. 결제(payment)
r = check("결제 2000", requests.post(f"{BASE}/deposit_transactions/payment", json={
    "account_id": account_id,
    "amount": 2000,
    "merchant_id": "MRC001",
    "merchant_name": "스타벅스",
    "payment_method": "ACCOUNT_TRANSFER"
}), 201, lambda d: d.get("transaction_type") == "PAYMENT")

# ── 27. 적금계좌 계약+계좌 생성
r2 = check("적금 계약+계좌 생성", requests.post(f"{BASE}/deposit_contracts", json={
    "customer_id": "CUST002",
    "banking_product_id": bp_id2,
    "contract_period_month": 12,
    "maturity_at": "20250201",
    "started_at": "20240201",
    "join_channel": "MOBILE",
    "is_auto_renewal": "N",
    "is_proxy_joined": "N",
    "is_power_of_attorney_verified": "N"
}), 201)
sav_contract_id = r2.json().get("contract_id")

# ── 28. 적금계좌 조회
r3 = check("적금계좌 목록 조회", requests.get(f"{BASE}/api/deposit_accounts?limit=10"), 200)
accounts = r3.json()
sav_account_id = None
for a in accounts:
    if str(a.get("contract_id")) == str(sav_contract_id):
        sav_account_id = a["account_id"]
        break

# ── 29. 적금계좌 입금 (납입 전 잔액 확보)
if sav_account_id:
    check("적금계좌 입금 100000", requests.post(f"{BASE}/deposit_transactions/deposit", json={
        "account_id": sav_account_id, "amount": 100000
    }), 201)

    # ── 30. 적금 납입
    r = check("적금 납입 50000", requests.post(f"{BASE}/deposit_transactions/savings-payment", json={
        "account_id": sav_account_id,
        "amount": 50000,
        "payment_round": 1
    }), 201, lambda d: d.get("transaction_type") == "SAVINGS_PAYMENT")
else:
    print("[SKIP] 적금 납입 - 계좌 못찾음")

# ── 31. CHAR(1) 타입 반환 검증 - is_online_banking_enabled 'Y' 확인
r = check("CHAR(1) 타입 검증(is_online_banking_enabled=Y)", requests.get(f"{BASE}/api/deposit_accounts/{account_id}"), 200,
    lambda d: d.get("is_online_banking_enabled") == "Y"
              and d.get("is_mobile_banking_enabled") == "Y"
              and d.get("is_phone_banking_enabled") == "N")

# ── 32. CHAR(8) 날짜 필드 검증
r = check("CHAR(8) 날짜 필드 검증(opened_at 8자리)", requests.get(f"{BASE}/api/deposit_accounts/{account_id}"), 200,
    lambda d: len(d.get("opened_at", "")) == 8)

# ── 33. TIMESTAMPTZ(3) 타입 검증 - created_at 밀리초 포함 확인
r = check("TIMESTAMPTZ(3) 검증(created_at 밀리초)", requests.get(f"{BASE}/api/deposit_accounts/{account_id}"), 200,
    lambda d: "." in d.get("created_at", "") and "T" in d.get("created_at", ""))

# ── 34. 전체 테이블 19개 확인
r = check("테이블 19개 확인", requests.get(f"{BASE}/api/meta/tables"), 200,
    lambda d: len(d.get("tables", [])) == 19)

# ── 35. 없는 테이블 404
r = check("없는 테이블 404", requests.get(f"{BASE}/api/nonexistent_table"), 404)

# ── 36. 잔액 부족 출금 400
r = check("잔액 부족 출금 400", requests.post(f"{BASE}/deposit_transactions/withdraw", json={
    "account_id": account_id,
    "amount": 9999999
}), 400)

print()
print("=" * 60)
print(f"  최종 결과: {ok} 성공 / {fail} 실패 / 전체 {ok+fail}")
print("=" * 60)
