<template>
  <div class="admin-panel">
    <AppTopBar variant="admin">
      <template #actions>
        <button class="admin-logout" @click="logoutAdmin">退出后台</button>
      </template>
    </AppTopBar>

    <div class="admin-container">
      <div class="sidebar">
        <div class="sidebar-header">
          <h2>后台管理</h2>
        </div>
        <nav class="sidebar-nav">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['nav-item', { active: currentTab === tab.key }]"
            @click="switchTab(tab.key)"
          >
            <span class="nav-icon">{{ tab.icon }}</span>
            <span class="nav-label">{{ tab.label }}</span>
          </button>
        </nav>
      </div>

      <main class="main-content">
        <div v-if="loading" class="loading-overlay">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else class="content-panel">
          <div class="panel-header">
            <h1>{{ getCurrentTabLabel() }}</h1>
            <button class="btn-refresh" @click="loadData">刷新</button>
          </div>

          <div class="panel-body">
            <div v-if="currentTab === 'dashboard'" class="dashboard">
              <div class="stats-grid">
                <div class="stat-card">
                  <div class="stat-icon">👥</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ dashboardData.overview.total_users || 0 }}</div>
                    <div class="stat-label">总用户数</div>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon">📦</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ dashboardData.overview.total_items || 0 }}</div>
                    <div class="stat-label">总物品数</div>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon">✅</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ dashboardData.overview.total_claims || 0 }}</div>
                    <div class="stat-label">总认领数</div>
                  </div>
                </div>
                <div class="stat-card">
                  <div class="stat-icon">🔔</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ dashboardData.overview.pending_items || 0 }}</div>
                    <div class="stat-label">待审核物品</div>
                  </div>
                </div>
              </div>

              <div class="charts-grid charts-grid-viz">
                <div class="chart-card chart-card-wide">
                  <h3>物品分类分布</h3>
                  <AdminPieChart
                    :items="dashboardData.itemsByCategory"
                    label-key="category"
                    value-key="count"
                    :size="220"
                  />
                </div>

                <div class="chart-card chart-card-wide">
                  <h3>物品状态分布</h3>
                  <AdminPieChart
                    :items="dashboardData.itemsByStatus"
                    label-key="status"
                    value-key="count"
                    :size="220"
                  />
                </div>

                <div class="chart-card">
                  <h3>发布趋势（近7天）</h3>
                  <AdminBarChart
                    :items="dashboardData.itemsTrend"
                    label-key="date"
                    value-key="count"
                  />
                </div>

                <div class="chart-card">
                  <h3>用户活跃度 TOP</h3>
                  <AdminBarChart
                    :items="dashboardData.userActivity"
                    label-key="username"
                    value-key="action_count"
                  />
                </div>
              </div>
            </div>

            <div v-else-if="currentTab === 'users'" class="data-table">
              <div class="table-toolbar">
                <input v-model="searchKeyword" type="text" placeholder="搜索用户名、邮箱或手机号" class="search-input" />
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户名</th>
                    <th>邮箱</th>
                    <th>手机号</th>
                    <th>角色</th>
                    <th>状态</th>
                    <th>注册时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="user in filteredUsers"
                    :key="user.user_id"
                    class="clickable-row"
                    @dblclick="editUser(user)"
                  >
                    <td>{{ user.user_id }}</td>
                    <td>{{ user.username }}</td>
                    <td>{{ user.email || '-' }}</td>
                    <td>{{ user.phone || '-' }}</td>
                    <td>{{ user.role || 'student' }}</td>
                    <td>
                      <span :class="['status-badge', user.status || 'normal']">
                        {{ user.status === 'normal' ? '正常' : user.status }}
                      </span>
                    </td>
                    <td>{{ user.create_time || '-' }}</td>
                    <td class="actions">
                      <button class="btn-action" @click="editUser(user)">编辑</button>
                      <button class="btn-action" @click="updateUserStatus(user.user_id, user.status === 'normal' ? 'banned' : 'normal')">
                        {{ user.status === 'normal' ? '禁用' : '启用' }}
                      </button>
                      <button class="btn-danger" @click="deleteUser(user.user_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-else-if="currentTab === 'items'" class="data-table">
              <div class="table-toolbar">
                <input v-model="searchKeyword" type="text" placeholder="搜索物品标题或描述" class="search-input" />
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>标题</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th>审核状态</th>
                    <th>发布者ID</th>
                    <th>发布时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in filteredItems"
                    :key="item.item_id"
                    class="clickable-row"
                    @dblclick="editItem(item)"
                  >
                    <td>{{ item.item_id }}</td>
                    <td>{{ item.title }}</td>
                    <td>
                      <span :class="['type-badge', item.item_type]">
                        {{ item.item_type === 'lost' ? '丢失' : '招领' }}
                      </span>
                    </td>
                    <td>
                      <span :class="['status-badge', item.status]">
                        {{ item.status }}
                      </span>
                    </td>
                    <td>
                      <span :class="['status-badge', item.audit_status]">
                        {{ item.audit_status }}
                      </span>
                    </td>
                    <td>{{ item.publisher_id }}</td>
                    <td>{{ item.publish_time || item.create_time || '-' }}</td>
                    <td class="actions">
                      <button v-if="item.audit_status === 'pending'" class="btn-success" @click="auditItem(item.item_id, 'approved')">
                        通过
                      </button>
                      <button v-if="item.audit_status === 'pending'" class="btn-danger" @click="auditItem(item.item_id, 'rejected')">
                        拒绝
                      </button>
                      <button class="btn-action" @click="editItem(item)">编辑</button>
                      <button class="btn-action" @click="showDetail('物品详情', item.description || '无描述')">详情</button>
                      <button class="btn-danger" @click="deleteItem(item.item_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-else-if="currentTab === 'audit'" class="audit-center">
              <div class="audit-subnav">
                <button
                  :class="['audit-tab', { active: auditSubTab === 'publish' }]"
                  @click="auditSubTab = 'publish'"
                >
                  发布审核
                  <span v-if="pendingPublishCount" class="badge">{{ pendingPublishCount }}</span>
                </button>
                <button
                  :class="['audit-tab', { active: auditSubTab === 'verify' }]"
                  @click="auditSubTab = 'verify'"
                >
                  用户认证
                  <span v-if="pendingVerifyCount" class="badge">{{ pendingVerifyCount }}</span>
                </button>
                <button
                  :class="['audit-tab', { active: auditSubTab === 'claim' }]"
                  @click="auditSubTab = 'claim'"
                >
                  认领申请
                  <span v-if="pendingClaimCount" class="badge">{{ pendingClaimCount }}</span>
                </button>
                <button
                  :class="['audit-tab', { active: auditSubTab === 'return' }]"
                  @click="auditSubTab = 'return'"
                >
                  归还申请
                  <span v-if="pendingReturnCount" class="badge">{{ pendingReturnCount }}</span>
                </button>
              </div>

              <div v-if="auditSubTab === 'publish'" class="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>标题</th>
                      <th>类型</th>
                      <th>发布者ID</th>
                      <th>描述</th>
                      <th>状态</th>
                      <th>发布时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in publishAuditItems" :key="'a-p-' + item.item_id">
                      <td>{{ item.item_id }}</td>
                      <td>{{ item.title }}</td>
                      <td>
                        <span :class="['type-badge', item.item_type]">
                          {{ item.item_type === 'lost' ? '丢失' : '招领' }}
                        </span>
                      </td>
                      <td>{{ item.publisher_id }}</td>
                      <td>
                        <button class="btn-link" @click="showDetail('物品描述', item.description || '无')">查看</button>
                      </td>
                      <td>
                        <span :class="['status-badge', item.audit_status || 'pending']">
                          {{ item.audit_status === 'approved' ? '已通过' : item.audit_status === 'rejected' ? '已拒绝' : '待审核' }}
                        </span>
                      </td>
                      <td>{{ item.publish_time || item.create_time || '-' }}</td>
                      <td class="actions">
                        <template v-if="item.audit_status === 'pending'">
                          <button class="btn-success" @click="auditItem(item.item_id, 'approved')">通过</button>
                          <button class="btn-danger" @click="auditItem(item.item_id, 'rejected')">拒绝</button>
                        </template>
                        <span v-else class="muted">已处理</span>
                      </td>
                    </tr>
                    <tr v-if="!publishAuditItems.length"><td colspan="8" class="empty-row">暂无待审核发布</td></tr>
                  </tbody>
                </table>
              </div>

              <div v-else-if="auditSubTab === 'verify'" class="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>用户ID</th>
                      <th>身份</th>
                      <th>真实姓名</th>
                      <th>学号/工号</th>
                      <th>手机</th>
                      <th>状态</th>
                      <th>申请时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="v in verifyList" :key="'a-v-' + v.verify_id">
                      <td>{{ v.verify_id }}</td>
                      <td>{{ v.user_id }}</td>
                      <td>{{ formatIdentity(v.identity) }}</td>
                      <td>{{ v.real_name }}</td>
                      <td>{{ v.student_id || '-' }}</td>
                      <td>{{ v.phone || '-' }}</td>
                      <td><span :class="['status-badge', isPendingStatus(v.status) ? 'pending' : 'done']">{{ v.status_label || formatAuditStatus(v.status) }}</span></td>
                      <td>{{ v.create_time || '-' }}</td>
                      <td class="actions">
                        <button class="btn-link" @click="viewVerifyDetail(v)">材料</button>
                        <template v-if="isPendingStatus(v.status)">
                          <button class="btn-success" @click="approveVerify(v.verify_id)">通过</button>
                          <button class="btn-danger" @click="rejectVerify(v.verify_id)">拒绝</button>
                        </template>
                        <span v-else class="muted">已处理</span>
                      </td>
                    </tr>
                    <tr v-if="!verifyList.length"><td colspan="9" class="empty-row">暂无认证申请</td></tr>
                  </tbody>
                </table>
              </div>

              <div v-else-if="auditSubTab === 'claim'" class="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>物品ID</th>
                      <th>申请人</th>
                      <th>联系方式</th>
                      <th>认领理由</th>
                      <th>状态</th>
                      <th>申请时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="c in claimAuditList" :key="'a-c-' + c.claim_id">
                      <td>{{ c.claim_id }}</td>
                      <td>{{ c.item_id }}</td>
                      <td>{{ c.applicant_name || c.claimer_name || '-' }}</td>
                      <td>{{ c.applicant_phone || c.contact_info || '-' }}</td>
                      <td>
                        <button class="btn-link" @click="showDetail('认领理由', c.claim_reason || '无')">查看</button>
                      </td>
                      <td><span :class="['status-badge', isPendingStatus(c.status) ? 'pending' : 'done']">{{ c.status_label || formatAuditStatus(c.status) }}</span></td>
                      <td>{{ c.create_time || '-' }}</td>
                      <td class="actions">
                        <button v-if="c.proof_images" class="btn-link" @click="showDetail('证明材料', c.proof_images)">材料</button>
                        <template v-if="isPendingStatus(c.status)">
                          <button class="btn-success" @click="approveClaim(c.claim_id)">通过</button>
                          <button class="btn-danger" @click="rejectClaim(c.claim_id)">拒绝</button>
                        </template>
                        <span v-else class="muted">已处理</span>
                      </td>
                    </tr>
                    <tr v-if="!claimAuditList.length"><td colspan="8" class="empty-row">暂无认领申请</td></tr>
                  </tbody>
                </table>
              </div>

              <div v-else-if="auditSubTab === 'return'" class="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>物品ID</th>
                      <th>申请人</th>
                      <th>联系方式</th>
                      <th>归还理由</th>
                      <th>状态</th>
                      <th>申请时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="r in returnAuditList" :key="'a-r-' + r.return_id">
                      <td>{{ r.return_id }}</td>
                      <td>{{ r.item_id }}</td>
                      <td>{{ r.applicant_name || r.returner_name || '-' }}</td>
                      <td>{{ r.applicant_phone || r.contact_info || '-' }}</td>
                      <td>
                        <button class="btn-link" @click="showDetail('归还理由', r.return_reason || '无')">查看</button>
                      </td>
                      <td><span :class="['status-badge', isPendingStatus(r.status) ? 'pending' : 'done']">{{ r.status_label || formatAuditStatus(r.status) }}</span></td>
                      <td>{{ r.create_time || '-' }}</td>
                      <td class="actions">
                        <button v-if="r.proof_images" class="btn-link" @click="showDetail('证明材料', r.proof_images)">材料</button>
                        <template v-if="isPendingStatus(r.status)">
                          <button class="btn-success" @click="approveReturn(r.return_id)">通过</button>
                          <button class="btn-danger" @click="rejectReturn(r.return_id)">拒绝</button>
                        </template>
                        <span v-else class="muted">已处理</span>
                      </td>
                    </tr>
                    <tr v-if="!returnAuditList.length"><td colspan="8" class="empty-row">暂无归还申请</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-else-if="currentTab === 'categories'" class="data-table">
              <div class="table-toolbar">
                <button class="btn-primary" @click="addCategory">添加分类</button>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>分类名称</th>
                    <th>描述</th>
                    <th>排序</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="cat in categories"
                    :key="cat.id"
                    class="clickable-row"
                    @dblclick="editCategory(cat)"
                  >
                    <td>{{ cat.id }}</td>
                    <td>{{ cat.name }}</td>
                    <td>{{ cat.description || '-' }}</td>
                    <td>{{ cat.sort_order || 0 }}</td>
                    <td>
                      <span :class="['status-badge', cat.is_active ? 'active' : 'inactive']">
                        {{ cat.is_active ? '启用' : '禁用' }}
                      </span>
                    </td>
                    <td class="actions">
                      <button class="btn-action" @click="editCategory(cat)">编辑</button>
                      <button class="btn-danger" @click="deleteCategory(cat.id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-else-if="currentTab === 'admins'" class="data-table">
              <div class="table-toolbar">
                <input v-model="searchKeyword" type="text" placeholder="搜索管理员用户名" class="search-input" />
                <button class="btn-primary" @click="addAdmin">添加管理员</button>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户名</th>
                    <th>角色</th>
                    <th>部门</th>
                    <th>权限类型</th>
                    <th>权限列表</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="admin in filteredAdmins"
                    :key="admin.admin_id"
                    class="clickable-row"
                    @dblclick="editAdmin(admin)"
                  >
                    <td>{{ admin.admin_id }}</td>
                    <td>{{ admin.username }}</td>
                    <td>
                      <span :class="['status-badge', admin.role === 'super_admin' ? 'active' : 'pending']">
                        {{ admin.role === 'super_admin' ? '超级管理员' : '二级管理员' }}
                      </span>
                    </td>
                    <td>{{ admin.department || '-' }}</td>
                    <td>{{ admin.permission_type || '-' }}</td>
                    <td>
                      <button class="btn-link" @click="showAdminPermissions(admin)">查看</button>
                    </td>
                    <td>{{ admin.create_time || '-' }}</td>
                    <td class="actions">
                      <button v-if="admin.role !== 'super_admin'" class="btn-action" @click="editAdmin(admin)">编辑</button>
                      <button v-if="admin.role !== 'super_admin'" class="btn-action" @click="editAdminPermissions(admin)">设置权限</button>
                      <button v-if="admin.role !== 'super_admin'" class="btn-danger" @click="deleteAdmin(admin.admin_id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-else-if="currentTab === 'permissions'" class="permissions-panel">
              <div class="permissions-header">
                <h3>权限定义</h3>
              </div>
              <div class="permissions-grid">
                <div
                  v-for="perm in permissions"
                  :key="perm.permission_id"
                  class="permission-card"
                >
                  <div class="permission-header">
                    <span class="permission-key">{{ perm.permission_key }}</span>
                    <span class="permission-category">{{ perm.category }}</span>
                  </div>
                  <div class="permission-name">{{ perm.permission_name }}</div>
                  <div class="permission-desc">{{ perm.description }}</div>
                </div>
              </div>

              <div class="permissions-header" style="margin-top: 30px;">
                <h3>权限申请审核</h3>
              </div>
              <div class="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>申请ID</th>
                      <th>申请人</th>
                      <th>申请权限</th>
                      <th>申请理由</th>
                      <th>状态</th>
                      <th>申请时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="req in privilegeRequests" :key="req.request_id">
                      <td>{{ req.request_id }}</td>
                      <td>{{ req.admin_username || req.admin_id }}</td>
                      <td>{{ formatRequestedPermissions(req.requested_permissions) }}</td>
                      <td>
                        <button class="btn-link" @click="showDetail('申请理由', req.reason || '无')">查看</button>
                      </td>
                      <td>
                        <span :class="['status-badge', req.status === 'pending' ? 'pending' : 'done']">
                          {{ req.status === 'pending' ? '待审核' : req.status === 'approved' ? '已通过' : '已拒绝' }}
                        </span>
                      </td>
                      <td>{{ req.create_time || '-' }}</td>
                      <td class="actions">
                        <template v-if="req.status === 'pending'">
                          <button class="btn-success" @click="approvePrivilegeRequest(req.request_id)">通过</button>
                          <button class="btn-danger" @click="rejectPrivilegeRequest(req.request_id)">拒绝</button>
                        </template>
                        <span v-else class="muted">已处理</span>
                      </td>
                    </tr>
                    <tr v-if="!privilegeRequests.length"><td colspan="7" class="empty-row">暂无权限申请</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-else-if="currentTab === 'repair'" class="data-table">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>标题</th>
                    <th>分类</th>
                    <th>报修人</th>
                    <th>状态</th>
                    <th>优先级</th>
                    <th>处理人</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="repair in repairList" :key="'r-' + repair.repair_id">
                    <td>{{ repair.repair_id }}</td>
                    <td>{{ repair.title }}</td>
                    <td>{{ repair.category_name || '-' }}</td>
                    <td>{{ repair.reporter_name || repair.reporter_id }}</td>
                    <td>
                      <span :class="['status-badge', getRepairStatusClass(repair.status)]">
                        {{ getRepairStatusText(repair.status) }}
                      </span>
                    </td>
                    <td>
                      <span :class="['priority-badge', getPriorityClass(repair.priority)]">
                        {{ getPriorityText(repair.priority) }}
                      </span>
                    </td>
                    <td>{{ repair.assignee_id || '-' }}</td>
                    <td>{{ repair.create_time || '-' }}</td>
                    <td class="actions">
                      <button class="btn-link" @click="showDetail('报修详情', repair.description || '无')">查看</button>
                      <button v-if="repair.status !== 2 && repair.status !== 3" class="btn-action" @click="editRepair(repair)">编辑</button>
                      <button v-if="repair.status !== 2 && repair.status !== 3" class="btn-success" @click="changeRepairStatus(repair.repair_id, 2)">完成</button>
                      <button class="btn-danger" @click="deleteRepair(repair.repair_id)">删除</button>
                    </td>
                  </tr>
                  <tr v-if="!repairList.length"><td colspan="9" class="empty-row">暂无报修记录</td></tr>
                </tbody>
              </table>
              <div v-if="repairTotal > 0" class="pagination">
                <button class="btn-page" :disabled="repairPage <= 1" @click="loadRepairList(repairPage - 1)">上一页</button>
                <span class="page-info">第 {{ repairPage }} 页，共 {{ Math.ceil(repairTotal / 20) }} 页</span>
                <button class="btn-page" :disabled="repairPage >= Math.ceil(repairTotal / 20)" @click="loadRepairList(repairPage + 1)">下一页</button>
              </div>
            </div>

            <div v-else-if="currentTab === 'logs'" class="data-table">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户ID</th>
                    <th>操作</th>
                    <th>目标类型</th>
                    <th>目标ID</th>
                    <th>详情</th>
                    <th>IP地址</th>
                    <th>时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="log in logs"
                    :key="log.id"
                    class="clickable-row"
                  >
                    <td>{{ log.id }}</td>
                    <td>{{ log.user_id || '-' }}</td>
                    <td>{{ log.action }}</td>
                    <td>{{ log.target_type || '-' }}</td>
                    <td>{{ log.target_id || '-' }}</td>
                    <td>
                      <button class="btn-link" @click="showDetail('日志详情', log.detail || '无')">
                        查看
                      </button>
                    </td>
                    <td>{{ log.ip_address || '-' }}</td>
                    <td>{{ log.created_at || '-' }}</td>
                  </tr>
                  <tr v-if="!logs.length"><td colspan="8" class="empty-row">暂无日志记录</td></tr>
                </tbody>
              </table>
              <div v-if="logsTotal > 0" class="pagination">
                <button 
                  class="btn-page" 
                  :disabled="logsPage <= 1" 
                  @click="loadLogs(logsPage - 1)"
                >
                  上一页
                </button>
                <span class="page-info">第 {{ logsPage }} 页，共 {{ Math.ceil(logsTotal / 20) }} 页</span>
                <button 
                  class="btn-page" 
                  :disabled="logsPage >= Math.ceil(logsTotal / 20)" 
                  @click="loadLogs(logsPage + 1)"
                >
                  下一页
                </button>
              </div>
            </div>

            <div v-else-if="currentTab === 'configs'" class="data-table">
              <table>
                <thead>
                  <tr>
                    <th>配置键</th>
                    <th>配置值</th>
                    <th>描述</th>
                    <th>更新时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="config in configs"
                    :key="config.config_key"
                    class="clickable-row"
                    @dblclick="editConfig(config)"
                  >
                    <td>{{ config.config_key }}</td>
                    <td>{{ config.config_value || '-' }}</td>
                    <td>{{ config.description || '-' }}</td>
                    <td>{{ config.updated_at || '-' }}</td>
                    <td class="actions">
                      <button class="btn-action" @click="editConfig(config)">编辑</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-else-if="currentTab === 'tables'" class="tables-manager">
              <aside class="table-sidebar">
                <p class="sidebar-title">数据库表</p>
                <button
                  v-for="t in tables"
                  :key="t"
                  :class="['table-pick', { active: selectedTable === t }]"
                  @click="selectTable(t)"
                >
                  {{ t }}
                </button>
              </aside>
              <section class="table-main">
                <div v-if="!selectedTable" class="table-placeholder">← 选择左侧数据表</div>
                <template v-else>
                  <div class="table-toolbar">
                    <span class="table-name">{{ selectedTable }}</span>
                    <button class="btn-primary" @click="loadTableRows">刷新</button>
                    <button class="btn-action" @click="insertTableRow">新建行</button>
                  </div>
                  <div class="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th v-for="col in tableColumns" :key="col">{{ col }}</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="row in tableRows"
                          :key="getRowKey(row)"
                          class="clickable-row"
                          @dblclick="editTableRow(row)"
                        >
                          <td v-for="col in tableColumns" :key="col">{{ formatCell(row[col]) }}</td>
                          <td class="actions">
                            <button class="btn-action" @click="editTableRow(row)">编辑</button>
                            <button class="btn-danger" @click="deleteTableRow(row)">删除</button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <p class="hint">双击行可像 DataGrip 一样编辑字段；请谨慎修改生产数据。</p>
                </template>
              </section>
            </div>
          </div>
        </div>
      </main>
    </div>

    <RecordEditorModal
      v-model:visible="editorVisible"
      :title="editorTitle"
      :subtitle="editorSubtitle"
      :fields="editorFields"
      :readonly="editorReadonly"
      :saving="editorSaving"
      @save="onEditorSave"
    />

    <div v-if="showDetailModal" class="modal-overlay" @click="closeDetailModal">
      <div class="modal-content detail-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ detailTitle }}</h3>
          <button class="modal-close" @click="closeDetailModal">&times;</button>
        </div>
        <div class="modal-body" v-if="detailType === 'text'">
          <textarea readonly :value="detailContent" class="detail-textarea"></textarea>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";
