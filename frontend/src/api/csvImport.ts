import { ApiClient } from './request'

// CSV导入请求参数
interface CSVImportParams {
  table: string
  mode: 'insert' | 'update' | 'upsert'
  data: any[]
  columns: string[]
}

// CSV导入响应
interface CSVImportResponse {
  success: boolean
  imported: number
  failed: number
  message: string
}

/**
 * 数据筛选请求参数
 */
interface DataFilterParams {
  table: string
  filters: Record<string, any>
  page: number
  page_size: number
  sort: string
  order: string
}

/**
 * 数据筛选响应
 */
interface DataFilterResponse<T = any> {
  success: boolean
  data: T[]
  total: number
  page: number
  page_size: number
  message: string
}

/**
 * CSV导入API模块
 */
export const csvImportApi = {
  /**
   * 导入数据到指定表
   * @param params 导入参数
   * @returns 导入结果
   */
  importData: async (params: CSVImportParams) => {
    return await ApiClient.post<CSVImportResponse>('/api/csv/import', params)
  },
  
  /**
   * 获取支持的表列表
   * @returns 表列表
   */
  getTables: async () => {
    return await ApiClient.get<string[]>('/api/csv/tables')
  },
  
  /**
   * 验证CSV数据格式
   * @param data 解析后的数据
   * @param columns 列名
   * @returns 验证结果
   */
  validateData: async (data: any[], columns: string[]) => {
    return await ApiClient.post('/api/csv/validate', { data, columns })
  },
  
  /**
   * 筛选导入的数据
   * @param params 筛选参数
   * @returns 筛选结果
   */
  filterData: async (params: DataFilterParams) => {
    return await ApiClient.post<DataFilterResponse>('/api/csv/filter', params)
  }
}
