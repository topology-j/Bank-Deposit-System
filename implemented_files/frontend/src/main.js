import { createApp } from 'vue'
import {
  Banknote,
  Boxes,
  Building2,
  FileText,
  Landmark,
  LayoutDashboard,
  ReceiptText,
  ShieldCheck,
  Sparkles,
} from 'lucide-vue-next'
import './style.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const sections = [
  { key: 'dashboard', label: '대시보드', icon: LayoutDashboard },
  { key: 'products', label: '상품 관리', icon: Boxes },
  { key: 'contracts', label: '계약/계좌', icon: FileText },
  { key: 'transactions', label: '거래 처리', icon: Banknote },
  { key: 'interest', label: '이자 내역', icon: Sparkles },
  { key: 'terms', label: '특약 관리', icon: ShieldCheck },
  { key: 'admin', label: '부서/대상', icon: Building2 },
]

const tableGroups = {
  products: ['products', 'deposit_products', 'savings_products', 'subscription_products', 'product_join_channels', 'product_interest_rates'],
  contracts: ['contracts', 'accounts', 'contract_applied_rates', 'contract_special_term_agreements', 'subscription_payment_recognition_history'],
  interest: ['interest_history'],
  terms: ['special_terms', 'product_special_terms'],
  admin: ['departments', 'target_groups', 'product_target_groups'],
  transactions: ['transactions'],
}

const formFields = {
  products: ['product_type', 'product_name', 'department_id', 'base_interest_rate', 'product_status'],
  departments: ['department_name', 'department_code', 'department_type', 'parent_department_id', 'is_active'],
  target_groups: ['target_group_name', 'description', 'is_active'],
  special_terms: ['special_term_name', 'special_term_code', 'term_version', 'is_required', 'status'],
  contracts: ['customer_id', 'product_id', 'contract_period_month', 'maturity_at', 'join_channel', 'initial_balance'],
  accounts: ['account_number', 'customer_id', 'contract_id', 'account_type', 'balance', 'opened_at'],
  transactions: [
    'account_id',
    'contract_id',
    'transaction_type',
    'direction_type',
    'amount',
    'channel_type',
    'depositor_customer_id',
    'depositor_name',
    'delegate_customer_id',
    'delegate_customer_name',
    'transaction_memo',
    'transaction_summary',
  ],
}

const defaults = {
  product_type: 'DEPOSIT',
  product_status: 'SELLING',
  department_type: 'PRODUCT',
  is_active: true,
  is_required: false,
  status: 'ACTIVE',
  join_channel: 'WEB',
  transaction_type: 'DEPOSIT',
  direction_type: 'IN',
  channel_type: 'INTERNET',
  amount: 10000,
  base_interest_rate: 2.5,
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const body = await response.text()
    throw new Error(body || `HTTP ${response.status}`)
  }
  if (response.status === 204) return null
  return response.json()
}

