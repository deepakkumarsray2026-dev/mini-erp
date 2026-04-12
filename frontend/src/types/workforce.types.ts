export interface Department {
  id: string
  name: string
  code: string
  description: string | null
  parent_id: string | null
  is_active: boolean
  created_at: string
}

export interface Job {
  id: string
  title: string
  code: string
  job_family_id: string
  grade_min: number | null
  grade_max: number | null
  is_active: boolean
}

export interface Employee {
  id: string
  employee_number: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  hire_date: string
  employment_status: 'active' | 'inactive' | 'terminated' | 'on_leave'
  department_id: string
  department_name: string | null
  job_id: string
  job_title: string | null
  manager_id: string | null
  manager_name: string | null
  created_at: string
}
