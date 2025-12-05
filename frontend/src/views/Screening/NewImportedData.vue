<template>
  <div class="new-imported-data">
    <h1>导入数据筛选</h1>
    
    <!-- 表选择 -->
    <el-card class="table-selection-card" shadow="never">
      <h2>选择表</h2>
      <el-select 
        v-model="selectedTable" 
        placeholder="选择要筛选的表" 
        :loading="loadingTables"
        @change="handleTableChange"
        style="width: 300px; margin-bottom: 20px"
      >
        <el-option 
          v-for="table in tables" 
          :key="table" 
          :label="table" 
          :value="table" 
        />
      </el-select>
    </el-card>
    
    <!-- 筛选条件 -->
    <el-card v-if="selectedTable" class="filter-card" shadow="never">
      <h2>筛选条件</h2>
      <el-form :model="filterForm" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8" v-for="(filter, index) in filters" :key="index">
            <el-form-item :label="filter.label">
              <!-- 根据字段类型使用不同的输入组件 -->
              <!-- 数值类型使用范围筛选 -->
              <div v-if="filter.type === 'number'" class="range-filter">
                <el-input 
                  v-model="filter.minValue" 
                  placeholder="最小值" 
                  type="number"
                  @input="handleFilterChange"
                  style="margin-bottom: 10px;"
                />
                <el-input 
                  v-model="filter.maxValue" 
                  placeholder="最大值" 
                  type="number"
                  @input="handleFilterChange"
                />
              </div>
              <!-- 字符串类型使用普通输入框 -->
              <el-input 
                v-else-if="filter.type === 'string'" 
                v-model="filter.value" 
                placeholder="请输入" 
                @input="handleFilterChange"
              />
              <!-- 日期类型使用日期选择器 -->
              <el-date-picker
                v-else-if="filter.type === 'date'"
                v-model="filter.value"
                type="date"
                placeholder="选择日期"
                style="width: 100%"
                @change="handleFilterChange"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24">
            <el-form-item>
              <el-button type="primary" @click="applyFilters" :loading="loading">应用筛选</el-button>
              <el-button @click="resetFilters">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <!-- 数据列表 -->
    <el-card v-if="selectedTable" class="data-list-card" shadow="never">
      <div class="card-header">
        <h2>{{ selectedTable }} 表数据</h2>
        <div class="data-count">共 {{ total }} 条数据</div>
      </div>
      <el-table 
        :data="tableData" 
        stripe 
        style="width: 100%"
        :loading="loading"
      >
        <el-table-column 
          v-for="column in tableColumns" 
          :key="column" 
          :prop="column" 
          :label="column" 
          show-overflow-tooltip
          min-width="120"
        />
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination" v-if="total > 0">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </div>
    </el-card>
    
    <!-- 空状态 -->
    <el-empty v-if="!selectedTable" description="请选择要筛选的表" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { csvImportApi } from '@/api/csvImport'
import { ElMessage } from 'element-plus'

// 状态管理
const tables = ref<string[]>([])
const selectedTable = ref<string>('')
const loadingTables = ref(false)
const loading = ref(false)
const tableData = ref<any[]>([])
const tableColumns = ref<string[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filters = ref<any[]>([])
const filterForm = ref<any>({})

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
    // 加载导入的表列表（保存在本地存储中的表名）
    loadImportedTables()
    
    const response = await csvImportApi.getTables()
    if (response.success) {
      // 获取所有可用表
      const allTables = response.data
      console.log('📋 从API获取的所有表:', allTables)
      
      // 只显示通过CSV导入界面创建的表（保存在本地存储中的表名）
      tables.value = allTables.filter(table => 
        importedTables.value.includes(table)
      )
      console.log('📋 过滤后的表列表:', tables.value)
    } else {
      ElMessage.error('获取表列表失败')
    }
  } catch (error) {
    console.error('加载表列表失败:', error)
    ElMessage.error('获取表列表失败')
  } finally {
    loadingTables.value = false
  }
}