const App = {
  components: { Landmark, ReceiptText },
  data() {
    return {
      API_BASE,
      sections,
      activeSection: 'dashboard',
      activeTable: 'products',
      rows: [],
      tableNames: [],
      form: {},
      txForm: {
        account_id: '',
        counterparty_account_id: '',
        amount: 10000,
        channel_type: 'INTERNET',
        depositor_customer_id: '',
        depositor_name: '',
        delegate_customer_id: '',
        delegate_customer_name: '',
        transaction_memo: '',
      },
      contractForm: {
        customer_id: '',
        product_id: '',
        contract_period_month: 12,
        maturity_at: '',
        join_channel: 'WEB',
        initial_balance: 0,
      },
      loading: false,
      error: '',
      notice: '',
    }
  },
  computed: {
    currentTables() {
      return tableGroups[this.activeSection] || []
    },
    currentFields() {
      return formFields[this.activeTable] || []
    },
    stats() {
      return [
        { label: 'ERD 테이블', value: this.tableNames.length || 18 },
        { label: '현재 화면', value: this.activeSection },
        { label: 'API', value: this.API_BASE },
      ]
    },
  },
  async mounted() {
    await this.loadMeta()
    await this.switchSection('dashboard')
  },
  methods: {
    async loadMeta() {
      try {
        const data = await request('/api/meta/tables')
        this.tableNames = data.tables
      } catch (err) {
        this.error = `API 연결 실패: ${err.message}`
      }
    },
    resetForm() {
      const next = {}
      for (const field of this.currentFields) next[field] = defaults[field] ?? ''
      this.form = next
    },
    async switchSection(section) {
      this.activeSection = section
      this.notice = ''
      this.error = ''
      if (section === 'dashboard') {
        this.rows = []
        return
      }
      this.activeTable = this.currentTables[0]
      this.resetForm()
      await this.loadRows()
    },
    async switchTable(table) {
      this.activeTable = table
      this.resetForm()
      await this.loadRows()
    },
    async loadRows() {
      this.loading = true
      this.error = ''
      try {
        this.rows = await request(`/api/${this.activeTable}`)
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async createRow() {
      this.loading = true
      this.error = ''
      try {
        const payload = normalize(this.form)
        await request(`/api/${this.activeTable}`, { method: 'POST', body: JSON.stringify(payload) })
        this.notice = `${this.activeTable} 등록 완료`
        this.resetForm()
        await this.loadRows()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async createContract() {
      try {
        await request('/contracts', { method: 'POST', body: JSON.stringify(normalize(this.contractForm)) })
        this.notice = '계약과 계좌가 생성되었습니다'
        await this.switchTable('contracts')
      } catch (err) {
        this.error = err.message
      }
    },
    async runTransaction(type) {
      const path = {
        deposit: '/transactions/deposit',
        withdraw: '/transactions/withdraw',
        transfer: '/transactions/transfer',
        payment: '/transactions/payment',
        savings: '/transactions/savings-payment',
      }[type]
      try {
        await request(path, { method: 'POST', body: JSON.stringify(normalize(this.txForm)) })
        this.notice = '거래 처리 완료'
        this.activeTable = 'transactions'
        await this.loadRows()
      } catch (err) {
        this.error = err.message
      }
    },
    rowPreview(row) {
      return Object.entries(row).slice(0, 7)
    },
  },
  template: `
    <div class="shell">
      <aside class="sidebar">
        <div class="brand"><Landmark :size="22" /> TeamProject</div>
        <button v-for="section in sections" :key="section.key" class="nav" :class="{ active: activeSection === section.key }" @click="switchSection(section.key)">
          <component :is="section.icon" :size="18" />
          <span>{{ section.label }}</span>
        </button>
      </aside>

      <main class="main">
        <header class="topbar">
          <div>
            <h1>{{ sections.find(s => s.key === activeSection)?.label }}</h1>
            <p>ERD 18개 테이블 기반 PostgreSQL + FastAPI + Vue 관리 화면</p>
          </div>
          <div class="api-pill">{{ API_BASE }}</div>
        </header>

        <section v-if="activeSection === 'dashboard'" class="dashboard">
          <div v-for="item in stats" :key="item.label" class="metric">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
          <div class="wide-panel">
            <h2>구현 범위</h2>
            <p>상품, 계약, 계좌, 거래, 이자, 특약, 부서/대상 그룹을 관리합니다. 거래에는 입금자와 위임받은 사람 정보를 함께 저장합니다.</p>
          </div>
        </section>

        <section v-else class="workbench">
          <div class="tabs">
            <button v-for="table in currentTables" :key="table" :class="{ active: activeTable === table }" @click="switchTable(table)">{{ table }}</button>
          </div>

          <div v-if="activeSection === 'transactions'" class="action-panel">
            <h2>거래 처리</h2>
            <div class="form-grid">
              <label v-for="field in ['account_id','counterparty_account_id','amount','channel_type','depositor_customer_id','depositor_name','delegate_customer_id','delegate_customer_name','transaction_memo']" :key="field">
                <span>{{ field }}</span>
                <input v-model="txForm[field]" />
              </label>
            </div>
            <div class="button-row">
              <button @click="runTransaction('deposit')">입금</button>
              <button @click="runTransaction('withdraw')">출금</button>
              <button @click="runTransaction('transfer')">이체</button>
              <button @click="runTransaction('payment')">결제</button>
              <button @click="runTransaction('savings')">적금 납입</button>
            </div>
          </div>

          <div v-if="activeSection === 'contracts'" class="action-panel">
            <h2>계약 생성 + 계좌 자동 생성</h2>
            <div class="form-grid">
              <label v-for="field in Object.keys(contractForm)" :key="field">
                <span>{{ field }}</span>
                <input v-model="contractForm[field]" />
              </label>
            </div>
            <button @click="createContract">계약 생성</button>
          </div>

          <div class="panel">
            <div class="panel-head">
              <h2>{{ activeTable }} 등록</h2>
              <button @click="loadRows">새로고침</button>
            </div>
            <div class="form-grid">
              <label v-for="field in currentFields" :key="field">
                <span>{{ field }}</span>
                <input v-model="form[field]" />
              </label>
            </div>
            <button @click="createRow">등록</button>
          </div>

          <p v-if="notice" class="notice">{{ notice }}</p>
          <p v-if="error" class="error">{{ error }}</p>

          <div class="panel">
            <div class="panel-head">
              <h2>{{ activeTable }} 목록</h2>
              <span>{{ rows.length }}건</span>
            </div>
            <div class="table-list">
              <article v-for="row in rows" :key="JSON.stringify(row)" class="row-card">
                <div v-for="[key, value] in rowPreview(row)" :key="key">
                  <span>{{ key }}</span>
                  <strong>{{ value }}</strong>
                </div>
              </article>
            </div>
          </div>
        </section>
      </main>
    </div>
  `,
}

function normalize(source) {
  const out = {}
  for (const [key, value] of Object.entries(source)) {
    if (value === '') continue
    if (value === 'true') out[key] = true
    else if (value === 'false') out[key] = false
    else if (!Number.isNaN(Number(value)) && value !== null && value !== '') out[key] = Number(value)
    else out[key] = value
  }
  return out
}

createApp(App).mount('#app')
