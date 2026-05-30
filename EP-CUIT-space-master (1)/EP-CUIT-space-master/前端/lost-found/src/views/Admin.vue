<!-- 管理员页面 -->
<script setup>
import { computed, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";
import MarkerDetailModal from "../components/MarkerDetailModal.vue";

const router = useRouter();
const showToast = window.showToast;

const showDetailModal = ref(false);
const detailTitle = ref('');
const detailContent = ref('');

function showDetail(title, content) {
  detailTitle.value = title;
  detailContent.value = content;
  showDetailModal.value = true;
}

function closeDetailModal() {
  showDetailModal.value = false;
}

const showMarkerDetailModal = ref(false);
const selectedMarker = ref(null);

const showImageModal = ref(false);
const previewImages = ref([]);
const currentImageIndex = ref(0);



function showImage(proofImages) {
  try {
    let images = [];
    if (typeof proofImages === 'string') {
      if (proofImages.startsWith('data:image/')) {
        images = [proofImages];
      } else {
        try {
          images = JSON.parse(proofImages);
        } catch {
          images = [];
        }
      }
    } else if (Array.isArray(proofImages)) {
      images = proofImages;
    }
    previewImages.value = images.map(img => {
      if (img.startsWith('data:image/')) {
        return img;
      }
      if (img.startsWith('http://') || img.startsWith('https://')) {
        return img;
      }
      if (img.startsWith('/')) {
        return `http://127.0.0.1:5000${img}`;
      }
      return `http://127.0.0.1:5000/${img}`;
    }).filter(img => img);
    currentImageIndex.value = 0;
    showImageModal.value = true;
  } catch (e) {
    console.error('解析图片数据失败:', e);
    showToast('无法解析图片数据', 'error');
  }
}

function closeImageModal() {
  showImageModal.value = false;
  previewImages.value = [];
  currentImageIndex.value = 0;
}

function prevImage() {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--;
  }
}

function nextImage() {
  if (currentImageIndex.value < previewImages.value.length - 1) {
    currentImageIndex.value++;
  }
}

async function viewClaimDetail(index) {
  const row = filteredRows.value[index];
  const itemId = row['物品ID'];
  
  if (!itemId) {
    showToast('无法获取物品ID', 'error');
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/lost-items/${itemId}`);
    const data = await res.json();
    
    if (data.success) {
      const item = data.data;
      selectedMarker.value = {
        id: item.item_id,
        title: item.title,
        detail: item.description || '',
        status: item.status,
        time: item.create_time,
        images: item.image_urls || [],
        type: item.type,
        publisher_id: item.publisher_id,
        lng: item.longitude,
        lat: item.latitude
      };
      showMarkerDetailModal.value = true;
    } else {
      showToast('获取物品详情失败', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('获取物品详情失败，请检查网络连接', 'error');
  }
}

async function viewReturnDetail(index) {
  const row = filteredRows.value[index];
  const itemId = row['物品ID'];
  
  if (!itemId) {
    showToast('无法获取物品ID', 'error');
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/lost-items/${itemId}`);
    const data = await res.json();
    
    if (data.success) {
      const item = data.data;
      selectedMarker.value = {
        id: item.item_id,
        title: item.title,
        detail: item.description || '',
        status: item.status,
        time: item.create_time,
        images: item.image_urls || [],
        type: item.type,
        publisher_id: item.publisher_id,
        lng: item.longitude,
        lat: item.latitude
      };
      showMarkerDetailModal.value = true;
    } else {
      showToast('获取物品详情失败', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('获取物品详情失败，请检查网络连接', 'error');
  }
}

function closeMarkerDetailModal() {
  showMarkerDetailModal.value = false;
  selectedMarker.value = null;
}

const tables = ref({
  lostItems: {
    label: "失物/招领信息表",
    columns: ["物品ID", "物品标题", "物品描述", "类型", "分类ID", "状态", "发布者ID", "位置ID", "发布时间", "更新时间"],
    rows: [],
    api: "lost_items"
  },
  claims: {
    label: "认领记录表",
    columns: ["认领ID", "物品ID", "认领人ID", "认领留言", "状态", "认领时间"],
    rows: [],
    api: "claims"
  },
  claimForms: {
    label: "认领表单审核表",
    columns: ["认领ID", "物品ID", "认领人姓名", "联系方式", "物品图片", "认领理由", "物品描述", "状态", "提交时间"],
    rows: [],
    api: "claim-forms"
  },
  returnForms: {
    label: "归还表单审核表",
    columns: ["归还ID", "物品ID", "归还人姓名", "联系方式", "物品图片", "归还理由", "物品描述", "状态", "提交时间"],
    rows: [],
    api: "return-forms"
  },
  userVerification: {
    label: "信息认证审核表",
    columns: ["认证ID", "用户ID", "身份类型", "真实姓名", "学号/工号", "学校/单位", "联系方式", "证件正面", "证件反面", "状态", "提交时间"],
    rows: [],
    api: "user-verify"
  },
  users: {
    label: "用户信息表",
    columns: ["用户ID", "用户名", "邮箱", "手机号", "头像URL", "个性签名", "个人简介", "创建时间"],
    rows: [],
    api: "users"
  },
  categories: {
    label: "物品分类表",
    columns: ["分类ID", "分类名称"],
    rows: [],
    api: "categories"
  },
  locations: {
    label: "地理位置表",
    columns: ["位置ID", "位置名称", "纬度", "经度", "详细地址"],
    rows: [],
    api: "locations"
  }
});

const currentTable = ref("lostItems");
const keyword = ref("");
const status = ref("已加载后台表格。");

const table = computed(() => tables.value[currentTable.value]);
const filteredRows = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  if (!key) return table.value.rows;
  return table.value.rows.filter((row) => 
    table.value.columns.some((col) => String(row[col] || "").toLowerCase().includes(key))
  );
});