import AdminPieChart from "../components/admin/AdminPieChart.vue";
import AdminBarChart from "../components/admin/AdminBarChart.vue";
import RecordEditorModal from "../components/admin/RecordEditorModal.vue";

const router = useRouter();
const showToast = window.showToast;
const showConfirm = window.showConfirm;
const API_ORIGIN = import.meta.env.VITE_API_BASE_URL || '';

const tabs = [
  { key: 'dashboard', label: '仪表板', icon: '📊' },
  { key: 'users', label: '用户管理', icon: '👥' },
  { key: 'items', label: '物品管理', icon: '📦' },
  { key: 'audit', label: '审核中心', icon: '🔍' },
  { key: 'categories', label: '分类管理', icon: '📁' },
  { key: 'repair', label: '报修管理', icon: '🔧' },
  { key: 'admins', label: '管理员管理', icon: '🛡️' },
  { key: 'permissions', label: '权限管理', icon: '🔐' },
  { key: 'logs', label: '系统日志', icon: '📝' },
  { key: 'configs', label: '系统配置', icon: '⚙️' },
  { key: 'tables', label: '数据表管理', icon: '🗄️' }
];

const currentTab = ref('dashboard');
const auditSubTab = ref('publish');
const loading = ref(false);
const searchKeyword = ref('');

