<script setup>
import { computed, ref } from "vue";

const db = ref({
  lostItems: {
    label: "失物信息表",
    columns: ["物品ID", "物品标题", "详细描述", "类型", "当前状态", "发布者ID"],
    rows: [
      { 物品ID: "L001", 物品标题: "黑色书包", 详细描述: "教学楼A302拾到", 类型: "包类", 当前状态: "待认领", 发布者ID: "U1001" },
      { 物品ID: "L002", 物品标题: "校园卡", 详细描述: "食堂二楼窗口附近", 类型: "证件", 当前状态: "待认领", 发布者ID: "U1020" },
    ],
  },
  claimRecords: {
    label: "认领记录表",
    columns: ["记录ID", "物品ID", "认领人ID", "认领时间", "审核状态"],
    rows: [{ 记录ID: "C001", 物品ID: "L003", 认领人ID: "U1099", 认领时间: "2026-04-01 14:20", 审核状态: "通过" }],
  },
  users: {
    label: "用户表",
    columns: ["用户ID", "用户名", "手机号", "角色", "状态"],
    rows: [{ 用户ID: "U1001", 用户名: "张三", 手机号: "13800001111", 角色: "学生", 状态: "正常" }],
  },
});

const currentTable = ref("lostItems");
const keyword = ref("");
const status = ref("已加载后台表格。");

const table = computed(() => db.value[currentTable.value]);
const filteredRows = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  if (!key) return table.value.rows;
  return table.value.rows.filter((row) => table.value.columns.some((col) => String(row[col] || "").toLowerCase().includes(key)));
});

function askRowData(columns, initial = {}) {
  const next = {};
  for (const col of columns) {
    const val = window.prompt(`请输入 ${col}`, initial[col] ?? "");
    if (val === null) return null;
    next[col] = val.trim();
  }
  return next;
}

function editRow(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  const next = askRowData(table.value.columns, row);
  if (!next) return;
  table.value.rows[rawIndex] = next;
  status.value = "修改成功。";
}

function delRow(index) {
  const row = filteredRows.value[index];
  const rawIndex = table.value.rows.indexOf(row);
  if (!confirm("确认删除该条记录吗？")) return;
  table.value.rows.splice(rawIndex, 1);
  status.value = "删除成功。";
}

function addRow() {
  const next = askRowData(table.value.columns);
  if (!next) return;
  table.value.rows.push(next);
  status.value = "新增成功。";
}
</script>

<template>
  <div>
    <header class="topbar">
      <h1 class="topbar-title">校园失物招领与位置追踪系统</h1>
      <div class="topbar-user">管</div>
    </header>

    <main class="container">
      <div class="toolbar">
        <input v-model="keyword" type="text" placeholder="检索：输入关键词（支持所有字段）" />
        <select v-model="currentTable">
          <option v-for="(v, k) in db" :key="k" :value="k">{{ v.label }}</option>
        </select>
        <button type="button" @click="keyword = ''">清空检索</button>
        <button type="button" @click="addRow">追加空白新增行</button>
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
