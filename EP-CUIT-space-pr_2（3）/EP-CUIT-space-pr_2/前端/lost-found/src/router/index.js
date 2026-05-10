import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Security from '../views/Security.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'
import EditProfile from '../views/EditProfile.vue'
import About from '../views/About.vue'
import Admin from '../views/Admin.vue'
import Messages from '../views/Messages.vue'
import ClaimForm from '../views/ClaimForm.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/home', component: Home },
  { path: '/security', component: Security },
  { path: '/profile', component: Profile },
  { path: '/edit', component: EditProfile },
  { path: '/about', component: About },
  { path: '/messages', component: Messages },
  { path: '/claim-form', component: ClaimForm },
  {
    path: '/admin',
    component: Admin,
    beforeEnter(to, from, next) {
      if (localStorage.getItem('is_admin') !== '1') {
        next('/login')
      } else {
        next()
      }
    },
  },
]

export default createRouter({
  history: createWebHistory(),
  routes
})