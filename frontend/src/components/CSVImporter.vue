<template>
  <div class="csv-importer">
    <el-card shadow="hover" :bordered="false">
      <template #header>
        <div class="card-header">
          <span>CSV数据导入</span>
        </div>
      </template>

      <!-- 文件上传区域 -->
      <el-upload
        v-model:file-list="fileList"
        accept=".csv"
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        drag
        class="upload-area"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽CSV文件到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持单个CSV文件上传，文件大小不超过10MB
          </div>
        </template>
      </el-upload>

      <!-- 操作按钮 -->
      <div class="action-buttons" v-if="fileList.length > 0">
        <el-button type="primary" @click="handleParseCSV">解析文件</el-button>
        <el-button @click="resetImport">重置</el-button>
      </div>

      <!-- 字段映射区域 -->
      <div class="field-mapping" v-if="parsedData.length > 0">
        <h3>字段预览与映射</h3>
        <p>共识别到 {{ columns.length }} 个字段，{{ parsedData.length }} 条数据</p>
        
        <!-- 预览表格 -->
        <div class="preview-table-wrapper">
          <el-table :data="previewData" stripe style="width: 100%">
            <el-table-column
              v-for="(column, index) in columns"
              :key="index"
              :prop="column"
              :label="column"
              show-overflow-tooltip
            />
          </el-table>
        </div>

        <!-- 导入设置 -->
        <div class="import-settings">
          <el-form :model="importForm" label-width="120px">
            <el-form-item label="目标数据表">
              <el-select 
                v-model="importForm.targetTable" 
                placeholder="选择现有表或输入新表名创建表" 
                :loading="loadingTables"
                style="width: 100%"
                filterable
                allow-create
                default-first-option
              >
                <el-option 
                  v-for="table in tables" 
                  :key="table" 
                  :label="table" 
                  :value="table" 
                />
              </el-select>
              <div class="el-form-item__help">
                <el-tag type="info" size="small">提示</el-tag>
                <span v-if="importForm.importMode === 'insert'">
                  选择现有表或输入新表名自动创建新表
                </span>
                <span v-else>
                  只能选择现有表进行更新操作
                </span>
              </div>
            </el-form-item>
            <el-form-item label="导入模式">
              <el-select v-model="importForm.importMode" placeholder="请选择导入模式" @change="handleImportModeChange">
                <el-option label="新增" value="insert" />
                <el-option label="更新" value="update" />
                <el-option label="新增或更新" value="upsert" />
              </el-select>
              <div class="el-form-item__help">
                <el-tag type="warning" size="small">注意</el-tag>
                <span v-if="importForm.importMode === 'update'">
                  更新模式需要数据中包含唯一标识符（如_id），否则会导入失败
                </span>
                <span v-else-if="importForm.importMode === 'upsert'">
                  新增或更新模式：如果有唯一标识符则更新，否则新增
                </span>
                <span v-else>
                  新增模式：直接插入新数据
                </span>
              </div>
            </el-form-item>
          </el-form>
        </div>

        <!-- 导入按钮 -->
        <div class="import-actions">
          <el-button type="success" size="large" @click="handleImport" :loading="importing">
            <el-icon v-if="!importing"><upload /></el-icon>
            <el-icon v-else><Loading /></el-icon>
            开始导入
          </el-button>
          <el-button size="large" @click="resetImport">取消</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled, Loading } from '@element-plus/icons-vue'
import { csvImportApi } from '../api/csvImport'

// 定义类型
interface UploadFile {
  uid: string
  name: string
  status?: string
  response?: any
  url?: string
  raw?: File
}

// 文件列表
const fileList = ref<UploadFile[]>([])
// 解析后的数据
const parsedData = ref<any[]>([])
// 列名
const columns = ref<string[]>([])
// 导入状态
const importing = ref(false)
// 表列表
const tables = ref<string[]>([])
// 导入的表列表（从本地存储获取）
const importedTables = ref<string[]>([])
// 加载表列表状态
const loadingTables = ref(false)

