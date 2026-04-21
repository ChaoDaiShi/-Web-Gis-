const userId = localStorage.getItem('user_id');

fetch(`http://127.0.0.1:5002/api/profile?user_id=${userId}`)
    .then(res => res.json())
    .then(res => {
        if (res.success) {
            const u = res.data;

            document.getElementById('username').value = u.username || '';
            document.getElementById('email').value = u.email || '';
            document.getElementById('signature').value = u.signature || '';
            document.getElementById('bio').value = u.bio || '';

            document.querySelector('.avatar').innerHTML =
                `<img src="${u.avatar}" style="width:100%;border-radius:50%">`;
        }
    });

(function () {
    var backProfileBtn = document.getElementById('backProfileBtn');
    var backHomeBtn = document.getElementById('backHomeBtn');
    var changeAvatarBtn = document.getElementById('changeAvatarBtn');
    var sendCodeBtn = document.getElementById('sendCodeBtn');
    var cancelBtn = document.getElementById('cancelBtn');
    var confirmBtn = document.getElementById('confirmBtn');

    backProfileBtn.addEventListener('click', function () {
        window.location.href = './个人中心.html';
    });

    backHomeBtn.addEventListener('click', function () {
        window.location.href = './主页.html';
    });

    document.querySelector('.topbar-user').addEventListener('click', function () {
        window.location.href = './个人中心.html';
    });

    changeAvatarBtn.addEventListener('click', function () {
        const userId = localStorage.getItem('user_id');

        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';

        input.onchange = function () {
            const file = input.files[0];

            if (!file) return;

            const formData = new FormData();
            formData.append('user_id', userId);
            formData.append('avatar', file);

            fetch('http://127.0.0.1:5002/api/profile/avatar', {
                method: 'POST',
                body: formData
            })
                .then(res => res.json())
                .then(res => {
                    if (res.success) {
                        document.querySelector('.avatar').innerHTML =
                            `<img src="${res.avatar}" style="width:100%;border-radius:50%">`;
                    } else {
                        alert('上传失败');
                    }
                });
        };

        input.click();
    });

    var codeCountdown = 0;
    var codeTimer = null;

    sendCodeBtn.addEventListener('click', function () {
        if (codeCountdown > 0) return;

        codeCountdown = 60;
        sendCodeBtn.disabled = true;
        sendCodeBtn.textContent = codeCountdown + '秒后重试';

        codeTimer = setInterval(function () {
            codeCountdown--;
            if (codeCountdown > 0) {
                sendCodeBtn.textContent = codeCountdown + '秒后重试';
            } else {
                clearInterval(codeTimer);
                sendCodeBtn.disabled = false;
                sendCodeBtn.textContent = '获取验证码';
            }
        }, 1000);

        alert('验证码已发送，请查收短信');
    });

    cancelBtn.addEventListener('click', function () {
        if (confirm('确定要取消修改吗？未保存的内容将丢失。')) {
            window.location.href = './个人中心.html';
        }
    });

    confirmBtn.addEventListener('click', function () {
        const userId = localStorage.getItem('user_id');

        const username = document.getElementById('username').value.trim();
        const signature = document.getElementById('signature').value.trim();
        const bio = document.getElementById('bio').value.trim();
        const email = document.getElementById('email').value.trim();

        if (!username) {
            alert('请输入用户名');
            return;
        }

        fetch('http://127.0.0.1:5002/api/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                username: username,
                signature: signature,
                bio: bio
            })
        })
            .then(res => res.json())
            .then(res => {
                if (res.success) {
                    document.getElementById('successMsg').style.display = 'block';

                    setTimeout(() => {
                        window.location.href = './个人中心.html';
                    }, 1500);
                } else {
                    alert(res.message || '修改失败');
                }
            });
    });
})();