function isPendingStatus(status) {
  return status === 0 || status === '0' || status === 'pending' || status === '待审核';
}

function formatAuditStatus(status) {
  if (status === 0 || status === '0' || status === 'pending') return '待审核';
  if (status === 1 || status === '1' || status === 'approved') return '已通过';
  if (status === 2 || status === '2' || status === 'rejected') return '已拒绝';
  return String(status ?? '未知');
}

function formatIdentity(identity) {
  const map = { student: '学生', teacher: '教师', maintenance: '维修员', staff: '教职工' };
  return map[identity] || identity || '-';
}

const pendingVerifyCount = computed(() => verifyList.value.filter((v) => isPendingStatus(v.status)).length);
const pendingPublishCount = computed(() => publishAuditItems.value.length);
const pendingClaimCount = computed(() => claimAuditList.value.filter((c) => isPendingStatus(c.status)).length);
const pendingReturnCount = computed(() => returnAuditList.value.filter((r) => isPendingStatus(r.status)).length);

function getCurrentTabLabel() {
  const tab = tabs.find(t => t.key === currentTab.value);
  return tab ? tab.label : '未定义';
}

function switchTab(tab) {
  currentTab.value = tab;
  loadData();
}

function logoutAdmin() {
  localStorage.removeItem("is_admin");
  localStorage.removeItem("admin_token");
  router.push("/login");
}

