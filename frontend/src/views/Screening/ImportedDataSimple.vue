<template>
  <div class="imported-data-screening-simple">
    <h1>导入数据筛选（简化版）</h1>
    
    <!-- 表选择 -->
    <div class="table-selection">
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
    </div>
    
    <!-- 数据列表 -->
    <div v-if="selectedTable" class="data-list">
      <h2>{{ selectedTable }} 表数据</h2>
      <el-button 
        type="primary" 
        @click="fetchTableData"
        :loading="loading"
        style="margin-bottom: 20px"
      >
        获取数据
      </el-button>
      
      <div v-if="tableData.length > 0" class="table-container">
        <el-table :data="tableData" stripe style="width: 100%">
          <el-table-column 
            v-for="column in tableColumns" 
            :key="column" 
            :prop="column" 
            :label="column" 
            show-overflow-tooltip
          />
        </el-table>
      </div>
      <div v-else-if="loading" class="loading">
        <el-spinner /> 正在加载数据...
      </div>
      <div v-else class="no-data">
        暂无数据
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { csvImportApi } from '@/api/csvImport'

// 状态管理
const tables = ref<string[]>([])
const selectedTable = ref<string>('')
const loadingTables = ref(false)
const loading = ref(false)
const tableData = ref<any[]>([])
const tableColumns = ref<string[]>([])

// 加载表列表
const loadTables = async () => {
  try {
    loadingTables.value = true
    console.log('📌 开始调用 getTables API...')
    const response = await csvImportApi.getTables()
    console.log('📌 getTables API 响应:', response)
    
    if (response.success) {
      tables.value = response.data
      console.log('📌 获取到的表列表:', tables.value)
    } else {
      console.error('📌 getTables API 返回失败:', response)
    }
  } catch (error) {
    console.error('📌 加载表列表失败:', error)
  } finally {
    loadingTables.value = false
  }
}

// 表选择变化处理
const handleTableChange = (table: string) => {
  console.log('📌 表选择变化:', table)
  selectedTable.value = table
  tableData.value = []
  tableColumns.value = []
}

// 获取表数据
const fetchTableData = async () => {
  if (!selectedTable.value) return
  
  try {
    loading.value = true
    console.log('📌 开始调用 filterData API...')
    const response = await csvImportApi.filterData({
      table: selectedTable.value,
      filters: {},
      page: 1,
      page_size: 10,
      sort: '',
      order: ''
    })
    console.log('📌 filterData API 响应:', response)
    
    if (response.success) {
      tableData.value = response.data || []
      console.log('📌 获取到的数据数量:', tableData.value.length)
      
      // 获取所有列名
      if (tableData.value.length > 0) {
        const firstRow = tableData.value[0]
        if (firstRow) {
          tableColumns.value = Object.keys(firstRow)
          console.log('📌 表列名:', tableColumns.value)
        }
      }
    } else {
      console.error('📌 filterData API 返回失败:', response)
    }
  } catch (error) {
    console.error('📌 获取表数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载表列表
onMounted(() => {
  console.log('📌 ImportedDataSimple.vue 组件已挂载，开始初始化...')
  loadTables()
})

console.log('📦 ImportedDataSimple.vue 组件已加载，准备挂载...')
</script>

<style scoped>
.imported-data-screening-simple {
  padding: 20px;
}

.table-selection, .data-list {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.loading, .no-data {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.table-container {
  max-height: 600px;
  overflow: auto;
}
</style>