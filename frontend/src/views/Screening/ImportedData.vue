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
                <el-input-number 
                  v-else-if="filter.type === 'number'" 
                  v-model="filter.value" 
                  :min="filter.min" 
                  :max="filter.max" 
                  :step="filter.step || 1" 
                  placeholder="输入数值" 
                />
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

// 加载表列表
const loadTables = async () => {
  try {
    loadingTables.value = true
    const response = await csvImportApi.getTables()
    if (response.success) {
      tables.value = response.data
      if (tables.value.length > 0 && !selectedTable.value) {
        selectedTable.value = tables.value[0]
        handleTableChange(selectedTable.value)
      }
    }
  } catch (error) {
    console.error('加载表列表失败:', error)
    ElMessage.error('加载表列表失败')
  } finally {
    loadingTables.value = false
  }
}

// 表选择变化处理
const handleTableChange = async (table: string) => {
  if (!table) return

  try {
    loading.value = true
    // 这里可以根据表结构动态生成筛选条件
    // 先获取表的一些样本数据来分析结构
    await analyzeTableStructure(table)
    // 重置筛选条件
    resetFilters()
    // 执行筛选
    handleFilter()
  } catch (error) {
    console.error('分析表结构失败:', error)
    ElMessage.error('分析表结构失败')
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
    
    // 先获取一些样本数据来分析表结构
    const response = await csvImportApi.filterData({
      table,
      filters: {},
      page: 1,
      page_size: 10,
      sort: '',
      order: ''
    })
    
    if (response.success) {
      if (response.data && response.data.length > 0) {
        // 获取所有列名
        const firstRow = response.data[0]
        if (firstRow) {
          tableColumns.value = Object.keys(firstRow)
          
          // 为每一列生成筛选条件
          tableColumns.value.forEach(col => {
            // 根据列名和样本数据类型推断字段类型
            const sampleValue = firstRow[col]
            let fieldType = 'string'
            
            // 推断字段类型
            if (typeof sampleValue === 'number') {
              fieldType = 'number'
            } else if (typeof sampleValue === 'string') {
              // 检查是否是日期格式
              if (/^\d{4}-\d{2}-\d{2}/.test(sampleValue) || sampleValue.includes('T') || sampleValue.includes(':')) {
                fieldType = 'date'
              }
            }
            
            // 生成筛选条件
            dynamicFilters.value.push({
              field: col,
              label: col,
              type: fieldType,
              value: ''
            })
          })
          
          console.log(`✅ 分析表结构完成，表: ${table}，列: ${tableColumns.value.length} 个`)
        }
      } else {
        // 表为空，没有数据
        console.log(`⚠️ 表 ${table} 为空，没有数据可分析`)
      }
    } else {
      ElMessage.error(response.message || '获取表数据失败')
    }
  } catch (error) {
    console.error('分析表结构失败:', error)
    ElMessage.error('分析表结构失败')
  }
}

// 重置筛选条件
const resetFilters = () => {
  dynamicFilters.value.forEach(filter => {
    filter.value = ''
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
      if (filter.value !== '' && filter.value !== undefined && filter.value !== null) {
        filterParams.filters[filter.field] = filter.value
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
  if (typeof value === 'string' && (column.toLowerCase().includes('date') || column.toLowerCase().includes('time'))) {
    try {
      const date = new Date(value)
      if (!isNaN(date.getTime())) {
        return date.toLocaleString()
      }
    } catch {
      // 不是有效日期，返回原始值
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
  loadTables()
})
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