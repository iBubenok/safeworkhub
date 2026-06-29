/** Общие типы приложения под новый backend-контракт. */

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  primary_organization_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Membership {
  organization_id: number;
  role: string;
  is_active: boolean;
  joined_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
  organization_id: number;
  role: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
  organization_id?: number;
}

export interface RegisterRequest {
  organization_name: string;
  inn: string;
  admin_email: string;
  admin_password: string;
  admin_name: string;
}

export interface RegisterResponse {
  organization_id: number;
  user_id: string;
  subscription_status: string;
  trial_ends_at: string | null;
}

export type MaterialType = 'article' | 'npa' | 'template' | 'reference' | 'news';
export type MaterialStatus = 'draft' | 'published' | 'archived';
export type MaterialContentFormat = 'markdown' | 'html';

export interface NewsDetail {
  source_url: string | null;
  event_date: string | null;
  cover_image_url: string | null;
  tags: string[];
}

export interface AttachmentResponse {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export type NpaActKind =
  | 'federal_law'
  | 'constitutional_law'
  | 'code'
  | 'presidential_decree'
  | 'government_decree'
  | 'ministry_order'
  | 'gost'
  | 'sanpin'
  | 'sp'
  | 'regional_law'
  | 'municipal_act'
  | 'local_act'
  | 'other';
export type NpaLevel = 'federal' | 'regional' | 'municipal' | 'local';
export type NpaStatus = 'in_force' | 'not_in_force' | 'repealed' | 'amended' | 'suspended';

export interface MaterialRef {
  id: string;
  title: string;
}

export interface NpaDetail {
  act_kind: NpaActKind;
  level: NpaLevel | null;
  act_status: NpaStatus | null;
  document_number: string | null;
  adoption_date: string | null;
  effective_date: string | null;
  revision_date: string | null;
  issuing_authority: string | null;
  region: string | null;
  official_source_url: string | null;
  replaced_by_id: string | null;
  replaced_by: MaterialRef | null;
  replaces: MaterialRef[];
}

export interface NpaUpdateInput {
  act_kind?: NpaActKind;
  level?: NpaLevel | null;
  act_status?: NpaStatus | null;
  document_number?: string | null;
  adoption_date?: string | null;
  effective_date?: string | null;
  revision_date?: string | null;
  issuing_authority?: string | null;
  region?: string | null;
  official_source_url?: string | null;
  replaced_by_id?: string | null;
}

export interface NpaCreateInput {
  title: string;
  summary: string | null;
  content?: string;
  content_format?: MaterialContentFormat;
  category_id?: number | null;
  status?: MaterialStatus;
  act_kind: NpaActKind;
  level?: NpaLevel | null;
  act_status?: NpaStatus | null;
  document_number?: string | null;
  adoption_date?: string | null;
  effective_date?: string | null;
  revision_date?: string | null;
  issuing_authority?: string | null;
  region?: string | null;
  official_source_url?: string | null;
}

export interface Material {
  id: string;
  organization_id: number;
  title: string;
  summary: string | null;
  content: string;
  content_format: MaterialContentFormat;
  type: MaterialType;
  status: MaterialStatus;
  author_id: string;
  author_name?: string | null;
  organization_name?: string | null;
  views_count: number;
  published_at: string | null;
  updated_by_id?: string | null;
  updated_by_name?: string | null;
  created_at: string;
  updated_at: string;
  news?: NewsDetail | null;
  npa?: NpaDetail | null;
  attachments?: AttachmentResponse[];
}

export interface TemplateCreateInput {
  title: string;
  summary: string | null;
  content?: string;
  content_format?: MaterialContentFormat;
  category_id?: number | null;
  status?: MaterialStatus;
}

export interface ArticleCreateInput {
  title: string;
  summary: string | null;
  content: string;
  content_format?: MaterialContentFormat;
  category_id?: number | null;
  status?: MaterialStatus;
}

export interface NewsCreateInput {
  title: string;
  summary: string | null;
  content: string;
  content_format?: MaterialContentFormat;
  category_id?: number | null;
  status?: MaterialStatus;
  source_url?: string | null;
  event_date?: string | null;
  cover_image_url?: string | null;
  tags?: string[];
}

export interface Category {
  id: number;
  organization_id: number;
  name: string;
  slug: string;
  parent_id: number | null;
  description: string | null;
  sort_order: number;
}

export interface MaterialListItem {
  id: string;
  organization_id: number;
  organization_name: string | null;
  title: string;
  summary: string | null;
  type: MaterialType;
  status: MaterialStatus;
  views_count: number;
  published_at: string | null;
  attachment_count: number;
}

export interface MaterialVersion {
  id: string;
  version_no: number;
  editor_id: string | null;
  editor_name: string | null;
  change_note: string | null;
  created_at: string;
  snapshot: {
    title?: string;
    summary?: string | null;
    content?: string;
    content_format?: MaterialContentFormat;
  };
}

export type ChecklistStatus = 'draft' | 'published' | 'archived';
export type ChecklistAnswerType = 'compliance' | 'yes_no' | 'text' | 'number';
export type ChecklistNodeType = 'group' | 'item';

export interface ChecklistReference {
  id: string;
  material_id: string | null;
  material_title: string | null;
  note: string | null;
}

export interface ChecklistReferenceInput {
  material_id?: string | null;
  note?: string | null;
}

export interface ChecklistNode {
  id: string;
  node_type: ChecklistNodeType;
  text: string;
  answer_type: ChecklistAnswerType | null;
  required: boolean;
  help_text: string | null;
  references: ChecklistReference[];
  children: ChecklistNode[];
}

export interface ChecklistNodeInput {
  node_type: ChecklistNodeType;
  text: string;
  answer_type?: ChecklistAnswerType | null;
  required?: boolean;
  help_text?: string | null;
  references?: ChecklistReferenceInput[];
  children?: ChecklistNodeInput[];
}

export interface Checklist {
  id: string;
  organization_id: number;
  organization_name: string | null;
  author_id: string;
  author_name: string | null;
  title: string;
  description: string | null;
  status: ChecklistStatus;
  views_count: number;
  created_at: string;
  updated_at: string;
  updated_by_name: string | null;
  items: ChecklistNode[];
}

export interface ChecklistListItem {
  id: string;
  title: string;
  description: string | null;
  status: ChecklistStatus;
  organization_name: string | null;
  item_count: number;
  views_count: number;
  created_at: string;
}

export interface ChecklistCreateInput {
  title: string;
  description?: string | null;
  status?: ChecklistStatus;
  items: ChecklistNodeInput[];
}

export interface ChecklistUpdateInput {
  title?: string;
  description?: string | null;
  status?: ChecklistStatus;
  items?: ChecklistNodeInput[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface MaterialSearchParams extends PaginationParams {
  query?: string;
  type?: MaterialType;
  category_id?: number;
  status?: MaterialStatus;
}

export interface CourseModule {
  id?: number;
  title: string;
  content: string;
  sort_order: number;
  duration_minutes: number;
  created_at?: string;
  updated_at?: string;
}

export interface Course {
  id: number;
  organization_id: number;
  title: string;
  description: string | null;
  duration_minutes: number;
  is_published: boolean;
  thumbnail_url: string | null;
  created_at: string;
  updated_at: string;
  modules: CourseModule[];
}

export interface CourseAssignment {
  id: string;
  course_id: number;
  organization_id: number;
  user_id: string;
  status: 'assigned' | 'in_progress' | 'completed' | 'overdue';
  progress_percent: number;
  due_at: string | null;
  completed_at: string | null;
  last_activity_at: string | null;
  created_at: string;
  updated_at: string;
}