async function loadTableData() {
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/admin/${table.value.api}`);
    const data = await res.json();
    
    tables.value[currentTable.value].rows = data.map((item) => {
      const row = {};
      table.value.columns.forEach((col) => {
        const fieldMap = {
          '物品ID': item.item_id,
          '物品标题': item.title,
          '物品描述': item.description,
          '类型': item.type,
          '分类ID': item.category_id,
          '状态': item.status,
          '发布者ID': item.publisher_id,
          '位置ID': item.location_id,
          '发布时间': item.create_time,
          '更新时间': item.update_time,
          '认领ID': item.claim_id,
          '认领人ID': item.claimer_id,
          '认领留言': item.message,
          '认领时间': item.create_time || item.claim_time,
          '用户ID': item.user_id,
          '用户名': item.username,
          '邮箱': item.email,
          '手机号': item.phone,
          '头像URL': item.avatar_url,
          '个性签名': item.signature,
          '个人简介': item.bio,
          '创建时间': item.created_at || item.create_time,
          '分类名称': item.name,
          '位置名称': item.location_name,
          '纬度': item.latitude,
          '经度': item.longitude,
          '详细地址': item.detail,
          '认领人姓名': item.applicant_name,
          '联系方式': item.applicant_phone,
          '物品图片': item.proof_images,
          '认领理由': item.claim_reason,
          '物品描述': item.item_description,
          '提交时间': item.submit_time || item.create_time,
          '归还ID': item.return_id,
          '归还人姓名': item.applicant_name,
          '归还理由': item.return_reason,
          '物品描述': item.item_description,
          '认证ID': item.verify_id,
          '身份类型': item.identity,
          '真实姓名': item.real_name,
          '学号/工号': item.student_id,
          '联系方式': item.phone || item.email,
          '证件正面': item.id_card_front,
          '证件反面': item.id_card_back
        };
        row[col] = fieldMap[col] ?? "";
      });
      return row;
    });
    
    status.value = `已加载 ${table.value.rows.length} 条记录`;
  } catch (err) {
    console.error(err);
    status.value = "加载数据失败";
  }
}

function askRowData(columns, initial = {}) {
  const next = {};
  for (const col of columns) {
    const val = window.prompt(`请输入 ${col}`, String(initial[col] ?? ""));
    if (val === null) return null;
    next[col] = val.trim();
  }
  return next;
}

const idFieldMap = {
  lostItems: 'item_id',
  claims: 'claim_id',
  users: 'user_id',
  categories: 'category_id',
  locations: 'location_id',
  claimForms: 'claim_id',
  returnForms: 'return_id',
  userVerification: 'verify_id'
};

const fieldToApiMap = {
  '物品ID': 'item_id',
  '物品标题': 'title',
  '物品描述': 'description',
  '类型': 'type',
  '分类ID': 'category_id',
  '状态': 'status',
  '发布者ID': 'publisher_id',
  '位置ID': 'location_id',
  '发布时间': 'create_time',
  '更新时间': 'update_time',
  '认领ID': 'claim_id',
  '认领人ID': 'claimer_id',
  '认领留言': 'message',
  '认领时间': 'create_time',
  '用户ID': 'user_id',
  '用户名': 'username',
  '邮箱': 'email',
  '手机号': 'phone',
  '头像URL': 'avatar_url',
  '个性签名': 'signature',
  '个人简介': 'bio',
  '创建时间': 'create_time',
  '分类名称': 'name',
  '位置名称': 'name',
  '纬度': 'latitude',
  '经度': 'longitude',
  '详细地址': 'detail'
};

async function editRow(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const next = askRowData(table.value.columns, row);
  if (!next) return;
  
  try {
    const idField = idFieldMap[currentTable.value];
    const id = row[idField];
    
    const apiData = {};
    table.value.columns.forEach(col => {
      if (col !== idField && next[col] !== undefined) {
        apiData[fieldToApiMap[col]] = next[col];
      }
    });
    
    const res = await fetch(`http://127.0.0.1:5000/api/admin/${table.value.api}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(apiData)
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows[rawIndex] = next;
      status.value = "修改成功。";
    } else {
      status.value = `修改失败: ${data.message}`;
    }
  } catch (err) {
    console.error(err);
    status.value = "修改失败";
  }
}

