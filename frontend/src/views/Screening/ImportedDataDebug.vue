<template>
  <div class="imported-data-debug">
    <h1>导入数据筛选 - 调试版</h1>
    
    <!-- 调试信息面板 -->
    <el-card class="debug-panel" shadow="never">
      <h3>调试信息</h3>
      <pre class="debug-info">{{ debugInfo }}</pre>
    </el-card>
    
    <!-- 表选择 -->
    <el-card class="table-card" shadow="never">
      <h3>1. 选择表</h3>
      <el-select 
        v-model="selectedTable" 
        placeholder="选择要筛选的表" 
        :loading="loadingTables"
        @change="onTableChange"
        style="width: 300px; margin-bottom: 20px"
      >
        <el-option 
          v-for="table in tables" 
          :key="table" 
          :label="table" 
          :value="table" 
        />
      </el-select>
      <el-button type="primary" @click="refreshTablesList" :loading="loadingTables">
        <el-icon><Refresh /></el-icon> 刷新表列表
      </el-button>
    </el-card>
    
    <!-- 筛选条件 -->
    <el-card v-if="selectedTable && tableColumns.length > 0" class="filter-card" shadow="never">
      <h3>2. 设置筛选条件</h3>
      <el-form :model="filterForm" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8" v-for="(column, index) in tableColumns" :key="index">
            <el-form-item :label="column">
              <el-input 
                v-model="filterForm[column]" 
                placeholder="请输入筛选值"
                @input="onFilterChange"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="filter-actions">
          <el-button type="primary" @click="applyFilter">应用筛选</el-button>
          <el-button @click="resetFilter">重置筛选</el-button>
        </div>
      </el-form>
    </el-card>
    
    <!-- 数据列表 -->
    <el-card v-if="selectedTable" class="data-list-card" shadow="never">
      <h3>3. 数据列表</h3>
      <el-table 
        :data="tableData" 
        :loading="loadingData"
        style="width: 100%"
        v-loading="loadingData"
      >
        <el-table-column 
          v-for="column in tableColumns" 
          :key="column" 
          :prop="column" 
          :label="column"
          show-overflow-tooltip
        />
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="onPageSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { csvImportApi } from '@/api/csvImport'

// 状态管理
const tables = ref<string[]>([])
const selectedTable = ref<string>('')
const loadingTables = ref<boolean>(false)
const loadingData = ref<boolean>(false)
const tableColumns = ref<string[]>([])
const tableData = ref<any[]>([])
const total = ref<number>(0)
const filterForm = ref<Record<string, any>>({})
const debugInfo = ref<string>('')

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 20
})

// 构建调试信息
const updateDebugInfo = (message: string) => {
  const timestamp = new Date().toLocaleString()
  debugInfo.value += `[${timestamp}] ${message}\n`
}

// 刷新表列表
const refreshTablesList = async () => {
  try {
    updateDebugInfo('开始刷新表列表...')
    loadingTables.value = true
    const response = await csvImportApi.getTables()
    if (response.success) {
      tables.value = response.data
      updateDebugInfo(`表列表刷新成功，共 ${response.data.length} 个表`)
      // 如果没有选择表，默认选择第一个
      if (!selectedTable.value && tables.value.length > 0) {
        selectedTable.value = tables.value[0]
        updateDebugInfo(`默认选择表: ${tables.value[0]}`)
        await loadTableColumns(tables.value[0])
      }
    } else {
      updateDebugInfo(`表列表刷新失败: ${response.message}`)
      ElMessage.error('获取表列表失败')
    }
  } catch (error: any) {
    updateDebugInfo(`获取表列表异常: ${error.message}`)
    ElMessage.error('获取表列表失败')
  } finally {
    loadingTables.value = false
  }
}

