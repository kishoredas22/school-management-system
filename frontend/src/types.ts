export type UserRole = "SUPER_ADMIN" | "ADMIN" | "TEACHER" | "DATA_ENTRY";
export type LoginMode = "PASSWORD" | "EMAIL_LINK";
export type PermissionCode =
  | "DASHBOARD_VIEW"
  | "USER_MANAGE"
  | "TEACHER_VIEW"
  | "TEACHER_MANAGE"
  | "TEACHER_SCOPE_MANAGE"
  | "STUDENT_VIEW"
  | "STUDENT_MANAGE"
  | "STUDENT_RECORDS"
  | "STUDENT_STATUS"
  | "ATTENDANCE_STUDENT"
  | "ATTENDANCE_TEACHER"
  | "FEE_VIEW"
  | "FEE_MANAGE"
  | "REPORT_VIEW"
  | "AUDIT_VIEW"
  | "REFERENCE_MANAGE"
  | "ACADEMIC_YEAR_MANAGE";
export type StudentStatus = "ACTIVE" | "PASSED_OUT" | "TOOK_TC" | "INACTIVE";
export type PromotionAction = "PROMOTE" | "HOLD" | "PASS_OUT";
export type AttendanceStatus = "PRESENT" | "ABSENT" | "LEAVE";
export type PaymentMode = "CASH" | "BANK" | "UPI";
export type FeeType = "ONE_TIME" | "RECURRING";
export type AuditReviewStatus = "NOT_REQUIRED" | "PENDING" | "APPROVED" | "REJECTED";

export interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
  details?: Record<string, unknown>;
}

export interface Paginated<T> {
  page: number;
  size: number;
  total_records: number;
  total_pages: number;
  data: T[];
}