async function fetchAPI(url, options = {}) {
  try {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    const token = localStorage.getItem('admin_token');
    if (localStorage.getItem('is_admin') === '1' && token && !headers.Authorization) {
      headers.Authorization = `Bearer ${token}`;
    }
    const res = await fetch(`${API_ORIGIN}${url}`, {
      ...options,
      headers
    });
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      throw new Error(res.ok ? '响应格式错误' : `请求失败 (${res.status})`);
    }
    if (!res.ok || (data && data.code && data.code >= 400) || data?.success === false) {
      throw new Error(data.message || '请求失败');
    }
    return data;
  } catch (err) {
    console.error('API Error:', err);
    if (!options.silent) {
      showToast(err.message, 'error');
    }
    throw err;
  }
}

onMounted(() => {
  loadData();
});

const dashboardData = ref({
  overview: {},
  itemsByCategory: [],
  itemsByStatus: [],
  itemsTrend: [],
  userActivity: []
});

const users = ref([]);
const items = ref([]);
const categories = ref([]);
const logs = ref([]);
const verifyList = ref([]);
const publishAuditItems = ref([]);
const claimAuditList = ref([]);
const returnAuditList = ref([]);
const repairList = ref([]);
const repairPage = ref(1);
const repairTotal = ref(0);
const configs = ref([]);

// 管理员管理相关
const admins = ref([]);
const permissions = ref([]);
const privilegeRequests = ref([]);

const filteredAdmins = computed(() => {
  if (!searchKeyword.value) return admins.value;
  const kw = searchKeyword.value.toLowerCase();
  return admins.value.filter(a => a.username && a.username.toLowerCase().includes(kw));
});
const tables = ref([]);
const selectedTable = ref('');
const tableColumns = ref([]);
const tableRows = ref([]);
const tablePkField = ref('');

const editorVisible = ref(false);
const editorTitle = ref('');
const editorSubtitle = ref('');
const editorFields = ref([]);
const editorReadonly = ref(false);
const editorSaving = ref(false);
let editorSaveHandler = null;

const filteredUsers = computed(() => {
  if (!searchKeyword.value) return users.value;
  const kw = searchKeyword.value.toLowerCase();
  return users.value.filter(u => 
    (u.username && u.username.toLowerCase().includes(kw)) ||
    (u.email && u.email.toLowerCase().includes(kw)) ||
    (u.phone && u.phone.includes(kw))
  );
});

const filteredItems = computed(() => {
  if (!searchKeyword.value) return items.value;
  const kw = searchKeyword.value.toLowerCase();
  return items.value.filter(i => 
    (i.title && i.title.toLowerCase().includes(kw)) ||
    (i.description && i.description.toLowerCase().includes(kw))
  );
});

async function loadData() {
  loading.value = true;
  try {
    switch (currentTab.value) {
      case 'dashboard':
        await loadDashboard();
        break;
      case 'users':
        await loadUsers();
        break;
      case 'items':
        await loadItems();
        break;
      case 'audit':
        await loadAuditData();
        break;
      case 'categories':
        await loadCategories();
        break;
      case 'repair':
        await loadRepairList();
        break;
      case 'admins':
        await loadAdmins();
        break;
      case 'permissions':
        await loadPermissions();
        break;
      case 'logs':
        await loadLogs();
        break;
      case 'configs':
        await loadConfigs();
        break;
      case 'tables':
        await loadTables();
        break;
    }
  } finally {
    loading.value = false;
  }
}

