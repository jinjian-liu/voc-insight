import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/feedbacks' },
    { path: '/feedbacks', component: () => import('./views/FeedbackPage.vue') },
    { path: '/issues', component: () => import('./views/IssuePage.vue') },
    { path: '/dashboard', component: () => import('./views/DashboardPage.vue') },
    { path: '/settings', component: () => import('./views/SettingsPage.vue') },
  ],
})

export default router
