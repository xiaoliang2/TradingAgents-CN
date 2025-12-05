<template>
  <div class="imported-data-screening">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Database /></el-icon>
        导入数据筛选
      </h1>
      <p class="page-description">
        筛选和查看通过CSV导入的数据
      </p>
    </div>

    <!-- 表选择和筛选条件面板 -->
    <el-card class="filter-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span>筛选条件</span>
          </div>
          <div class="header-actions">
            <el-button type="text" @click="resetFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </div>
      </template>

      <el-form :model="filters" label-width="120px" class="filter-form">
        <el-row :gutter="24">
          <!-- 表选择 -->
          <el-col :span="8">
            <el-form-item label="目标表">
              <el-select 
                v-model="selectedTable" 
                placeholder="选择要筛选的表" 
                :loading="loadingTables"
                @change="handleTableChange"
                style="width: 100%"
              >
                <el-option 
                  v-for="table in tables" 
                  :key="table" 
                  :label="table" 
                  :value="table" 
                />
              </el-select>
            </el-form-item>
          </el-col>

          <!-- 动态筛选条件 -->
          <template v-if="dynamicFilters.length > 0">
            <el-col 
              v-for="(filter, index) in dynamicFilters" 
              :key="index" 
              :span="8"
            >
              <el-form-item :label="filter.label">
                <!-- 根据字段类型选择不同的筛选控件 -->
                <el-input 
                  v-if="filter.type === 'string'" 
                  v-model="filter.value" 
                  placeholder="输入筛选值" 
                />
                <!-- 数值类型使用范围筛选 -->
                <div v-else-if="filter.type === 'number'" class="range-filter">
                  <el-input 
                    v-model="filter.minValue" 
                    placeholder="最小值" 
                    type="number"
                    style="margin-bottom: 10px;"
                  />
                  <el-input 
                    v-model="filter.maxValue" 
                    placeholder="最大值" 
                    type="number"
                  />
                </div>
                <el-select 
                  v-else-if="filter.type === 'select'" 
                  v-model="filter.value" 
                  placeholder="选择选项" 
                  clearable
                >
                  <el-option 
                    v-for="option in filter.options" 
                    :key="option.value" 
                    :label="option.label" 
                    :value="option.value" 
                  />
                </el-select>
                <el-date-picker
                  v-else-if="filter.type === 'date'"
                  v-model="filter.value"
                  type="date"
                  placeholder="选择日期"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </template>
        </el-row>

        <!-- 筛选按钮 -->
        <div class="filter-actions">
          <el-button type="primary" @click="handleFilter" :loading="loading">
            <el-icon><Search /></el-icon>
            筛选数据
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 数据列表 -->
    <el-card class="data-list" shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <span>数据列表</span>
            <el-tag v-if="total > 0" type="success" size="small" effect="plain">
              共 {{ total }} 条数据
            </el-tag>
          </div>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="handleExport">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
          </div>
        </div>
      </template>

      <!-- 数据表格 -->
      <el-table 
        v-if="tableData.length > 0" 
        :data="tableData" 
        stripe 
        style="width: 100%"
        :loading="loading"
        @sort-change="handleSortChange"
      >
        <!-- 动态列 -->
        <el-table-column
          v-for="column in tableColumns"
          :key="column"
          :prop="column"
          :label="column"
          show-overflow-tooltip
          :sortable="canSort(column)"
        >
          <template #default="scope">
            {{ formatCellValue(column, scope.row[column]) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-else-if="!loading" class="empty-state">
        <el-empty description="暂无数据">
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon>
            点击筛选
          </el-button>
        </el-empty>
      </div>

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Database, Search, Refresh, Download } from '@element-plus/icons-vue'
import { csvImportApi } from '@/api/csvImport'

// 状态管理
const tables = ref<string[]>([])
const selectedTable = ref<string>('')
const loadingTables = ref(false)
const loading = ref(false)
const tableData = ref<any[]>([])
const tableColumns = ref<string[]>([])
const total = ref(0)

// 动态筛选条件
const dynamicFilters = ref<any[]>([])

// 分页
const pagination = ref({
  current: 1,
  pageSize: 20
})

// 排序
const sort = ref({
  prop: '',
  order: ''
})

// 筛选条件
const filters = ref({})

// 导入的表列表（从本地存储获取）
const importedTables = ref<string[]>([])

// 加载导入的表列表
const loadImportedTables = () => {
  try {
    const savedTables = localStorage.getItem('importedTables')
    if (savedTables) {
      importedTables.value = JSON.parse(savedTables)
    }
    console.log('📋 从本地存储加载的导入表列表:', importedTables.value)
  } catch (error) {
    console.error('加载导入表列表失败:', error)
    importedTables.value = []
  }
}

// 加载表列表
const loadTables = async () => {
  try {
    loadingTables.value = true
    console.log('开始调用 getTables API...')
    
    // 加载导入的表列表（保存在本地存储中的表名）
    loadImportedTables()
    
    const response = await csvImportApi.getTables()
    console.log('getTables API 响应:', response)
    if (response && response.success) {
      // 获取所有可用表
      const allTables = response.data || []
      console.log('📋 从API获取的所有表:', allTables)
      
      // 只显示通过CSV导入界面创建的表（保存在本地存储中的表名）
      tables.value = allTables.filter(table => 
        importedTables.value.includes(table)
      )
      console.log('📋 过滤后的表列表:', tables.value)
      
      if (tables.value.length > 0 && !selectedTable.value) {
        selectedTable.value = tables.value[0]
        console.log('默认选择的表:', selectedTable.value)
        handleTableChange(selectedTable.value)
      }
    } else {
      console.error('getTables API 返回失败:', response)
      ElMessage.error(response?.message || '加载表列表失败')
    }
  } catch (error: any) {
    console.error('加载表列表异常:', error)
    console.error('异常详情:', error.message, error.stack)
    ElMessage.error('加载表列表失败: ' + (error.message || '未知错误'))
  } finally {
    loadingTables.value = false
  }
}

// 表选择变化处理
const handleTableChange = async (table: string) => {
  if (!table) return

  try {
    loading.value = true
    console.log('开始分析表结构:', table)
    // 这里可以根据表结构动态生成筛选条件
    // 先获取表的一些样本数据来分析结构
    await analyzeTableStructure(table)
    // 重置筛选条件
    resetFilters()
    // 执行筛选
    handleFilter()
  } catch (error: any) {
    console.error('分析表结构失败:', error)
    console.error('异常详情:', error.message, error.stack)
    ElMessage.error('分析表结构失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 分析表结构
const analyzeTableStructure = async (table: string) => {
  try {
    // 清空之前的筛选条件
    dynamicFilters.value = []
    // 清空之前的列
    tableColumns.value = []
    
    console.log('开始调用 filterData API 获取样本数据...')
    console.log('API 参数:', {
      table,
      filters: {},
      page: 1,
      page_size: 10,
      sort: '',
      order: ''
    })
    
    // 先获取一些样本数据来分析表结构
    const response = await csvImportApi.filterData({
      table,
      filters: {},
      page: 1,
      page_size: 10,
      sort: '',
      order: ''
    })
    
    console.log('filterData API 响应:', response)
    
    if (response && response.success) {
      if (response.data && response.data.length > 0) {
        // 收集所有可能的字段（检查前10条记录）
        const allPossibleColumns = new Set<string>()
        const firstRow = response.data[0]
        const sampleRows = response.data.slice(0, Math.min(10, response.data.length))
        
        // 收集所有出现过的字段
        sampleRows.forEach(row => {
          Object.keys(row).forEach(key => {
            if (key !== '_id') {
              allPossibleColumns.add(key)
            }
          })
        })
        
        // 获取所有列名，排除_id字段
        const allColumns = Object.keys(firstRow)
        const columnsToDisplay = allColumns.filter(col => col !== '_id')
        
        // 确保导入日期字段被添加到显示列中
        if (!columnsToDisplay.includes('导入日期')) {
          columnsToDisplay.push('导入日期')
        }
        
        tableColumns.value = columnsToDisplay
        
        // 清空之前的筛选条件
        dynamicFilters.value = []
        
        // 为每一列生成筛选条件
        columnsToDisplay.forEach(col => {
          // 检查该字段是否存在于数据中
          const fieldExists = allPossibleColumns.has(col)
          let sampleValue: any = ''
          let fieldType = 'string'
          
          // 首先根据字段名推断类型
          // 检查字段名是否包含数值相关关键词
          const numericKeywords = ['%', '元', '亿', '万', '金额', '值', '数', '率', '量', '价']
          const hasNumericKeyword = numericKeywords.some(keyword => col.includes(keyword))
          
          // 如果字段名包含数值相关关键词，直接识别为数值类型
          if (hasNumericKeyword) {
            fieldType = 'number'
          }
          // 如果字段名不包含数值关键词，再根据字段值推断类型
          else if (fieldExists) {
            // 找第一个包含该字段的记录
            const sampleRow = sampleRows.find(row => row.hasOwnProperty(col))
            if (sampleRow) {
              sampleValue = sampleRow[col]
              
              // 推断字段类型
              if (typeof sampleValue === 'number') {
                fieldType = 'number'
              } else if (typeof sampleValue === 'string') {
                // 检查是否是日期格式
                if (/^\d{4}-\d{2}-\d{2}/.test(sampleValue) || sampleValue.includes('T') || sampleValue.includes(':')) {
                  fieldType = 'date'
                } else {
                  // 检查是否是数值字符串（包括带有单位的数值、百分比）
                  // 移除单位、千分位逗号、百分比符号，然后尝试转换为数字
                  // 处理百分比形式（如 "10.50%"）
                  // 处理金额形式（如 "2.33亿"、"12,345.67万"）
                  const numericStr = sampleValue.replace(/[\s,，亿万千佰拾%]+/g, '')
                  if (!isNaN(Number(numericStr)) && numericStr.trim() !== '') {
                    fieldType = 'number'
                  }
                }
              }
            }
          }
          
          // 特别处理导入日期字段，强制为日期类型
          if (col === '导入日期') {
            fieldType = 'date'
          }
          
          // 生成筛选条件
          dynamicFilters.value.push({
            field: col,
            label: col,
            type: fieldType,
            value: '',
            minValue: null,
            maxValue: null
          })
        })
        
        console.log(`✅ 分析表结构完成，表: ${table}，列: ${tableColumns.value.length} 个，排除了 _id 字段`)
      } else {
        // 表为空，没有数据
        console.log(`⚠️ 表 ${table} 为空，没有数据可分析`)
        // 默认显示导入日期筛选选项
        tableColumns.value = ['导入日期']
        dynamicFilters.value = [
          {
            field: '导入日期',
            label: '导入日期',
            type: 'date',
            value: '',
            minValue: null,
            maxValue: null
          }
        ]
      }
    } else {
      console.error('filterData API 返回失败:', response)
      ElMessage.error(response?.message || '获取表数据失败')
    }
  } catch (error: any) {
    console.error('分析表结构异常:', error)
    console.error('异常详情:', error.message, error.stack)
    ElMessage.error('分析表结构失败: ' + (error.message || '未知错误'))
  }
}

// 重置筛选条件
const resetFilters = () => {
  dynamicFilters.value.forEach(filter => {
    filter.value = ''
    
    // 重置数值类型的范围筛选条件
    if (filter.type === 'number') {
      filter.minValue = null
      filter.maxValue = null
    }
  })
  pagination.value.current = 1
}

// 筛选数据
const handleFilter = async () => {
  if (!selectedTable.value) {
    ElMessage.warning('请先选择表')
    return
  }

  try {
    loading.value = true
    
    // 构建筛选条件
    const filterParams = {
      table: selectedTable.value,
      filters: {},
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      sort: sort.value.prop,
      order: sort.value.order
    }
    
    // 收集动态筛选条件
    dynamicFilters.value.forEach(filter => {
      if (filter.type === 'number') {
        // 数值类型处理范围筛选
        const field = filter.field
        const hasMin = filter.minValue !== null && filter.minValue !== '' && filter.minValue !== undefined
        const hasMax = filter.maxValue !== null && filter.maxValue !== '' && filter.maxValue !== undefined
        
        if (hasMin || hasMax) {
          filterParams.filters[field] = {}
          
          if (hasMin) {
            filterParams.filters[field]['$gte'] = Number(filter.minValue)
          }
          
          if (hasMax) {
            filterParams.filters[field]['$lte'] = Number(filter.maxValue)
          }
        }
      } else {
        // 非数值类型处理普通筛选
        if (filter.value !== '' && filter.value !== undefined && filter.value !== null) {
          filterParams.filters[filter.field] = filter.value
        }
      }
    })
    
    // 调用API获取数据
    const response = await csvImportApi.filterData(filterParams)
    
    if (response.success) {
      tableData.value = response.data || []
      total.value = response.total || 0
      console.log(`✅ 数据筛选完成，表: ${selectedTable.value}，共 ${response.total} 条数据`) 
    } else {
      ElMessage.error(response.message || '数据筛选失败')
    }
  } catch (error) {
    console.error('筛选数据失败:', error)
    ElMessage.error('数据筛选失败')
  } finally {
    loading.value = false
  }
}

// 判断列是否可排序
const canSort = (column: string) => {
  // 这里可以根据字段类型判断是否可排序
  return true
}

// 格式化单元格值
const formatCellValue = (column: string, value: any) => {
  if (value === null || value === undefined) {
    return '-'
  }
  
  // 日期格式处理
  if (typeof value === 'string') {
    // 检查是否是导入日期字段
    if (column === '导入日期' || column.toLowerCase().includes('date') || column.toLowerCase().includes('time')) {
      try {
        const date = new Date(value)
        if (!isNaN(date.getTime())) {
          return date.toLocaleDateString() // 只显示日期，不显示时间
        }
      } catch {
        // 不是有效日期，返回原始值
      }
    }
  }
  
  // 数值格式处理
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  
  return value
}

// 排序变化
const handleSortChange = (sortInfo: any) => {
  sort.value = {
    prop: sortInfo.prop,
    order: sortInfo.order
  }
  handleFilter()
}

// 分页变化
const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.current = 1
  handleFilter()
}

const handleCurrentChange = (current: number) => {
  pagination.value.current = current
  handleFilter()
}

// 导出数据
const handleExport = () => {
  ElMessage.info('导出功能待实现')
}

// 组件挂载时加载表列表
onMounted(() => {
  console.log('📌 ImportedData.vue 组件已挂载，开始初始化...')
  loadTables()
})

// 添加组件初始化日志
defineExpose({
  name: 'ImportedData'
})

console.log('📦 ImportedData.vue 组件已加载，准备挂载...')
</script>

<style scoped>
.imported-data-screening {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.page-description {
  margin: 5px 0 0 40px;
  color: #606266;
}

.filter-panel {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-top: 20px;
}

.filter-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.data-list {
  margin-top: 20px;
}

.empty-state {
  padding: 40px 0;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>