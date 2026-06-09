import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Security from '../components/Security.vue'
import Login from '../views/Login.vue'
import Profile from '../components/Profile.vue'
import EditProfile from '../components/EditProfile.vue'
import About from '../components/About.vue'
import Admin from '../views/Admin.vue'
import Messages from '../components/Messages.vue'
import ClaimForm from '../components/ClaimForm.vue'
import ReturnForm from '../components/ReturnForm.vue'
import Navigation from '../views/Navigation.vue'
import Community from '../views/Community.vue'
import CommunityNotifications from '../views/CommunityNotifications.vue'
import AppointmentForm from '../components/AppointmentForm.vue'
import AppointmentList from '../components/AppointmentList.vue'
import AppointmentManage from '../components/AppointmentManage.vue'
import AppointmentCreate from '../components/AppointmentCreate.vue'
import UserProfile from '../views/UserProfile.vue'
import Chat from '../views/Chat.vue'
import Friends from '../views/Friends.vue'
import ReturnAppointment from '../views/ReturnAppointment.vue'

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
  { path: '/return-form', component: ReturnForm },
  { path: '/navigation', component: Navigation },
  { path: '/community', component: Community },
  { path: '/community/notifications', component: CommunityNotifications },
  { path: '/appointment/form', component: AppointmentForm },
  { path: '/appointment/list', component: AppointmentList },
  { path: '/appointment/create', component: AppointmentCreate },
  { path: '/user/:id', component: UserProfile },
  { path: '/chat', component: Chat },
  { path: '/chat/:id', component: Chat },
  { path: '/friends', component: Friends },
  { path: '/return-appointment', component: ReturnAppointment },
  {
    path: '/admin',
    component: Admin,
    beforeEnter() {
      if (localStorage.getItem('is_admin') !== '1') {
        return '/login'
      }
      return true
    },
    children: [
      { path: 'appointments', component: AppointmentManage }
    ]
  },
]

export default createRouter({
  history: createWebHistory(),
  routes
})