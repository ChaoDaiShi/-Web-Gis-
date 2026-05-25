import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Security from '../views/Security.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'
import EditProfile from '../views/EditProfile.vue'
import About from '../views/About.vue'
import Admin from '../views/Admin.vue'
import Messages from '../views/Messages.vue'
import LostItems from '../views/LostItems.vue'
import LostItemDetail from '../views/LostItemDetail.vue'
import ClaimForm from '../views/ClaimForm.vue'
import ClaimReview from '../views/ClaimReview.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/home', component: Home },
  { path: '/security', component: Security },
  { path: '/profile', component: Profile },
  { path: '/edit', component: EditProfile },
  { path: '/about', component: About },
  { path: '/admin', component: Admin },
  { path: '/messages', component: Messages },
  { path: '/lost-items', component: LostItems },
  { path: '/lost-item-detail', component: LostItemDetail },
  { path: '/claim-form', component: ClaimForm },
  { path: '/claim-review', component: ClaimReview }
]

export default createRouter({
  history: createWebHistory(),
  routes
})