async function loadDashboard() {
  const endpoints = [
    { key: 'overview', url: '/api/admin/statistics/overview' },
    { key: 'itemsByCategory', url: '/api/admin/statistics/items-by-category' },
    { key: 'itemsByStatus', url: '/api/admin/statistics/items-by-status' },
    { key: 'itemsTrend', url: '/api/admin/statistics/items-trend' },
    { key: 'userActivity', url: '/api/admin/statistics/user-activity' }
  ];
  const results = await Promise.allSettled(
    endpoints.map((e) => fetchAPI(e.url, { silent: true }))
  );
  const next = { ...dashboardData.value };
  results.forEach((result, i) => {
    const { key, url } = endpoints[i];
    if (result.status === 'fulfilled') {
      const payload = result.value;
      next[key] = payload.data ?? payload;
    } else {
      console.error(`加载仪表板失败 [${url}]:`, result.reason);
    }
  });
  dashboardData.value = next;
  const failed = results.filter((r) => r.status === 'rejected').length;
  if (failed > 0 && failed < endpoints.length) {
    showToast(`部分统计数据加载失败（${failed}/${endpoints.length}）`, 'error');
  } else if (failed === endpoints.length) {
    showToast('加载仪表板失败', 'error');
  }
}

async function loadUsers() {
  try {
    const data = await fetchAPI('/api/admin/users');
    users.value = data.data?.users || data.data || data || [];
  } catch (err) {
    console.error('加载用户失败:', err);
  }
}

async function loadItems() {
  try {
    const data = await fetchAPI('/api/admin/lost_items');
    items.value = data.data || data || [];
  } catch (err) {
    console.error('加载物品失败:', err);
  }
}

function normalizeListResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.data)) return data.data;
  return [];
}

async function loadVerifications() {
  try {
    const data = await fetchAPI('/api/admin/user-verify');
    verifyList.value = normalizeListResponse(data);
  } catch (err) {
    console.error('加载用户认证失败:', err);
    verifyList.value = [];
  }
}

async function loadPublishAudit() {
  try {
    const data = await fetchAPI('/api/admin/lost_items?audit_status=pending');
    publishAuditItems.value = data.data || data || [];
  } catch (err) {
    console.error('加载发布审核失败:', err);
    publishAuditItems.value = [];
  }
}

async function loadAuditData() {
  await Promise.all([loadPublishAudit(), loadVerifications(), loadClaimAudit(), loadReturnAudit()]);
}

async function loadClaimAudit() {
  try {
    const data = await fetchAPI('/api/admin/claim-forms');
    claimAuditList.value = data.data || data || [];
  } catch (err) {
    console.error('加载认领审核失败:', err);
    claimAuditList.value = [];
  }
}

async function loadReturnAudit() {
  try {
    const data = await fetchAPI('/api/admin/return-forms');
    returnAuditList.value = data.data || data || [];
  } catch (err) {
    console.error('加载归还审核失败:', err);
    returnAuditList.value = [];
  }
}

async function approveClaim(claimId) {
  const confirmed = await showConfirm({ title: '通过认领', message: '确定通过该物品的认领申请吗？', type: 'success', confirmText: '通过' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/claim-forms/${claimId}/approve`, { method: 'POST' });
    showToast('认领已通过', 'success');
    await loadAuditData();
  } catch (err) {
    console.error('通过认领失败:', err);
  }
}

async function rejectClaim(claimId) {
  const confirmed = await showConfirm({ title: '拒绝认领', message: '确定拒绝该物品的认领申请吗？', type: 'warning', confirmText: '拒绝' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/claim-forms/${claimId}/reject`, { method: 'POST' });
    showToast('已拒绝认领', 'success');
    await loadAuditData();
  } catch (err) {
    console.error('拒绝认领失败:', err);
  }
}

async function approveReturn(returnId) {
  const confirmed = await showConfirm({ title: '通过归还', message: '确定通过该物品的归还申请吗？', type: 'success', confirmText: '通过' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/return-forms/${returnId}/approve`, { method: 'POST' });
    showToast('归还已通过', 'success');
    await loadAuditData();
  } catch (err) {
    console.error('通过归还失败:', err);
  }
}

async function rejectReturn(returnId) {
  const confirmed = await showConfirm({ title: '拒绝归还', message: '确定拒绝该物品的归还申请吗？', type: 'warning', confirmText: '拒绝' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/return-forms/${returnId}/reject`, { method: 'POST' });
    showToast('已拒绝归还', 'success');
    await loadAuditData();
  } catch (err) {
    console.error('拒绝归还失败:', err);
  }
}

async function approveVerify(verifyId) {
  const confirmed = await showConfirm({ title: '通过认证', message: '确定通过该用户的实名认证吗？', type: 'success', confirmText: '通过' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/user-verify/${verifyId}/approve`, { method: 'POST' });
    showToast('认证已通过', 'success');
    await loadAuditData();
  } catch (err) {
    console.error('通过认证失败:', err);
  }
}

async function rejectVerify(verifyId) {
  const confirmed = await showConfirm({ title: '拒绝认证', message: '确定拒绝该用户的实名认证吗？', type: 'warning', confirmText: '拒绝' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/user-verify/${verifyId}/reject`, { method: 'POST' });
    showToast('已拒绝认证', 'success');
    await loadAuditData();
  } catch (err) {
    console.error('拒绝认证失败:', err);
  }
}

function viewVerifyDetail(v) {
  const lines = [
    `用户ID: ${v.user_id}`,
    `身份: ${formatIdentity(v.identity)}`,
    `姓名: ${v.real_name}`,
    `学号/工号: ${v.student_id || '-'}`,
    `学校: ${v.school || '-'}`,
    `手机: ${v.phone || '-'}`,
    `邮箱: ${v.email || '-'}`,
    `身份证: ${v.id_card || '-'}`,
    `（证件照请在数据库或后续版本中预览）`
  ];
  showDetail('认证材料摘要', lines.join('\n'));
}

async function loadCategories() {
  try {
    const data = await fetchAPI('/api/admin/categories');
    categories.value = data.data || data || [];
  } catch (err) {
    console.error('加载分类失败:', err);
  }
}

const logsPage = ref(1);
const logsTotal = ref(0);

async function loadRepairList(page = 1) {
  try {
    const params = new URLSearchParams({ page });
    const data = await fetchAPI(`/api/admin/repair-list?${params}`);
    repairList.value = data.data?.repairs || data.data || data || [];
    repairTotal.value = data.data?.total || 0;
    repairPage.value = page;
  } catch (err) {
    console.error('加载报修列表失败:', err);
    repairList.value = [];
  }
}

function getRepairStatusText(status) {
  const statusMap = {
    0: '待处理',
    1: '处理中',
    2: '已完成',
    3: '已关闭'
  };
  return statusMap[status] || '未知';
}

function getRepairStatusClass(status) {
  const classMap = {
    0: 'pending',
    1: 'processing',
    2: 'done',
    3: 'closed'
  };
  return classMap[status] || 'pending';
}

function getPriorityText(priority) {
  const priorityMap = {
    1: '低',
    2: '中',
    3: '高'
  };
  return priorityMap[priority] || '低';
}

function getPriorityClass(priority) {
  const classMap = {
    1: 'priority-low',
    2: 'priority-medium',
    3: 'priority-high'
  };
  return classMap[priority] || 'priority-low';
}

function editRepair(repair) {
  openRecordEditor(`报修 #${repair.repair_id}`, repair, { subtitle: '编辑报修' }, async (updated) => {
    try {
      await fetchAPI(`/api/admin/repair/${repair.repair_id}`, {
        method: 'PUT',
        body: JSON.stringify(updated)
      });
      showToast('更新成功', 'success');
      await loadRepairList();
    } catch (err) {
      console.error('更新报修失败:', err);
    }
  });
}

async function changeRepairStatus(repairId, status) {
  const statusText = getRepairStatusText(status);
  const confirmed = await showConfirm({ title: `设置状态为${statusText}`, message: `确定将该报修状态设置为${statusText}吗？`, type: 'success', confirmText: '确认' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/repair/${repairId}`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    });
    showToast('状态已更新', 'success');
    await loadRepairList();
  } catch (err) {
    console.error('更新状态失败:', err);
  }
}

async function deleteRepair(repairId) {
  const confirmed = await showConfirm({ title: '删除报修', message: '确定删除该报修记录吗？', type: 'danger', confirmText: '删除' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/repair/${repairId}`, { method: 'DELETE' });
    showToast('删除成功', 'success');
    await loadRepairList();
  } catch (err) {
    console.error('删除报修失败:', err);
  }
}

