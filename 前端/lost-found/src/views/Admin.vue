<script setup>
import { computed, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";

const router = useRouter();

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
    
    const idFieldMap = {
      lostItems: 'item_id',
      claims: 'claim_id',
      users: 'user_id',
      categories: 'category_id',
      locations: 'location_id'
    };
    
    const idField = idFieldMap[currentTable.value];
    
    tables.value[currentTable.value].rows = data.map((item, index) => {
      const row = {};
      table.value.columns.forEach((col) => {
        const fieldMap = {
          '物品ID': item[idField],
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
          '认领时间': item.create_time,
          '用户ID': item.user_id,
          '用户名': item.username,
          '邮箱': item.email,
          '手机号': item.phone,
          '头像URL': item.avatar_url,
          '个性签名': item.signature,
          '个人简介': item.bio,
          '创建时间': item.create_time,
          '分类ID': item.category_id,
          '分类名称': item.name,
          '位置ID': item.location_id,
          '位置名称': item.name,
          '纬度': item.latitude,
          '经度': item.longitude,
          '详细地址': item.detail
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
  lostItems: '物品ID',
  claims: '认领ID',
  users: '用户ID',
  categories: '分类ID',
  locations: '位置ID'
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
              <td v-for="col in table.columns" :key="col">{{ row[col] ?? "" }}</td>
              <td class="ops">
                <button @click="editRow(i)">编辑</button>
                <button class="delete-btn" @click="delRow(i)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="status">{{ status }}</p>
    </main>
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
</style>