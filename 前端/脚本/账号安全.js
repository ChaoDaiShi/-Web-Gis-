(function () {
    var tabBind = document.getElementById('tabBind');
    var tabPassword = document.getElementById('tabPassword');
    var panelBind = document.getElementById('panelBind');
    var panelPassword = document.getElementById('panelPassword');
    var backProfileBtn = document.getElementById('backProfileBtn');
    var backHomeBtn = document.getElementById('backHomeBtn');
    var sendSmsBtn = document.getElementById('sendSmsBtn');
    var bindSubmitBtn = document.getElementById('bindSubmitBtn');
    var pwdSubmitBtn = document.getElementById('pwdSubmitBtn');

    function switchTab(target) {
        var isBind = target === 'bind';
        tabBind.classList.toggle('active', isBind);
        tabPassword.classList.toggle('active', !isBind);
        panelBind.classList.toggle('active', isBind);
        panelPassword.classList.toggle('active', !isBind);
        window.location.hash = isBind ? 'bind' : 'password';
    }

    tabBind.addEventListener('click', function () {
        switchTab('bind');
    });

    tabPassword.addEventListener('click', function () {
        switchTab('password');
    });

    backProfileBtn.addEventListener('click', function () {
        window.location.href = './个人中心.html';
    });

    backHomeBtn.addEventListener('click', function () {
        window.location.href = './主页.html';
    });

    document.querySelector('.topbar-user').addEventListener('click', function () {
        window.location.href = './个人中心.html';
    });

    var initial = (window.location.hash || '').replace('#', '');
    switchTab(initial === 'password' ? 'password' : 'bind');

    var smsCountdown = 0;
    var smsTimer = null;

    sendSmsBtn.addEventListener('click', function () {
        var phone = document.getElementById('phoneInput').value;
        if (!phone || phone.length !== 11) {
            alert('请输入正确的手机号');
            return;
        }

        if (smsCountdown > 0) return;

        smsCountdown = 60;
        sendSmsBtn.disabled = true;
        sendSmsBtn.textContent = smsCountdown + '秒后重试';

        smsTimer = setInterval(function () {
            smsCountdown--;
            if (smsCountdown > 0) {
                sendSmsBtn.textContent = smsCountdown + '秒后重试';
            } else {
                clearInterval(smsTimer);
                sendSmsBtn.disabled = false;
                sendSmsBtn.textContent = '获取验证码';
            }
        }, 1000);

        alert('验证码已发送，请查收短信');
    });

    bindSubmitBtn.addEventListener('click', function () {
        var phone = document.getElementById('phoneInput').value;
        var sms = document.getElementById('smsInput').value;

        if (!phone || phone.length !== 11) {
            alert('请输入正确的手机号');
            return;
        }

        if (!sms || sms.length !== 6) {
            alert('请输入6位验证码');
            return;
        }

        document.getElementById('bindSuccess').style.display = 'block';
        document.getElementById('bindError').style.display = 'none';

        setTimeout(function () {
            document.getElementById('bindSuccess').style.display = 'none';
        }, 3000);
    });

    pwdSubmitBtn.addEventListener('click', function () {
        var oldPwd = document.getElementById('oldPwd').value;
        var newPwd = document.getElementById('newPwd').value;
        var confirmPwd = document.getElementById('confirmPwd').value;

        if (!oldPwd) {
            alert('请输入当前密码');
            return;
        }

        if (!newPwd || newPwd.length < 8) {
            alert('新密码至少8位');
            return;
        }

        if (newPwd !== confirmPwd) {
            alert('两次输入的密码不一致');
            return;
        }

        document.getElementById('pwdSuccess').style.display = 'block';
        document.getElementById('pwdError').style.display = 'none';

        setTimeout(function () {
            document.getElementById('pwdSuccess').style.display = 'none';
            document.getElementById('oldPwd').value = '';
            document.getElementById('newPwd').value = '';
            document.getElementById('confirmPwd').value = '';
        }, 3000);
    });
})();