async function loadLogs(page = 1) {
  try {
    const params = new URLSearchParams({ page });
    const data = await fetchAPI(`/api/admin/logs?${params}`);
    logs.value = data.data?.logs || data.data || data || [];
    logsTotal.value = data.data?.total || 0;
    logsPage.value = page;
  } catch (err) {
    console.error('加载日志失败:', err);
  }
}

async function loadConfigs() {
  try {
    const data = await fetchAPI('/api/admin/configs');
    configs.value = data.data || data || [];
  } catch (err) {
    console.error('加载配置失败:', err);
  }
}

async function loadTables() {
  try {
    const data = await fetchAPI('/api/admin/tables');
    tables.value = data.data || data || [];
  } catch (err) {
    console.error('加载表列表失败:', err);
  }
}

async function loadAdmins() {
  try {
    const data = await fetchAPI('/api/admin/admins');
    admins.value = data.data || data || [];
  } catch (err) {
    console.error('加载管理员列表失败:', err);
    admins.value = [];
  }
}

async function loadPermissions() {
  try {
    const [permData, reqData] = await Promise.all([
      fetchAPI('/api/admin/permissions'),
      fetchAPI('/api/admin/privilege-requests')
    ]);
    permissions.value = permData.data || permData || [];
    privilegeRequests.value = reqData.data || reqData || [];
  } catch (err) {
    console.error('加载权限数据失败:', err);
    permissions.value = [];
    privilegeRequests.value = [];
  }
}

async function addAdmin() {
  const username = prompt('请输入管理员用户名：');
  if (!username) return;
  const password = prompt('请输入管理员密码：');
  if (!password) return;
  try {
    await fetchAPI('/api/admin/admins', {
      method: 'POST',
      body: JSON.stringify({ username, password, role: 'secondary_admin' })
    });
    showToast('添加成功', 'success');
    await loadAdmins();
  } catch (err) {
    console.error('添加管理员失败:', err);
  }
}

async function deleteAdmin(adminId) {
  const confirmed = await showConfirm({ title: '删除管理员', message: '确定删除该管理员吗？', type: 'danger', confirmText: '删除' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/admins/${adminId}`, { method: 'DELETE' });
    showToast('删除成功', 'success');
    await loadAdmins();
  } catch (err) {
    console.error('删除管理员失败:', err);
  }
}

function showAdminPermissions(admin) {
  let perms = [];
  if (admin.role === 'super_admin') {
    perms = ['所有权限'];
  } else if (admin.permissions) {
    try {
      perms = JSON.parse(admin.permissions);
    } catch {
      perms = [admin.permissions];
    }
  }
  showDetail('权限列表', perms.join('\n'));
}

function editAdmin(admin) {
  openRecordEditor(`管理员 #${admin.admin_id}`, admin, {
    readonlyKeys: ['admin_id', 'username', 'create_time'],
    editableKeys: ['admin_id', 'username', 'role', 'department', 'permission_type']
  }, async (data) => {
    await fetchAPI(`/api/admin/admins/${admin.admin_id}`, {
      method: 'PUT',
      body: JSON.stringify({
        role: data.role,
        department: data.department,
        permission_type: data.permission_type
      })
    });
    showToast('保存成功', 'success');
    await loadAdmins();
  });
}

async function editAdminPermissions(admin) {
  const currentPerms = admin.role === 'super_admin' ? [] : (admin.permissions ? JSON.parse(admin.permissions) : []);
  const availablePerms = permissions.value.filter(p => !currentPerms.includes(p.permission_key));
  
  let permList = '当前权限:\n' + (currentPerms.length ? currentPerms.join('\n') : '无') + '\n\n可选权限:\n';
  availablePerms.forEach((p, i) => {
    permList += `${i + 1}. ${p.permission_key} - ${p.permission_name}\n`;
  });
  
  const input = prompt(`请选择要添加的权限（输入序号，多个用逗号分隔，清空请输入"clear"）：\n\n${permList}`);
  if (input === null) return;
  
  let newPerms = [...currentPerms];
  if (input === 'clear') {
    newPerms = [];
  } else {
    const indices = input.split(',').map(i => parseInt(i.trim()) - 1).filter(i => i >= 0 && i < availablePerms.length);
    indices.forEach(i => {
      if (!newPerms.includes(availablePerms[i].permission_key)) {
        newPerms.push(availablePerms[i].permission_key);
      }
    });
  }
  
  try {
    await fetchAPI(`/api/admin/admins/${admin.admin_id}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({ permissions: newPerms })
    });
    showToast('权限更新成功', 'success');
    await loadAdmins();
  } catch (err) {
    console.error('更新权限失败:', err);
  }
}

function formatRequestedPermissions(permissionsStr) {
  if (!permissionsStr) return '-';
  try {
    const perms = JSON.parse(permissionsStr);
    return Array.isArray(perms) ? perms.join(', ') : permissionsStr;
  } catch {
    return permissionsStr;
  }
}

async function approvePrivilegeRequest(requestId) {
  const confirmed = await showConfirm({ title: '通过权限申请', message: '确定通过该权限申请吗？', type: 'success', confirmText: '通过' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/privilege-requests/${requestId}/approve`, { method: 'POST' });
    showToast('已通过', 'success');
    await loadPermissions();
  } catch (err) {
    console.error('通过权限申请失败:', err);
  }
}

async function rejectPrivilegeRequest(requestId) {
  const confirmed = await showConfirm({ title: '拒绝权限申请', message: '确定拒绝该权限申请吗？', type: 'warning', confirmText: '拒绝' });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/privilege-requests/${requestId}/reject`, { method: 'POST' });
    showToast('已拒绝', 'success');
    await loadPermissions();
  } catch (err) {
    console.error('拒绝权限申请失败:', err);
  }
}

async function updateUserStatus(userId, status) {
  const confirmed = await showConfirm({title: '修改用户状态', message: `确定要将用户状态修改为"${status}"吗？`, type: 'warning', confirmText: '确认'});
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    });
    showToast('修改成功', 'success');
    await loadUsers();
  } catch (err) {
    console.error('修改用户状态失败:', err);
  }
}

async function deleteUser(userId) {
  const confirmed = await showConfirm({title: '删除用户', message: '确定要删除该用户吗？此操作不可恢复！', type: 'danger', confirmText: '删除用户'});
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/users/${userId}`, {
      method: 'DELETE'
    });
    showToast('删除成功', 'success');
    await loadUsers();
  } catch (err) {
    console.error('删除用户失败:', err);
  }
}

async function auditItem(itemId, status) {
  console.log('[auditItem] 开始审核操作:', { itemId, status, API_ORIGIN });
  const confirmed = await showConfirm({title: '物品审核', message: `确定要${status === 'approved' ? '通过' : '拒绝'}该物品吗？`, type: status === 'approved' ? 'success' : 'warning', confirmText: '确认'});
  console.log('[auditItem] 确认对话框结果:', confirmed);
  if (!confirmed) {
    console.log('[auditItem] 用户取消了审核');
    return;
  }
  try {
    console.log('[auditItem] 发送请求:', `${API_ORIGIN}/api/admin/items/${itemId}/audit`);
    await fetchAPI(`/api/admin/items/${itemId}/audit`, {
      method: 'POST',
      body: JSON.stringify({ audit_status: status })
    });
    console.log('[auditItem] 请求成功');
    showToast('审核成功', 'success');
    await loadItems();
    if (currentTab.value === 'audit') await loadAuditData();
  } catch (err) {
    console.error('[auditItem] 请求失败:', err);
  }
}