// 导入表单
const importForm = ref({
  targetTable: '',
  importMode: 'insert' as 'insert' | 'update' | 'upsert'
})

// 预览数据（最多显示10行）
const previewData = computed(() => {
  return parsedData.value.slice(0, 10)
})

// 加载导入的表列表（从本地存储）
const loadImportedTables = () => {
  try {
    const savedTables = localStorage.getItem('importedTables')
    if (savedTables) {
      importedTables.value = JSON.parse(savedTables)
    }
  } catch (error) {
    console.error('加载导入表列表失败:', error)
    importedTables.value = []
  }
}

// 保存导入的表列表到本地存储
const saveImportedTables = (tableName: string) => {
  if (!importedTables.value.includes(tableName)) {
    importedTables.value.push(tableName)
    localStorage.setItem('importedTables', JSON.stringify(importedTables.value))
  }
}

// 加载表列表
const loadTables = async () => {
  try {
    loadingTables.value = true
    // 加载导入的表列表
    loadImportedTables()
    
    const response = await csvImportApi.getTables()
    if (response.success) {
      // 获取所有可用表
      const allTables = response.data
      
      // 无论什么模式，都只显示通过CSV导入界面创建的表（保存在本地存储中的表名）
      // 同时，用户可以输入新表名创建新表
      tables.value = allTables.filter(table => 
        importedTables.value.includes(table)
      )
    }
  } catch (error) {
    console.error('加载表列表失败:', error)
    ElMessage.error('加载表列表失败')
  } finally {
    loadingTables.value = false
  }
}

// 初始化函数，确保pingtoudi表被添加到本地存储中
const initImportedTables = async () => {
  try {
    // 加载现有导入的表列表
    loadImportedTables()
    
    // 获取所有可用表
    const response = await csvImportApi.getTables()
    if (response.success) {
      const allTables = response.data
      // 检查是否存在pingtoudi表
      if (allTables.includes('pingtoudi') && !importedTables.value.includes('pingtoudi')) {
        // 将pingtoudi表添加到本地存储中
        saveImportedTables('pingtoudi')
      }
      // 可以添加更多需要默认显示的表
    }
  } catch (error) {
    console.error('初始化导入表列表失败:', error)
  }
}

// 组件挂载时加载表列表和初始化
onMounted(async () => {
  await initImportedTables()
  loadTables()
})

// 文件变化处理
const handleFileChange = (file: UploadFile) => {
  console.log('文件变化:', file)
}

// 文件超出限制处理
const handleExceed = () => {
  ElMessage.warning('只能上传一个CSV文件')
}

// 解析CSV文件
const handleParseCSV = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择CSV文件')
    return
  }

  const file = fileList.value[0].raw
  if (!file) {
    ElMessage.error('文件无效')
    return
  }

  try {
    const text = await readFileAsText(file)
    let { headers, rows } = parseCSV(text)
    
    // 确保日期列被正确添加，即使CSV文件中已经存在同名列
    const dateColumnName = '导入日期'
    const currentDate = new Date().toISOString().split('T')[0] // 格式：YYYY-MM-DD
    
    console.log('📅 准备添加导入日期:', currentDate)
    console.log('📋 原始列名:', headers)
    
    // 为每一行数据添加日期列
    const rowsWithDate = rows.map(row => {
      const newRow = { ...row }
      newRow[dateColumnName] = currentDate // 添加或覆盖导入日期列
      return newRow
    })
    
    // 更新列名，确保包含导入日期列
    let headersWithDate = [...headers]
    if (!headersWithDate.includes(dateColumnName)) {
      headersWithDate = [...headers, dateColumnName]
    }
    
    // 保存到响应式变量
    columns.value = headersWithDate
    parsedData.value = rowsWithDate
    
    console.log('✅ 已为所有数据添加导入日期')
    console.log('📋 更新后的列名:', headersWithDate)
    console.log('📋 前2行数据（含日期）:', parsedData.value.slice(0, 2))
    
    ElMessage.success(`成功解析 ${rows.length} 条数据，并添加了导入日期列`)
  } catch (error) {
    console.error('解析CSV失败:', error)
    console.error('失败详情:', error.stack)
    ElMessage.error('解析CSV文件失败，请检查文件格式')
  }
}