async function approveClaim(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const claimId = row['认领ID'];
  
  if (!confirm('确定要通过该认领申请吗？')) {
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/admin/claim-forms/${claimId}/approve`, {
      method: 'POST'
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows[rawIndex]['状态'] = '已通过';
      showToast('通过成功', 'success');
    } else {
      showToast(`通过失败: ${data.message}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('通过失败，请检查网络连接', 'error');
  }
}

async function rejectClaim(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const claimId = row['认领ID'];
  
  if (!confirm('确定要拒绝该认领申请吗？此操作将删除该认领记录。')) {
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/admin/claim-forms/${claimId}/reject`, {
      method: 'POST'
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows.splice(rawIndex, 1);
      showToast('拒绝成功', 'success');
    } else {
      showToast(`拒绝失败: ${data.message}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('拒绝失败，请检查网络连接', 'error');
  }
}

async function approveReturn(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const returnId = row['归还ID'];
  
  if (!confirm('确定要通过该归还申请吗？')) {
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/admin/return-forms/${returnId}/approve`, {
      method: 'POST'
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows[rawIndex]['状态'] = '已通过';
      showToast('通过成功', 'success');
    } else {
      showToast(`通过失败: ${data.message}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('通过失败，请检查网络连接', 'error');
  }
}

async function rejectReturn(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const returnId = row['归还ID'];
  
  if (!confirm('确定要拒绝该归还申请吗？此操作将删除该归还记录。')) {
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/admin/return-forms/${returnId}/reject`, {
      method: 'POST'
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows.splice(rawIndex, 1);
      showToast('拒绝成功', 'success');
    } else {
      showToast(`拒绝失败: ${data.message}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('拒绝失败，请检查网络连接', 'error');
  }
}

async function approveUserVerify(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const verifyId = row['认证ID'];
  
  if (!confirm('确定要通过该认证申请吗？')) {
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/admin/user-verify/${verifyId}/approve`, {
      method: 'POST'
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows[rawIndex]['状态'] = '已通过';
      showToast('通过成功', 'success');
    } else {
      showToast(`通过失败: ${data.message}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('通过失败，请检查网络连接', 'error');
  }
}

async function rejectUserVerify(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const verifyId = row['认证ID'];
  
  if (!confirm('确定要拒绝该认证申请吗？此操作将删除该认证记录。')) {
    return;
  }
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/admin/user-verify/${verifyId}/reject`, {
      method: 'POST'
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows.splice(rawIndex, 1);
      showToast('拒绝成功', 'success');
    } else {
      showToast(`拒绝失败: ${data.message}`, 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('拒绝失败，请检查网络连接', 'error');
  }
}

async function delRow(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  
  try {
    const idField = idFieldMap[currentTable.value];
    const id = row[idField];
    
    const res = await fetch(`http://127.0.0.1:5000/api/admin/${table.value.api}/${id}`, {
      method: 'DELETE'
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows.splice(rawIndex, 1);
      showToast('删除成功', 'success');
    } else {
      showToast(`删除失败: ${data.message}`, 'error');
    }
  } catch (err) {
    console.error(err);
    status.value = "删除失败";
  }
}