// 加载表列
const loadTableColumns = async (table: string) => {
  try {
    updateDebugInfo(`开始加载表 ${table} 的列信息...`)
    // 清空之前的列信息
    tableColumns.value = []
    filterForm.value = {}
    
    // 简单获取表的前1条数据来获取列名
    const response = await csvImportApi.filterData({
      table,
      filters: {},
      page: 1,
      page_size: 1,
      sort: '',
      order: ''
    })
    
    if (response.success && response.data.length > 0) {
      const firstRow = response.data[0]
      tableColumns.value = Object.keys(firstRow)
      updateDebugInfo(`表 ${table} 列信息加载成功，共 ${tableColumns.value.length} 列`)
      // 初始化筛选表单
      tableColumns.value.forEach(col => {
        filterForm.value[col] = ''
      })
      // 加载数据
      await loadTableData(table, 1, pagination.value.pageSize)
    } else {
      updateDebugInfo(`表 ${table} 没有数据`)
      // 即使没有数据，也要初始化空的列列表，避免UI错误
      tableColumns.value = []
      tableData.value = []
      total.value = 0
    }
  } catch (error: any) {
    updateDebugInfo(`加载表 ${table} 列信息异常: ${error.message}`)
    ElMessage.error(`加载表 ${table} 列信息失败`)
  }
}

// 加载表数据
const loadTableData = async (table: string, page: number, pageSize: number) => {
  try {
    updateDebugInfo(`开始加载表 ${table} 数据，第 ${page} 页，每页 ${pageSize} 条...`)
    loadingData.value = true
    
    // 构建筛选条件
    const filters: Record<string, any> = {}
    tableColumns.value.forEach(col => {
      const value = filterForm.value[col]
      if (value !== '' && value !== undefined && value !== null) {
        filters[col] = value
      }
    })
    
    updateDebugInfo(`应用的筛选条件: ${JSON.stringify(filters)}`)
    
    const response = await csvImportApi.filterData({
      table,
      filters,
      page,
      page_size: pageSize,
      sort: '',
      order: ''
    })
    
    if (response.success) {
      tableData.value = response.data
      total.value = response.total
      updateDebugInfo(`表 ${table} 数据加载成功，共 ${response.total} 条，当前页 ${response.data.length} 条`)
    } else {
      updateDebugInfo(`表 ${table} 数据加载失败: ${response.message}`)
      ElMessage.error(`加载表 ${table} 数据失败`)
      tableData.value = []
      total.value = 0
    }
  } catch (error: any) {
    updateDebugInfo(`加载表 ${table} 数据异常: ${error.message}`)
    ElMessage.error(`加载表 ${table} 数据失败`)
    tableData.value = []
    total.value = 0
  } finally {
    loadingData.value = false
  }
}

// 表选择变化
const onTableChange = (table: string) => {
  updateDebugInfo(`表选择变化: ${table}`)
  // 重置分页
  pagination.value.current = 1
  // 加载表列
  loadTableColumns(table)
}

// 筛选条件变化
const onFilterChange = () => {
  updateDebugInfo('筛选条件变化，重置到第1页')
  pagination.value.current = 1
  // 可以选择自动应用筛选，或者等待用户点击应用按钮
  // loadTableData(selectedTable.value, 1, pagination.value.pageSize)
}

// 应用筛选
const applyFilter = () => {
  updateDebugInfo('应用筛选条件')
  loadTableData(selectedTable.value, 1, pagination.value.pageSize)
}

// 重置筛选
const resetFilter = () => {
  updateDebugInfo('重置筛选条件')
  // 重置筛选表单
  tableColumns.value.forEach(col => {
    filterForm.value[col] = ''
  })
  // 重新加载数据
  loadTableData(selectedTable.value, 1, pagination.value.pageSize)
}

// 分页变化
const onPageSizeChange = (size: number) => {
  updateDebugInfo(`页码大小变化: ${size}`)
  pagination.value.pageSize = size
  loadTableData(selectedTable.value, 1, size)
}

const onPageChange = (current: number) => {
  updateDebugInfo(`页码变化: ${current}`)
  pagination.value.current = current
  loadTableData(selectedTable.value, current, pagination.value.pageSize)
}

// 组件挂载时初始化
onMounted(() => {
  updateDebugInfo('组件挂载，开始初始化...')
  refreshTablesList()
})
</script>

<style scoped>
.imported-data-debug {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.debug-panel {
  margin-bottom: 20px;
}

.debug-info {
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.table-card {
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.data-list-card {
  margin-top: 20px;
}
</style>