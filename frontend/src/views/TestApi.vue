<template>
  <div class="test-api">
    <h1>API 测试页面</h1>
    <div class="test-section">
      <h2>测试 1: 获取表列表</h2>
      <el-button type="primary" @click="testGetTables">调用 /api/csv/tables</el-button>
      <div v-if="tablesResponse" class="response">
        <pre>{{ JSON.stringify(tablesResponse, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="test-section">
      <h2>测试 2: 获取 pingtoudi 表数据</h2>
      <el-button type="primary" @click="testFilterData">调用 /api/csv/filter</el-button>
      <div v-if="filterResponse" class="response">
        <pre>{{ JSON.stringify(filterResponse, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { csvImportApi } from '@/api/csvImport'
import { ElMessage } from 'element-plus'

const tablesResponse = ref<any>(null)
const filterResponse = ref<any>(null)

const testGetTables = async () => {
  try {
    console.log('开始调用 getTables API...')
    const response = await csvImportApi.getTables()
    console.log('getTables API 响应:', response)
    tablesResponse.value = response
    ElMessage.success('获取表列表成功')
  } catch (error) {
    console.error('获取表列表失败:', error)
    ElMessage.error('获取表列表失败')
  }
}

const testFilterData = async () => {
  try {
    console.log('开始调用 filterData API...')
    const response = await csvImportApi.filterData({
      table: 'pingtoudi',
      filters: {},
      page: 1,
      page_size: 5,
      sort: '',
      order: ''
    })
    console.log('filterData API 响应:', response)
    filterResponse.value = response
    ElMessage.success('获取表数据成功')
  } catch (error) {
    console.error('获取表数据失败:', error)
    ElMessage.error('获取表数据失败')
  }
}
</script>

<style scoped>
.test-api {
  padding: 20px;
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.response {
  margin-top: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  overflow: auto;
  max-height: 400px;
}

pre {
  margin: 0;
  font-family: monospace;
  white-space: pre-wrap;
}
</style>