async function deleteItem(itemId) {
  const confirmed = await showConfirm({title: '删除物品', message: '确定要删除该物品吗？', type: 'danger', confirmText: '删除'});
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/lost_items/${itemId}`, {
      method: 'DELETE'
    });
    showToast('删除成功', 'success');
    await loadItems();
  } catch (err) {
    console.error('删除物品失败:', err);
  }
}

async function addCategory() {
  const name = prompt('请输入分类名称：');
  if (!name) return;
  const description = prompt('请输入分类描述：', '');
  try {
    await fetchAPI('/api/admin/categories', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    });
    showToast('添加成功', 'success');
    await loadCategories();
  } catch (err) {
    console.error('添加分类失败:', err);
  }
}

function buildEditorFields(record, options = {}) {
  const {
    readonlyKeys = [],
    editableKeys = null,
    jsonKeys = [],
    textareaKeys = ['description', 'reason', 'detail', 'content', 'claim_reason', 'return_reason', 'config_value']
  } = options;
  const keys = editableKeys || Object.keys(record);
  return keys.map((key) => {
    const raw = record[key];
    const readonly = readonlyKeys.includes(key);
    let type = 'text';
    if (readonly) type = 'readonly';
    else if (jsonKeys.includes(key) || (typeof raw === 'object' && raw !== null)) type = 'json';
    else if (textareaKeys.includes(key)) type = 'textarea';
    else if (typeof raw === 'number') type = 'number';

    let value = raw;
    if (type === 'json' && value !== null && typeof value === 'object') {
      value = JSON.stringify(value, null, 2);
    } else if (value === null || value === undefined) {
      value = '';
    }

    return { key, value, type, readonly };
  });
}

function openRecordEditor(title, record, options, onSave, readonly = false) {
  editorTitle.value = title;
  editorSubtitle.value = options.subtitle || '双击行可快速打开 · 主键字段不可修改';
  editorFields.value = buildEditorFields(record, options);
  editorReadonly.value = readonly;
  editorSaveHandler = onSave;
  editorVisible.value = true;
}

async function onEditorSave(payload) {
  if (!editorSaveHandler) return;
  editorSaving.value = true;
  try {
    await editorSaveHandler(payload);
    editorVisible.value = false;
  } catch (err) {
    console.error('保存失败:', err);
  } finally {
    editorSaving.value = false;
  }
}

function editUser(user) {
  openRecordEditor(`用户 #${user.user_id}`, user, {
    readonlyKeys: ['user_id', 'username', 'create_time'],
    editableKeys: ['user_id', 'username', 'email', 'phone', 'role', 'status', 'create_time']
  }, async (data) => {
    await fetchAPI(`/api/admin/users/${user.user_id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    showToast('保存成功', 'success');
    await loadUsers();
  });
}

function editItem(item) {
  openRecordEditor(`物品 #${item.item_id}`, item, {
    readonlyKeys: ['item_id', 'id', 'publish_time', 'create_time', 'publisher_name', 'category_name'],
    editableKeys: ['item_id', 'title', 'description', 'item_type', 'status', 'category_id', 'publisher_id'],
    jsonKeys: ['image_url', 'image_urls']
  }, async (data) => {
    await fetchAPI(`/api/admin/lost_items/${item.item_id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    showToast('保存成功', 'success');
    await loadItems();
  });
}

function editCategory(cat) {
  openRecordEditor(`分类 #${cat.id}`, cat, {
    readonlyKeys: ['id']
  }, async (data) => {
    await fetchAPI(`/api/admin/categories/${cat.id}`, {
      method: 'PUT',
      body: JSON.stringify({ name: data.name, description: data.description, sort_order: data.sort_order, is_active: data.is_active })
    });
    showToast('保存成功', 'success');
    await loadCategories();
  });
}

function editConfig(config) {
  openRecordEditor(`配置 ${config.config_key}`, config, {
    readonlyKeys: ['config_key', 'description', 'updated_at'],
    textareaKeys: ['config_value', 'description']
  }, async (data) => {
    await fetchAPI(`/api/admin/configs/${config.config_key}`, {
      method: 'PUT',
      body: JSON.stringify({ config_value: typeof data.config_value === 'object' ? JSON.stringify(data.config_value) : data.config_value })
    });
    showToast('保存成功', 'success');
    await loadConfigs();
  });
}

function editLog(log) {
  openRecordEditor(`系统日志 #${log.id}`, log, { subtitle: '只读查看' }, async () => {}, true);
}

function formatCell(val) {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'object') return JSON.stringify(val);
  const s = String(val);
  return s.length > 48 ? s.slice(0, 48) + '…' : s;
}

function getRowKey(row) {
  const pk = tablePkField.value;
  return row[pk] ?? JSON.stringify(row);
}

async function selectTable(name) {
  selectedTable.value = name;
  await loadTableRows();
}

async function loadTableRows() {
  if (!selectedTable.value) return;
  try {
    const structRes = await fetchAPI(`/api/admin/tables/${selectedTable.value}/structure`);
    const structure = structRes.data || [];
    tableColumns.value = structure.map((c) => c.field);
    tablePkField.value = structure.find((c) => c.key === 'PRI')?.field || tableColumns.value[0];

    const dataRes = await fetchAPI(`/api/admin/tables/${selectedTable.value}/data?per_page=50`);
    tableRows.value = dataRes.data?.items || [];
  } catch (err) {
    console.error('加载表数据失败:', err);
    tableRows.value = [];
  }
}

