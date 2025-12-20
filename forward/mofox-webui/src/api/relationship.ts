/**
 * 人物关系管理 API
 */

import { api } from './index'

/**
 * 用户基础信息
 */
export interface PersonBasicInfo {
  person_id: string
  person_name: string
  nickname?: string
  know_times: number
  know_since?: string
  last_know?: string
  attitude?: string
}

/**
 * 用户卡片信息（列表展示）
 */
export interface PersonCard {
  person_id: string
  person_name: string
  nickname?: string
  relationship_score: number
  relationship_text?: string
  short_impression?: string
  know_times: number
  last_know?: string
}

/**
 * 用户列表响应
 */
export interface PersonListResponse {
  persons: PersonCard[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 用户关系信息
 */
export interface PersonRelationship {
  person_id: string
  person_name: string
  relationship_score: number
  relationship_text?: string
}

/**
 * 记忆点
 */
export interface MemoryPoint {
  content: string
  weight: number
  timestamp: string
}

/**
 * 用户详情
 */
export interface PersonDetail {
  basic_info: PersonBasicInfo
  relationship: PersonRelationship
  impression: string
  short_impression: string
  memory_points: MemoryPoint[]
}

/**
 * 关系报告
 */
export interface RelationshipReport {
  person_id: string
  report: string
}

/**
 * 更新关系请求
 */
export interface UpdateRelationshipRequest {
  relationship_score: number
  relationship_text?: string
}

/**
 * 平台信息
 */
export interface PlatformInfo {
  platform: string
  count: number
}

/**
 * 平台列表响应
 */
export interface PlatformsResponse {
  platforms: PlatformInfo[]
}

/**
 * 获取平台列表
 */
export async function getPlatforms() {
  return await api.get<PlatformsResponse>('relationship/platforms')
}

/**
 * 获取用户列表
 */
export async function getPersonList(page: number = 1, pageSize: number = 20, platform?: string) {
  let url = `relationship/list?page=${page}&page_size=${pageSize}`
  if (platform) {
    url += `&platform=${encodeURIComponent(platform)}`
  }
  return await api.get<PersonListResponse>(url)
}

/**
 * 获取用户详情
 */
export async function getPersonDetail(personId: string) {
  return await api.get<PersonDetail>(`relationship/person/${personId}`)
}

/**
 * 更新用户关系
 */
export async function updatePersonRelationship(
  personId: string,
  data: UpdateRelationshipRequest
) {
  return await api.put<{ success: boolean; message: string }>(
    `relationship/person/${personId}`,
    data
  )
}

/**
 * 获取关系报告
 */
export async function getRelationshipReport(personId: string) {
  return await api.get<RelationshipReport>(`relationship/person/${personId}/report`)
}

/**
 * 获取关系统计
 */
export async function getRelationshipStats() {
  return await api.get<Record<string, unknown>>('relationship/stats')
}

/**
 * 清理关系缓存
 */
export async function clearRelationshipCache(personId?: string) {
  return await api.post<{ success: boolean; message: string }>(
    'relationship/cache/clear',
    { person_id: personId }
  )
}

/**
 * 搜索用户
 */
export async function searchPerson(query: string) {
  return await api.get<PersonBasicInfo>(`relationship/search?query=${encodeURIComponent(query)}`)
}

/**
 * 更新用户印象
 */
export async function updatePersonImpression(
  personId: string,
  impression?: string,
  shortImpression?: string
) {
  return await api.put<{ success: boolean; message: string }>(
    `relationship/person/${personId}/impression`,
    {
      impression: impression || null,
      short_impression: shortImpression || null
    }
  )
}

/**
 * 更新用户记忆点
 */
export async function updatePersonPoints(
  personId: string,
  points: Array<{ content: string; weight: number; timestamp: string }>
) {
  return await api.put<{ success: boolean; message: string }>(
    `relationship/person/${personId}/points`,
    points
  )
}
