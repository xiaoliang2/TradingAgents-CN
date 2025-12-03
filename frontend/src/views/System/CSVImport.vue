<template>
  <div class="csv-import-page">
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/system' }">系统管理</el-breadcrumb-item>
      <el-breadcrumb-item>CSV数据导入</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="page-container">
      <el-card shadow="hover" :bordered="false">
        <template #header>
          <div class="card-header">
            <span>CSV数据导入</span>
            <el-button type="primary" size="small" @click="refreshTables">
              <el-icon><Refresh /></el-icon>
              刷新表列表
            </el-button>
          </div>
        </template>

        <div class="card-content">
          <CSVImporter ref="csvImporterRef" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import CSVImporter from '@/components/CSVImporter.vue'

// CSV导入组件引用
const csvImporterRef = ref()

// 刷新表列表
const refreshTables = () => {
  // 可以通过组件引用来调用组件内的方法
  if (csvImporterRef.value?.loadTables) {
    csvImporterRef.value.loadTables()
  }
}
</script>

<style scoped>
.csv-import-page {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  padding: 20px 0;
}
</style>