export interface Session {
  accessToken: string;
  tokenType: string;
  role: UserRole;
  username: string;
  loginMode: LoginMode;
  permissions: PermissionCode[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: UserRole;
  login_mode: LoginMode;
  permissions: PermissionCode[];
}

export interface AcademicYear {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  is_closed: boolean;
}

export interface ClassRoom {
  id: string;
  name: string;
}

export interface Section {
  id: string;
  name: string;
  class_id: string;
}

export type ExamStatus = "DRAFT" | "PUBLISHED";

export interface TeacherAssignment {
  id?: string;
  class_id?: string | null;
  class_name?: string | null;
  section_id?: string | null;
  section_name?: string | null;
  academic_year_id?: string | null;
}

export interface Subject {
  id: string;
  name: string;
  code: string;
  is_active: boolean;
}

export interface TeacherSubjectAssignment {
  id: string;
  teacher_id: string;
  teacher_name: string;
  subject_id: string;
  subject_name: string;
  academic_year_id: string;
  academic_year_name: string;
  class_id: string;
  class_name: string;
  section_id: string | null;
  section_name: string | null;
}

export interface TimetableEntry {
  id: string;
  academic_year_id: string;
  academic_year_name: string;
  class_id: string;
  class_name: string;
  section_id: string | null;
  section_name: string | null;
  subject_id: string;
  subject_name: string;
  teacher_id: string;
  teacher_name: string;
  weekday: string;
  period_label: string;
  start_time: string;
  end_time: string;
  room_label: string | null;
}

export interface GradeRule {
  id: string;
  academic_year_id: string;
  academic_year_name: string;
  grade_label: string;
  min_percentage: string;
  max_percentage: string;
  remark: string | null;
  sort_order: number;
}

export interface ExamSubject {
  id: string;
  subject_id: string;
  subject_name: string;
  max_marks: string;
  pass_marks: string;
}

export interface Exam {
  id: string;
  academic_year_id: string;
  academic_year_name: string;
  class_id: string;
  class_name: string;
  section_id: string | null;
  section_name: string | null;
  name: string;
  term_label: string | null;
  start_date: string;
  end_date: string;
  status: ExamStatus;
  subject_count: number;
  subjects: ExamSubject[];
}

export interface MarkRegisterRow {
  student_id: string;
  student_name: string;
  student_code: string | null;
  marks_obtained: string | null;
  is_absent: boolean;
  remark: string | null;
}

export interface ExamResultSummary {
  student_id: string;
  student_name: string;
  student_code: string | null;
  percentage: string;
  overall_grade: string | null;
  result: string;
}

export interface ReportCardSubjectRow {
  subject_name: string;
  max_marks: string;
  pass_marks: string;
  marks_obtained: string | null;
  is_absent: boolean;
  result: string;
}

export interface ReportCard {
  exam_id: string;
  exam_name: string;
  term_label: string | null;
  academic_year_name: string;
  class_name: string;
  section_name: string | null;
  student_id: string;
  student_name: string;
  student_code: string | null;
  generated_at: string;
  total_marks: string;
  obtained_marks: string;
  percentage: string;
  overall_grade: string | null;
  overall_remark: string | null;
  result: string;
  subject_rows: ReportCardSubjectRow[];
}

export interface StudentRecord {
  id: string;
  student_id: string | null;
  first_name: string;
  last_name: string | null;
  dob: string;
  guardian_name: string | null;
  guardian_phone: string | null;
  status: StudentStatus;
  class_id: string | null;
  class_name: string | null;
  section_id: string | null;
  section_name: string | null;
  academic_year_id: string | null;
  academic_year_name: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Teacher {
  id: string;
  name: string;
  phone: string | null;
  is_active: boolean;
  assignment_count?: number;
  assignments?: TeacherAssignment[];
}

export interface TeacherContract {
  id: string;
  teacher_id: string;
  teacher_name: string;
  academic_year_id: string;
  academic_year_name: string;
  yearly_contract_amount: string;
  monthly_salary: string | null;
  created_at: string;
}

export interface FeeStructure {
  id: string;
  class_id: string;
  academic_year_id: string;
  fee_name: string;
  amount: string;
  fee_type: FeeType;
  is_active: boolean;
}

export interface FeePaymentHistory {
  id: string;
  student_id: string;
  fee_structure_id: string;
  amount_paid: string;
  payment_mode: PaymentMode;
  payment_date: string;
  receipt_number: string;
  created_at: string;
}

export interface FeeSummary {
  total_fee: string;
  total_paid: string;
  pending: string;
  payment_history: FeePaymentHistory[];
}

export interface AttendanceSummary {
  entity_id: string;
  entity_name: string;
  present_count: number;
  absent_count: number;
  leave_count: number;
  attendance_percentage: number;
}

export interface AttendanceDetail {
  attendance_date: string;
  status: AttendanceStatus;
}

export interface StudentAttendanceRegisterItem {
  student_id: string;
  student_code: string | null;
  student_name: string;
  status: AttendanceStatus | null;
}

export interface TeacherAttendanceRecord {
  id: string;
  teacher_id: string;
  teacher_name: string;
  attendance_date: string;
  status: AttendanceStatus;
  note: string | null;
}

export interface FeeReport {
  total_collected: string;
  total_pending: string;
}

export interface PendingFeeItem {
  student_id: string;
  student_name: string;
  class_name: string;
  total_fee: string;
  total_paid: string;
  pending: string;
}

export interface TeacherPaymentSummary {
  teacher_id: string;
  teacher_name: string;
  contract_total: string;
  total_paid: string;
  pending_balance: string;
}

export interface DashboardOverview {
  student_total: number;
  active_students: number;
  teacher_total: number;
  active_teachers: number;
  class_count: number;
  section_count: number;
  fee_collected: string;
  fee_pending: string;
  pending_students: number;
  salary_pending: string;
  student_status: StudentStatusBreakdown[];
}

export interface MonthlyFinanceTrendPoint {
  month: number;
  label: string;
  fee_collected: string;
  teacher_paid: string;
  net_cashflow: string;
}

export interface StudentStatusBreakdown {
  status: StudentStatus;
  count: number;
}

export interface ClassFeeBalance {
  class_name: string;
  student_count: number;
  pending_total: string;
  collected_total: string;
}

export interface AuditLog {
  id: string;
  entity_name: string;
  entity_id: string | null;
  action: string;
  performed_by: string | null;
  performed_by_username: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  performed_at: string;
  requires_review: boolean;
  review_status: AuditReviewStatus;
  review_note: string | null;
  reviewed_by: string | null;
  reviewed_by_username: string | null;
  reviewed_at: string | null;
}

export interface AuditSummary {
  total_logs: number;
  review_required: number;
  pending_reviews: number;
  approved_reviews: number;
  rejected_reviews: number;
}

export interface UserRecord {
  id: string;
  username: string;
  email: string | null;
  login_mode: LoginMode;
  is_active: boolean;
  role: UserRole;
  teacher_id: string | null;
  teacher_name: string | null;
  teacher_phone: string | null;
  teacher_assignment_count: number;
  teacher_assignments: TeacherAssignment[];
  permissions: PermissionCode[];
}

export interface AccessOption {
  code: PermissionCode;
  label: string;
  description: string;
  group?: string;
}

export interface UserAccessOptions {
  permissions: AccessOption[];
  default_permissions_by_role: Record<UserRole, PermissionCode[]>;
  login_modes: LoginMode[];
}

export interface EmailLinkPreview {
  delivery: string;
  email?: string | null;
  expires_at?: string;
  login_url?: string;
  purpose?: string;
}

export interface UserCreateResponse {
  user: UserRecord;
  email_link: EmailLinkPreview | null;
}
