import { reactive } from 'vue'
import { api } from './api'

export const sessionState = reactive({
  loading: true,
  ready: false,
  operatorName: '',
})

export async function refreshSession() {
  sessionState.loading = true
  try {
    const session = await api.getSession()
    sessionState.ready = true
    sessionState.operatorName = session.operator_name
  } catch {
    sessionState.ready = false
    sessionState.operatorName = localStorage.getItem('voc_operator_name') || ''
  } finally {
    sessionState.loading = false
  }
}

