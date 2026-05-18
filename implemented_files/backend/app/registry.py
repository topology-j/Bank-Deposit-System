from app import models


TABLES = {
    "departments": (models.Department, "department_id"),
    "products": (models.Product, "product_id"),
    "deposit_products": (models.DepositProduct, "deposit_product_id"),
    "savings_products": (models.SavingsProduct, "savings_product_id"),
    "subscription_products": (models.SubscriptionProduct, "subscription_product_id"),
    "product_join_channels": (models.ProductJoinChannel, "channel_id"),
    "target_groups": (models.TargetGroup, "target_group_id"),
    "product_target_groups": (models.ProductTargetGroup, "product_target_group_id"),
    "product_interest_rates": (models.ProductInterestRate, "rate_id"),
    "special_terms": (models.SpecialTerm, "special_term_id"),
    "product_special_terms": (models.ProductSpecialTerm, "product_special_term_id"),
    "contracts": (models.Contract, "contract_id"),
    "contract_applied_rates": (models.ContractAppliedRate, "applied_rate_id"),
    "contract_special_term_agreements": (models.ContractSpecialTermAgreement, "agreement_id"),
    "subscription_payment_recognition_history": (models.SubscriptionPaymentRecognitionHistory, "recognition_id"),
    "accounts": (models.Account, "account_id"),
    "interest_history": (models.InterestHistory, "interest_id"),
    "transactions": (models.Transaction, "transaction_id"),
}
