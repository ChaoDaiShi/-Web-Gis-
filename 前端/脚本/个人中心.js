function formatStatus(status) {
    const map = {
        0: '待认领',
        1: '已认领',
        2: '已关闭'
    };
    return map[status] || '未知';
}

function loadPublish() {
    const userId = localStorage.getItem('user_id');

    fetch(`http://127.0.0.1:5002/api/my/publish?user_id=${userId}`)
        .then(res => res.json())
        .then(res => {
            if (!res.success) return;

            const tbody = document.querySelector('#publish-panel tbody');
            tbody.innerHTML = '';

            res.data.forEach(item => {
                const tr = `
                <tr>
                    <td>${item.title}</td>
                    <td>${item.create_time}</td>
                    <td>${formatStatus(item.status)}</td>
                    <td><a href="#">查看</a></td>
                </tr>
            `;
                tbody.innerHTML += tr;
            });
        });
}

function loadClaim() {
    const userId = localStorage.getItem('user_id');

    fetch(`http://127.0.0.1:5002/api/my/claim?user_id=${userId}`)
        .then(res => res.json())
        .then(res => {
            if (!res.success) return;

            const tbody = document.querySelector('#claim-panel tbody');
            tbody.innerHTML = '';

            res.data.forEach(item => {
                const tr = `
                <tr>
                    <td>${item.title}</td>
                    <td>${item.create_time}</td>
                    <td>${formatStatus(item.status)}</td>
                    <td><a href="#">查看</a></td>
                </tr>
            `;
                tbody.innerHTML += tr;
            });
        });
}

(function() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const panels = document.querySelectorAll('.panel');
    const panelTabs = document.querySelectorAll('.panel-tab');

    navButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const panel = this.dataset.panel;
            const action = this.dataset.action;

            if (action) {
                handleAction(action);
                return;
            }

            if (panel) {
                navButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                panels.forEach(p => p.classList.add('hidden'));
                document.getElementById(panel + '-panel').classList.remove('hidden');
            }

            if (panel === 'publish') {
                loadPublish();
            }

            if (panel === 'claim') {
                loadClaim();
            }
        });
    });

    panelTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const parent = this.closest('.panel-header');
            parent.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });

    function handleAction(action) {
        switch(action) {
            case 'home':
                window.location.href = './主页.html';
                break;
            case 'bind':
                window.location.href = './账号安全.html#bind';
                break;
            case 'password':
                window.location.href = './账号安全.html#password';
                break;
            case 'logout':
                if(confirm('确定要退出登录吗？')) {
                    window.location.href = './登录界面.html';
                }
                break;
        }
    }

    document.querySelectorAll('.sidebar-footer a').forEach(link => {
        link.addEventListener('click', function() {
            const action = this.dataset.action;
            if (action) {
                handleAction(action);
            }
        });
    });

    document.querySelector('.topbar-user').addEventListener('click', function() {
        alert('用户中心功能开发中...');
    });
})();

const userId = localStorage.getItem('user_id');

fetch(`http://127.0.0.1:5002/api/profile?user_id=${userId}`)
    .then(res => res.json())
    .then(res => {
        if (res.success) {
            const user = res.data;

            document.querySelector('.username').innerText = user.username;
            document.querySelector('.user-id').innerText = 'ID: ' + user.user_id;

            document.querySelector('.info-value').innerText = user.email;

            document.querySelector('.description-area textarea').value = user.bio;
        }
    });