// 读取文件为文本
const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      resolve(e.target?.result as string)
    }
    reader.onerror = reject
    reader.readAsText(file, 'utf-8')
  })
}

// 解析CSV文本
const parseCSV = (text: string) => {
  // 处理不同换行符
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').filter(line => line.trim())
  
  if (lines.length === 0) {
    return { headers: [], rows: [] }
  }
  
  // 解析表头
  const headers = parseCSVLine(lines[0])
  
  // 解析数据行
  const rows = lines.slice(1).map(line => {
    const values = parseCSVLine(line)
    const row: any = {}
    headers.forEach((header, index) => {
      row[header] = values[index] || ''
    })
    return row
  })
  
  return { headers, rows }
}

// 解析单行CSV
const parseCSVLine = (line: string): string[] => {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  let i = 0
  
  while (i < line.length) {
    const char = line[i]
    
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        // 转义引号
        current += '"'
        i += 2
      } else {
        inQuotes = !inQuotes
        i++
      }
    } else if (char === ',' && !inQuotes) {
      // 字段分隔符
      result.push(current)
      current = ''
      i++
    } else {
      current += char
      i++
    }
  }
  
  // 添加最后一个字段
  result.push(current)
  
  return result
}

// 导入模式变化处理
const handleImportModeChange = () => {
  // 重新加载表列表，确保根据导入模式显示正确的表
  loadTables()
}

// 重置导入
const resetImport = () => {
  fileList.value = []
  parsedData.value = []
  columns.value = []
  importForm.value = {
    targetTable: '',
    importMode: 'insert'
  }
  // 重新加载表列表
  loadTables()
}

// 数据验证
const validateData = () => {
  // 检查数据是否为空
  if (parsedData.value.length === 0) {
    ElMessage.warning('没有可导入的数据')
    return false
  }

  // 检查每行数据的字段数量是否一致
  const expectedFields = columns.value.length
  const invalidRows = parsedData.value.filter((row, index) => {
    const actualFields = Object.keys(row).length
    return actualFields !== expectedFields
  })

  if (invalidRows.length > 0) {
    ElMessage.error(`发现 ${invalidRows.length} 行数据字段数量不一致，请检查CSV文件格式`)
    return false
  }

  // 检查必填字段（如果有）
  // TODO: 根据表结构获取必填字段列表
  
  // 检查数据类型（基本验证）
  // 可以根据列名进行一些基本的数据类型推测和验证
  const numericColumns = columns.value.filter(col => 
    col.toLowerCase().includes('id') || 
    col.toLowerCase().includes('number') || 
    col.toLowerCase().includes('amount') || 
    col.toLowerCase().includes('price') || 
    col.toLowerCase().includes('value') || 
    col.toLowerCase().includes('count')
  )

  let validationErrors = 0
  parsedData.value.forEach((row, rowIndex) => {
    numericColumns.forEach(col => {
      const value = row[col]
      if (value && isNaN(Number(value))) {
        validationErrors++
        if (validationErrors < 5) {
          ElMessage.warning(`第 ${rowIndex + 1} 行，"${col}" 字段的值 "${value}" 不是有效的数字`)
        }
      }
    })
  })

  if (validationErrors > 0) {
    if (validationErrors >= 5) {
      ElMessage.error(`共发现 ${validationErrors} 个数据类型错误，请检查CSV文件`)
    }
    // 允许继续导入，但显示警告
  }

  return true
}

