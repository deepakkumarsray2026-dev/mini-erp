import api from './api'

export const aiService = {
  // Model registry
  getModels: (params?: { model_type?: string; active_only?: boolean; page?: number }) =>
    api.get('/mlops/models', { params }).then((r) => r.data),

  getModel: (id: string) =>
    api.get(`/mlops/models/${id}`).then((r) => r.data),

  // Training
  trainModel: (modelType: string) =>
    api.post(`/mlops/train/${modelType}`, { triggered_by: 'ui' }).then((r) => r.data),

  // Predictions
  predictAttrition: (employeeId: string) =>
    api.post(`/mlops/predict/attrition/${employeeId}`).then((r) => r.data),

  predictExpenseViolation: (lineId: string) =>
    api.post(`/mlops/predict/expense-violation/${lineId}`).then((r) => r.data),

  predictPayrollAnomaly: (payslipId: string) =>
    api.post(`/mlops/predict/payroll-anomaly/${payslipId}`).then((r) => r.data),

  predictInvoice: (invoiceId: string) =>
    api.post(`/mlops/predict/invoice/${invoiceId}`).then((r) => r.data),

  // Audit log & jobs
  getPredictions: (params?: { page?: number; entity_type?: string; model_type?: string }) =>
    api.get('/mlops/predictions', { params }).then((r) => r.data),

  getJobs: (params?: { page?: number; model_type?: string }) =>
    api.get('/mlops/jobs', { params }).then((r) => r.data),
}

// Entity lists for picking IDs
export const entityService = {
  getEmployees: () =>
    api.get('/workforce/employees', { params: { page: 1, page_size: 100 } }).then((r) => r.data.items ?? []),

  getExpenseLines: () =>
    api.get('/expenses/reports', { params: { page: 1, page_size: 50 } }).then((r) => r.data.items ?? []),

  getPayslips: () =>
    api.get('/payroll/payslips', { params: { page: 1, page_size: 100 } }).then((r) => r.data.items ?? []),

  getInvoices: () =>
    api.get('/ap/invoices', { params: { page: 1, page_size: 100 } }).then((r) => r.data.items ?? []),
}
