function goBack() {
    if (document.referrer) {
        window.history.back();
    } else {
        window.location.href = './主页.html';
    }
}

document.querySelector('.topbar-user').addEventListener('click', function() {
    window.location.href = './个人中心.html';
});