// 处理导入
const handleImport = async () => {
  console.log('🔍 开始处理导入')
  
  if (parsedData.value.length === 0) {
    console.log('⚠️ 未解析CSV文件')
    ElMessage.warning('请先解析CSV文件')
    return
  }

  if (!importForm.value.targetTable) {
    console.log('⚠️ 未选择目标数据表')
    ElMessage.warning('请选择目标数据表')
    return
  }

  console.log(`📊 准备导入 ${parsedData.value.length} 条数据到 ${importForm.value.targetTable} 表`)
  console.log(`📋 导入模式: ${importForm.value.importMode}`)
  console.log(`📋 列数: ${columns.value.length}`)
  console.log(`📋 前2行数据:`, parsedData.value.slice(0, 2))

  // 数据验证
  if (!validateData()) {
    console.log('⚠️ 数据验证失败')
    // 询问用户是否继续导入
    try {
      await ElMessageBox.confirm(
        '发现数据格式问题，是否继续导入？',
        '验证警告',
        {
          confirmButtonText: '继续导入',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      console.log('✅ 用户确认继续导入')
    } catch {
      console.log('❌ 用户取消导入')
      return
    }
  } else {
    console.log('✅ 数据验证通过')
  }

  try {
    await ElMessageBox.confirm(
      `确认要导入 ${parsedData.value.length} 条数据到 ${importForm.value.targetTable} 表吗？`,
      '导入确认',
      {
        confirmButtonText: '确认导入',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    console.log('✅ 用户确认导入')

    importing.value = true
    
    console.log('🚀 开始调用API导入数据')
    
    // 调用API导入数据
    const response = await csvImportApi.importData({
      table: importForm.value.targetTable,
      mode: importForm.value.importMode,
      data: parsedData.value,
      columns: columns.value
    })
    
    console.log('📡 API响应:', response)
    
    if (response.success) {
        console.log('✅ API调用成功')
        console.log('📊 API返回结果:', response.data)
        
        // 保存导入的表名到本地存储
        saveImportedTables(importForm.value.targetTable)
        // 刷新表列表
        await loadTables()
        
        // 根据实际导入情况显示不同的提示信息
        const totalImported = response.data.imported
        const totalFailed = response.data.failed
        
        console.log(`📊 导入统计: 成功 ${totalImported} 条，失败 ${totalFailed} 条`)
        
        // 检查是否所有数据都失败了
        if (totalFailed > 0 && totalImported === 0) {
          // 所有数据都失败了，显示失败提示
          console.log(`❌ 所有数据导入失败`)
          ElMessage.error(`数据导入失败，共导入 ${totalImported} 条，失败 ${totalFailed} 条`)
        } else if (totalImported > 0) {
          // 有成功导入的记录，显示成功提示
          console.log(`🎉 数据导入完成，部分成功`)
          ElMessage.success(`数据导入完成，共导入 ${totalImported} 条，失败 ${totalFailed} 条`)
        } else if (totalFailed > 0) {
          // 没有成功导入的记录，但有失败的记录，显示失败提示
          console.log(`❌ 数据导入失败`)
          ElMessage.error(`数据导入失败，共导入 ${totalImported} 条，失败 ${totalFailed} 条`)
        } else {
          // 没有成功也没有失败的记录，显示警告提示
          console.log(`⚠️ 数据导入完成，但没有导入任何记录`)
          ElMessage.warning(`数据导入完成，但没有导入任何记录，共导入 ${totalImported} 条，失败 ${totalFailed} 条`)
        }
        
        resetImport()
      } else {
        console.log(`❌ API调用失败: ${response.message}`)
        ElMessage.error(response.message || '数据导入失败')
      }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('❌ 导入失败:', error)
      console.error('❌ 错误栈:', error.stack)
      ElMessage.error(error.message || '数据导入失败')
    } else {
      console.log('❌ 用户取消导入')
    }
  } finally {
    importing.value = false
    console.log('🔚 导入流程结束')
  }
}
</script>

<style scoped>
.csv-importer {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  margin-bottom: 20px;
}

.action-buttons {
  margin-bottom: 20px;
}

.field-mapping {
  margin-top: 20px;
}

.field-mapping h3 {
  margin-bottom: 10px;
  font-size: 16px;
  font-weight: bold;
}

.field-mapping p {
  margin-bottom: 20px;
  color: #606266;
}

.preview-table-wrapper {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.import-settings {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.import-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}
</style>