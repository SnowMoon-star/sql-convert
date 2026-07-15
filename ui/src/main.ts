import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import App from './App.vue'

import { addCollection } from '@iconify/vue'
import localIcons from './assets/local-icons.json'

localIcons.forEach((collection: any) => {
  addCollection(collection)
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