async function addRow() {
  const next = askRowData(table.value.columns);
  if (!next) return;
  
  try {
    const apiData = {};
    table.value.columns.forEach(col => {
      if (col !== idFieldMap[currentTable.value] && next[col] !== undefined) {
        apiData[fieldToApiMap[col]] = next[col];
      }
    });
    
    const res = await fetch(`http://127.0.0.1:5000/api/admin/${table.value.api}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(apiData)
    });
    
    const data = await res.json();
    if (data.success) {
      table.value.rows.push(next);
      status.value = "新增成功。";
    } else {
      status.value = `新增失败: ${data.message}`;
    }
  } catch (err) {
    console.error(err);
    status.value = "新增失败";
  }
}

function logoutAdmin() {
  localStorage.removeItem("is_admin");
  router.push("/login");
}

function switchTable(tableName) {
  currentTable.value = tableName;
  loadTableData();
}

onMounted(() => {
  loadTableData();
});
</script>

<template>
  <div>
    <AppTopBar variant="admin">
      <template #actions>
        <button type="button" class="admin-logout" @click="logoutAdmin">退出后台</button>
      </template>
    </AppTopBar>

    <main class="container">
      <div class="toolbar">
        <input v-model="keyword" type="text" placeholder="检索：输入关键词（支持所有字段）" />
        <select v-model="currentTable" @change="switchTable(currentTable)">
          <option v-for="(v, k) in tables" :key="k" :value="k">{{ v.label }}</option>
        </select>
        <button type="button" @click="keyword = ''">清空检索</button>
        <button type="button" @click="addRow">追加空白新增行</button>
        <button type="button" @click="loadTableData">刷新数据</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th v-for="col in table.columns" :key="col">{{ col }}</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in filteredRows" :key="i" class="clickable-row">
              <td v-for="col in table.columns" :key="col">
                <template v-if="col === '认领理由' && row[col]">
                  <span class="view-link" @click="showDetail('认领理由', row[col])">点击查看</span>
                </template>
                <template v-else-if="col === '归还理由' && row[col]">
                  <span class="view-link" @click="showDetail('归还理由', row[col])">点击查看</span>
                </template>
                <template v-else-if="col === '物品描述' && row[col]">
                  <span class="view-link" @click="showDetail('物品描述', row[col])">点击查看</span>
                </template>
                <template v-else-if="col === '物品图片'">
                  <template v-if="row[col] && row[col] !== '' && row[col] !== '[]'">
                    <span class="view-link" @click="showImage(row[col])">查看图片</span>
                  </template>
                  <template v-else>
                    <span style="color: #999; font-size: 12px;">无图片</span>
                  </template>
                </template>
                <template v-else-if="col === '证件正面'">
                  <template v-if="row[col] && row[col] !== ''">
                    <span class="view-link" @click="showImage(row[col])">点击查看</span>
                  </template>
                  <template v-else>
                    <span style="color: #999; font-size: 12px;">未上传</span>
                  </template>
                </template>
                <template v-else-if="col === '证件反面'">
                  <template v-if="row[col] && row[col] !== ''">
                    <span class="view-link" @click="showImage(row[col])">点击查看</span>
                  </template>
                  <template v-else>
                    <span style="color: #999; font-size: 12px;">未上传</span>
                  </template>
                </template>
                <template v-else>
                  {{ row[col] ?? "" }}
                </template>
              </td>
              <td class="ops">
                <template v-if="currentTable === 'claimForms'">
                  <button class="btn-view" @click="viewClaimDetail(i)">查看</button>
                  <button class="btn-approve" @click="approveClaim(i)">通过</button>
                  <button class="btn-reject" @click="rejectClaim(i)">拒绝</button>
                </template>
                <template v-else-if="currentTable === 'returnForms'">
                  <button class="btn-view" @click="viewReturnDetail(i)">查看</button>
                  <button class="btn-approve" @click="approveReturn(i)">通过</button>
                  <button class="btn-reject" @click="rejectReturn(i)">拒绝</button>
                </template>
                <template v-else-if="currentTable === 'userVerification'">
                  <button class="btn-approve" @click="approveUserVerify(i)">通过</button>
                  <button class="btn-reject" @click="rejectUserVerify(i)">拒绝</button>
                </template>
                <template v-else>
                  <button @click="editRow(i)">编辑</button>
                  <button class="delete-btn" @click="delRow(i)">删除</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="status">{{ status }}</p>
    </main>
  </div>
  
  <MarkerDetailModal
    :show="showMarkerDetailModal"
    :marker="selectedMarker"
    :show-action-buttons="false"
    @close="closeMarkerDetailModal"
  />
  
  <div v-if="showDetailModal" class="detail-modal-overlay" @click="closeDetailModal">
    <div class="detail-modal" @click.stop>
      <div class="detail-modal-header">
        <h3>{{ detailTitle }}</h3>
        <button class="close-btn" @click="closeDetailModal">&times;</button>
      </div>
      <div class="detail-modal-body">
        <textarea readonly class="detail-textarea" :value="detailContent"></textarea>
      </div>
    </div>
  </div>
  
  <div v-if="showImageModal" class="image-modal-overlay" @click="closeImageModal">
    <div class="image-modal" @click.stop>
      <div class="image-modal-header">
        <h3>图片预览</h3>
        <button class="close-btn" @click="closeImageModal">&times;</button>
      </div>
      <div class="image-modal-body">
        <div v-if="previewImages.length > 0" class="image-preview">
          <button class="nav-btn prev-btn" @click="prevImage" :disabled="currentImageIndex === 0">‹</button>
          <img :src="previewImages[currentImageIndex]" :alt="`图片 ${currentImageIndex + 1}`" />
          <button class="nav-btn next-btn" @click="nextImage" :disabled="currentImageIndex === previewImages.length - 1">›</button>
          <div class="image-indicator">{{ currentImageIndex + 1 }} / {{ previewImages.length }}</div>
        </div>
        <div v-else class="no-image">
          暂无图片
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/后台面板.css"></style>

<style scoped>
.admin-logout {
  width: auto;
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  background: #111827;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.admin-logout:hover {
  opacity: 0.92;
}

.view-link {
  color: #3b82f6;
  cursor: pointer;
  text-decoration: underline;
}

.view-link:hover {
  color: #2563eb;
}

.detail-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.detail-modal {
  background: #fff;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.detail-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.detail-modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #374151;
}

.detail-modal-body {
  padding: 20px;
}

.detail-textarea {
  width: 100%;
  height: 200px;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  background: #f9fafb;
}

.ops .btn-view,
.ops .btn-approve,
.ops .btn-reject {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  writing-mode: horizontal-tb;
  text-orientation: mixed;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
}

.ops .btn-view {
  background: #3b82f6;
  color: #fff;
}

.ops .btn-view:hover {
  background: #2563eb;
}

.ops .btn-approve {
  background: #22c55e;
  color: #fff;
}

.ops .btn-approve:hover {
  background: #16a34a;
}

.ops .btn-reject {
  background: #ef4444;
  color: #fff;
}

.ops .btn-reject:hover {
  background: #dc2626;
}

.item-detail-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.item-detail-modal {
  background: #fff;
  border-radius: 8px;
  width: 450px;
  max-width: 90%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.item-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: #fff;
  border-radius: 8px 8px 0 0;
}

.item-detail-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.item-detail-header .close-btn {
  color: #fff;
}

.item-detail-header .close-btn:hover {
  color: rgba(255, 255, 255, 0.8);
}

.item-detail-body {
  padding: 20px;
}

.item-detail-section {
  margin-bottom: 16px;
}

.item-detail-section:last-child {
  margin-bottom: 0;
}

.item-detail-section .label {
  font-weight: 600;
  color: #374151;
}

.status-lost {
  color: #ef4444;
  font-weight: 600;
}

.status-found {
  color: #22c55e;
  font-weight: 600;
}

.location-section {
  background: #f3f4f6;
  padding: 12px;
  border-radius: 6px;
}

.location-info {
  display: flex;
  gap: 20px;
  margin-top: 8px;
}

.publisher-info {
  margin-top: 8px;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 6px;
}

.item-detail-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  text-align: right;
}

.item-detail-footer .close-btn {
  background: #3b82f6;
  color: #fff;
  font-size: 14px;
  padding: 8px 20px;
  border-radius: 4px;
}

.item-detail-footer .close-btn:hover {
  background: #2563eb;
}

.image-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.image-modal {
  background: #fff;
  border-radius: 8px;
  width: 800px;
  max-width: 90%;
  max-height: 80vh;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}

.image-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: #fff;
  border-radius: 8px 8px 0 0;
}

.image-modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.image-modal-header .close-btn {
  color: #fff;
}

.image-modal-body {
  padding: 20px;
}

.image-preview {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview img {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border-radius: 8px;
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.nav-btn:hover:not(:disabled) {
  background: #fff;
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.prev-btn {
  left: 10px;
}

.next-btn {
  right: 10px;
}

.image-indicator {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
}

.no-image {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
  font-size: 14px;
}
</style>