// 表选择变化处理
const handleTableChange = async (table: string) => {
  if (!table) return
  
  try {
    loading.value = true
    selectedTable.value = table
    tableData.value = []
    tableColumns.value = []
    filters.value = []
    filterForm.value = {}
    currentPage.value = 1
    total.value = 0
    
    // 获取表的基本信息
    const response = await csvImportApi.filterData({
      table: selectedTable.value,
      filters: {},
      page: 1,
      page_size: 10,
      sort: '',
      order: ''
    })
    
    if (response.success) {
      // 获取总数
      total.value = response.total
      
      if (response.data.length > 0) {
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
        const columnsToDisplay = allColumns.filter(column => column !== '_id')
        
        // 确保导入日期字段被添加到显示列中
        if (!columnsToDisplay.includes('导入日期')) {
          columnsToDisplay.push('导入日期')
        }
        
        tableColumns.value = columnsToDisplay
        
        // 初始化筛选条件
        filters.value = []
        
        // 处理所有显示的列
        columnsToDisplay.forEach(column => {
          // 检查该字段是否存在于数据中
          const fieldExists = allPossibleColumns.has(column)
          let sampleValue: any = ''
          let fieldType = 'string'
          
          // 首先根据字段名推断类型
          // 检查字段名是否包含数值相关关键词
          const numericKeywords = ['%', '元', '亿', '万', '金额', '值', '数', '率', '量', '价']
          const hasNumericKeyword = numericKeywords.some(keyword => column.includes(keyword))
          
          // 如果字段名包含数值相关关键词，直接识别为数值类型
          if (hasNumericKeyword) {
            fieldType = 'number'
          }
          // 如果字段名不包含数值关键词，再根据字段值推断类型
          else if (fieldExists) {
            // 找第一个包含该字段的记录
            const sampleRow = sampleRows.find(row => row.hasOwnProperty(column))
            if (sampleRow) {
              sampleValue = sampleRow[column]
              
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
          if (column === '导入日期') {
            fieldType = 'date'
          }
          
          // 初始化筛选条件对象
          const filterObj = {
            field: column,
            label: column,
            type: fieldType,
            value: '',
            minValue: null,
            maxValue: null
          }
          
          filters.value.push(filterObj)
          filterForm.value[column] = ''
        })
        
        tableData.value = response.data
      } else {
        // 表为空时的处理逻辑
        // 默认显示导入日期筛选选项
        tableColumns.value = ['导入日期']
        filters.value = [
          {
            field: '导入日期',
            label: '导入日期',
            type: 'date',
            value: '',
            minValue: null,
            maxValue: null
          }
        ]
        filterForm.value['导入日期'] = ''
        tableData.value = []
      }
    }
  } catch (error) {
    console.error('获取表信息失败:', error)
    ElMessage.error('获取表信息失败')
  } finally {
    loading.value = false
  }
}

// 筛选条件变化
const handleFilterChange = () => {
  // 可以在这里实现实时筛选
}

// 应用筛选
const applyFilters = async () => {
  if (!selectedTable.value) return
  
  try {
    loading.value = true
    currentPage.value = 1
    
    // 构建筛选条件
    const filterParams: any = {}
    
    filters.value.forEach(filter => {
      if (filter.type === 'number') {
        // 数值类型使用范围筛选
        const field = filter.field
        const hasMin = filter.minValue !== null && filter.minValue !== '' && filter.minValue !== undefined
        const hasMax = filter.maxValue !== null && filter.maxValue !== '' && filter.maxValue !== undefined
        
        if (hasMin || hasMax) {
          filterParams[field] = {}
          
          if (hasMin) {
            filterParams[field]['$gte'] = Number(filter.minValue)
          }
          
          if (hasMax) {
            filterParams[field]['$lte'] = Number(filter.maxValue)
          }
        }
      } else {
        // 非数值类型使用普通筛选
        if (filter.value) {
          filterParams[filter.field] = filter.value
        }
      }
    })
    
    const response = await csvImportApi.filterData({
      table: selectedTable.value,
      filters: filterParams,
      page: currentPage.value,
      page_size: pageSize.value,
      sort: '',
      order: ''
    })
    
    if (response.success) {
      total.value = response.total
      tableData.value = response.data
    } else {
      ElMessage.error('筛选数据失败')
    }
  } catch (error) {
    console.error('筛选数据失败:', error)
    ElMessage.error('筛选数据失败')
  } finally {
    loading.value = false
  }
}

// 重置筛选条件
const resetFilters = () => {
  filters.value.forEach(filter => {
    filter.value = ''
    
    // 重置数值类型的范围筛选条件
    if (filter.type === 'number') {
      filter.minValue = null
      filter.maxValue = null
    }
    
    filterForm.value[filter.field] = ''
  })
  applyFilters()
}

// 分页变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  applyFilters()
}

const handleCurrentChange = (current: number) => {
  currentPage.value = current
  applyFilters()
}

// 组件挂载时加载表列表
onMounted(() => {
  loadTables()
})
</script>

<style scoped>
.new-imported-data {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 20px;
  color: #303133;
}

h2 {
  margin-bottom: 15px;
  color: #606266;
  font-size: 16px;
  font-weight: bold;
}

.table-selection-card,
.filter-card,
.data-list-card {
  margin-bottom: 20px;
  padding: 20px;
}

.data-count {
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>