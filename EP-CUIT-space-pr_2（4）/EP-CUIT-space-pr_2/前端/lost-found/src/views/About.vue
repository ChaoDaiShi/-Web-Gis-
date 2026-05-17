<script setup>
import AppTopBar from "../components/AppTopBar.vue";

function goBack() {
  if (window.history.length > 1) {
    window.history.back();
  } else {
    window.location.href = "/home";
  }
}

function goProfile() {
  window.location.href = "/profile";
}
</script>

<template>
  <div class="about-page">
    <AppTopBar variant="inner" />

    <div class="container">
      <div class="scroll-container">
        <div class="content-card">
        <h1 class="page-title">关于我们</h1>
        <div class="section">
          <h2 class="section-title">平台简介</h2>
          <p class="section-content">
            校园GIS失物招领平台，是由本校学生自主研发、专为全校师生打造的校园专属失物寻回服务平台。我们立足校园日常需求，依托GIS地理信息技术，打破传统失物招领信息零散、查找低效、定位模糊的难题，搭建起便捷、精准、高效的线上失物招领桥梁，全力解决师生校园物品遗失、捡拾归还难题，让失物寻回更简单，让校园温情更浓厚。
          </p>
          <p class="section-content" style="margin-top: 15px">
            我们始终扎根校园、服务师生，以技术为支撑，以服务为核心，摒弃复杂繁琐的操作流程，打造轻量化、精准化、本土化的校园失物招领工具，让每一件遗失物品都能快速找到归属，让每一次善意归还都能高效传递。
          </p>
        </div>

        <div class="section">
          <h2 class="section-title">团队初心</h2>
          <p class="section-content">
            本平台由本校专注于GIS技术应用、校园服务优化的学生团队倾力打造。团队成员怀揣着服务校园、学以致用的初心，结合专业所学的地理信息系统技术，针对校园内物品遗失后寻回难、招领信息分散、线下公告栏信息更新不及时等痛点，历经调研、研发、测试与优化，最终搭建起这套贴合校园场景的失物招领系统。
          </p>
          <p class="section-content" style="margin-top: 15px">
            我们始终秉持公益服务、便捷高效、精准对接的理念，不追求商业利益，只为用专业技术解决师生身边的小麻烦，用用心服务温暖校园生活，打造属于师生自己的贴心失物招领平台。
          </p>
        </div>

        <div class="section">
          <h2 class="section-title">平台特色</h2>
          <ul class="feature-list">
            <li>
              <div class="feature-title">1. GIS精准定位，寻回更高效</div>
              <p class="feature-desc">依托GIS地理信息技术，支持遗失/捡拾物品位置精准标注、校园地图可视化展示，快速定位物品遗失与发现范围，大幅缩小查找范围，提升失物配对与寻回效率。</p>
            </li>
            <li>
              <div class="feature-title">2. 信息真实透明，服务更安心</div>
              <p class="feature-desc">严格聚焦校园场景，仅限本校师生使用，所有招领信息经规范发布，信息真实可查，杜绝虚假信息，保障师生物品与信息安全。</p>
            </li>
            <li>
              <div class="feature-title">3. 一站式便捷操作，使用更简单</div>
              <p class="feature-desc">极简操作流程，支持遗失物品发布、捡拾物品上传、信息筛选查询、在线沟通对接等全流程服务，无需复杂操作，轻松发布与查找信息。</p>
            </li>
            <li>
              <div class="feature-title">4. 专属校园服务，适配性更强</div>
              <p class="feature-desc">深度贴合校园生活场景，覆盖校园各区域、各类日常物品招领需求，针对性解决校园内失物招领的各类问题，更懂师生需求。</p>
            </li>
          </ul>
        </div>

        <div class="section">
          <h2 class="section-title">服务宗旨</h2>
          <p class="section-content">以GIS技术为纽带，以校园服务为使命，我们致力于搭建安全、高效、便捷、暖心的校园失物招领生态，让遗失不再遗憾，让归还更有温度。</p>
          <p class="section-content" style="margin-top: 15px">未来，我们将持续优化平台功能、完善服务体验，倾听师生的每一条建议，不断提升平台实用性与便捷性，全力守护校园物品安全，传递校园互助正能量，成为全校师生值得信赖的校园服务伙伴。</p>
        </div>

        <div class="section">
          <h2 class="section-title">联系我们</h2>
          <div class="contact-info">
            <p>如果您对平台有任何建议、意见，或是需要平台协助，欢迎随时与我们联系，我们将竭诚为您服务，与您一同打造更美好的校园生活。</p>
          </div>
        </div>

        <button class="back-btn" @click="goBack">返回</button>
      </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/关于我们.css"></style>