function editTableRow(row) {
  const pk = row[tablePkField.value];
  openRecordEditor(`${selectedTable.value} · ${tablePkField.value}=${pk}`, row, {
    readonlyKeys: [tablePkField.value],
    jsonKeys: tableColumns.value.filter((c) => {
      const v = row[c];
      return typeof v === 'object' && v !== null;
    })
  }, async (data) => {
    await fetchAPI(`/api/admin/tables/${selectedTable.value}/data/${pk}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    showToast('保存成功', 'success');
    await loadTableRows();
  });
}

function insertTableRow() {
  if (!selectedTable.value || !tableColumns.value.length) return;
  const empty = {};
  tableColumns.value.forEach((c) => { empty[c] = ''; });
  openRecordEditor(`新建 · ${selectedTable.value}`, empty, {
    readonlyKeys: [tablePkField.value]
  }, async (data) => {
    const body = { ...data };
    delete body[tablePkField.value];
    await fetchAPI(`/api/admin/tables/${selectedTable.value}/data`, {
      method: 'POST',
      body: JSON.stringify(body)
    });
    showToast('创建成功', 'success');
    await loadTableRows();
  });
}

async function deleteTableRow(row) {
  const pk = row[tablePkField.value];
  const confirmed = await showConfirm({
    title: '删除行',
    message: `确定删除 ${selectedTable.value} 中 ${tablePkField.value}=${pk} 的记录？`,
    type: 'danger',
    confirmText: '删除'
  });
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/tables/${selectedTable.value}/data/${pk}`, { method: 'DELETE' });
    showToast('删除成功', 'success');
    await loadTableRows();
  } catch (err) {
    console.error('删除失败:', err);
  }
}

async function deleteCategory(categoryId) {
  const confirmed = await showConfirm({title: '删除分类', message: '确定要删除该分类吗？', type: 'danger', confirmText: '删除'});
  if (!confirmed) return;
  try {
    await fetchAPI(`/api/admin/categories/${categoryId}`, {
      method: 'DELETE'
    });
    showToast('删除成功', 'success');
    await loadCategories();
  } catch (err) {
    console.error('删除分类失败:', err);
  }
}

const showDetailModal = ref(false);
const detailTitle = ref('');
const detailContent = ref('');
const detailType = ref('text');

function showDetail(title, content) {
  detailType.value = 'text';
  detailTitle.value = title;
  detailContent.value = content;
  showDetailModal.value = true;
}

function parseProofImages(proofImages) {
  if (!proofImages) return [];
  try {
    if (typeof proofImages === 'string') {
      const parsed = JSON.parse(proofImages);
      return Array.isArray(parsed) ? parsed : [parsed];
    }
    return Array.isArray(proofImages) ? proofImages : [proofImages];
  } catch (e) {
    return [proofImages];
  }
}

function closeDetailModal() {
  showDetailModal.value = false;
  detailType.value = 'text';
}
</script>

<style scoped>
.admin-panel {
  min-height: 100vh;
  background: #f5f7fa;
}

.admin-container {
  display: flex;
  min-height: calc(100vh - 60px);
}

.sidebar {
  width: 240px;
  background: #2c3e50;
  color: #fff;
  padding: 20px 0;
  position: fixed;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.sidebar-header {
  padding: 0 20px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 20px;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 20px;
  color: #fff;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
  font-size: 14px;
  text-align: left;
  width: 100%;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background: #3498db;
  color: #fff;
}

.nav-icon {
  font-size: 18px;
}

.nav-label {
  font-weight: 500;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  padding: 20px;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.content-panel {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
}

.panel-header h1 {
  margin: 0;
  font-size: 24px;
  color: #2c3e50;
}

.btn-refresh {
  padding: 8px 20px;
  background: #3498db;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-refresh:hover {
  background: #2980b9;
}

.panel-body {
  padding: 32px;
}

.dashboard {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card:nth-child(2) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card:nth-child(3) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card:nth-child(4) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon {
  font-size: 40px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.charts-grid-viz {
  grid-template-columns: repeat(2, 1fr);
}

@media (max-width: 900px) {
  .charts-grid-viz {
    grid-template-columns: 1fr;
  }
  .tables-manager {
    grid-template-columns: 1fr;
  }
}

.chart-card-wide {
  min-height: 280px;
}

.clickable-row {
  cursor: pointer;
}

.audit-center {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.audit-subnav {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.audit-tab {
  padding: 10px 18px;
  border: 1px solid #e0e0e0;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.audit-tab.active {
  background: #3498db;
  color: #fff;
  border-color: #3498db;
}

.audit-tab .badge {
  background: #e74c3c;
  color: #fff;
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.audit-tab.active .badge {
  background: #fff;
  color: #3498db;
}

.empty-row {
  text-align: center;
  color: #999;
  padding: 32px !important;
}

.muted {
  color: #999;
  font-size: 13px;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.done {
  background: #d4edda;
  color: #155724;
}

.tables-manager {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
  min-height: 480px;
}

.table-sidebar {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e8e8e8;
  max-height: 600px;
  overflow-y: auto;
}

.sidebar-title {
  margin: 0 0 12px;
  font-size: 12px;
  color: #888;
  text-transform: uppercase;
}

.table-pick {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  margin-bottom: 4px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #444;
  font-family: Consolas, Monaco, monospace;
}

.table-pick:hover,
.table-pick.active {
  background: #3498db;
  color: #fff;
}

.table-main {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  padding: 16px;
  overflow: hidden;
}

.table-placeholder {
  color: #999;
  padding: 80px 20px;
  text-align: center;
}

.table-name {
  font-weight: 600;
  font-family: Consolas, Monaco, monospace;
  margin-right: 12px;
}

.table-scroll {
  overflow-x: auto;
  margin-top: 12px;
}

.chart-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e8e8e8;
}

.chart-card h3 {
  margin: 0 0 20px;
  font-size: 16px;
  color: #2c3e50;
  font-weight: 600;
}

.chart-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chart-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.chart-label {
  color: #666;
  font-size: 14px;
}

.chart-value {
  font-weight: 600;
  color: #2c3e50;
}

.data-table {
  width: 100%;
  overflow-x: auto;
}

.table-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  max-width: 400px;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}

thead {
  background: #f8f9fa;
}

th {
  padding: 14px 16px;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
  border-bottom: 2px solid #e8e8e8;
}

td {
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: #555;
}

tr:hover {
  background: #f8f9fa;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn-primary,
.btn-action,
.btn-success,
.btn-danger {
  padding: 6px 14px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-primary {
  background: #3498db;
  color: #fff;
}

.btn-primary:hover {
  background: #2980b9;
}

.btn-action {
  background: #95a5a6;
  color: #fff;
}

.btn-action:hover {
  background: #7f8c8d;
}

.btn-success {
  background: #27ae60;
  color: #fff;
}

.btn-success:hover {
  background: #229954;
}

.btn-danger {
  background: #e74c3c;
  color: #fff;
}

.btn-danger:hover {
  background: #c0392b;
}

.btn-link {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  font-size: 14px;
  text-decoration: underline;
}

.btn-link:hover {
  color: #2980b9;
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.normal,
.status-badge.active,
.status-badge.pending,
.status-badge.approved {
  background: #d4edda;
  color: #155724;
}

.status-badge.banned,
.status-badge.rejected,
.status-badge.inactive {
  background: #f8d7da;
  color: #721c24;
}

.type-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.type-badge.lost {
  background: #fff3cd;
  color: #856404;
}

.type-badge.found {
  background: #cce5ff;
  color: #004085;
}

.admin-logout {
  padding: 8px 16px;
  background: #e74c3c;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.admin-logout:hover {
  background: #c0392b;
}

.info-box {
  padding: 20px;
  background: #e8e8e8;
  border: 1px solid #ccc;
  border-radius: 8px;
  margin-bottom: 20px;
}

.info-box p {
  margin: 0;
  color: #333;
}

.hint {
  color: #666;
  font-style: italic;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #2c3e50;
}

.modal-close {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.detail-textarea {
  width: 100%;
  min-height: 200px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  background: #f8f9fa;
}

.detail-modal {
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.detail-item {
  display: flex;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-label {
  font-weight: 500;
  color: #666;
  min-width: 100px;
}

.detail-content {
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.detail-images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.detail-image {
  max-width: 150px;
  max-height: 150px;
  border-radius: 6px;
  border: 1px solid #ddd;
  cursor: pointer;
  transition: transform 0.2s;
}

.detail-image:hover {
  transform: scale(1.05);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-top: 1px solid #eee;
}

.btn-page {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.btn-page:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #ccc;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.priority-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.priority-low {
  background: #f6ffed;
  color: #52c41a;
}

.priority-medium {
  background: #fff7e6;
  color: #fa8c16;
}

.priority-high {
  background: #fff2f0;
  color: #ff4d4f;
}

.status-badge.processing {
  background: #e6f7ff;
  color: #1890ff;
}

.status-badge.closed {
  background: #f5f5f5;
  color: #999;
}

.permissions-panel {
  padding: 0;
}

.permissions-header {
  padding: 20px 32px;
  background: #f8f9fa;
  border-bottom: 1px solid #e8e8e8;
}

.permissions-header h3 {
  margin: 0;
  font-size: 16px;
  color: #2c3e50;
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  padding: 24px 32px;
}

.permission-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s;
}

.permission-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #3498db;
}

.permission-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.permission-key {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.permission-category {
  font-size: 12px;
  padding: 2px 8px;
  background: #e8e8e8;
  border-radius: 12px;
  color: #666;
}

.permission-name {
  font-size: 16px;
  font-weight: 500;
  color: #3498db;
  margin-bottom: 8px;
}

.permission-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}
</style>
