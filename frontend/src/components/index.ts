import type { App } from 'vue'
import MarketSelector from './Global/MarketSelector.vue'
import MultiMarketStockSearch from './Global/MultiMarketStockSearch.vue'
import CSVImporter from './CSVImporter.vue'

// 全局组件注册
export function setupGlobalComponents(app: App) {
  // 注册多市场相关组件
  app.component('MarketSelector', MarketSelector)
  app.component('MultiMarketStockSearch', MultiMarketStockSearch)
  app.component('CSVImporter', CSVImporter)
}

export default setupGlobalComponents
