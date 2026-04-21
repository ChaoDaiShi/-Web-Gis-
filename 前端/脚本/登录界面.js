document.addEventListener("DOMContentLoaded", function () {
    const loginBtn = document.getElementById("u50");

    loginBtn.addEventListener("click", function (e) {
        e.preventDefault();
    });
    const emailInput = document.getElementById("u48_input");
    const passwordInput = document.getElementById("u49_input");

    loginBtn.addEventListener("click", async function (e) {
        e.preventDefault();

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!email || !password) {
            alert("请输入邮箱和密码");
            return;
        }

        try {
            let res = await fetch("http://127.0.0.1:5000/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            let data = await res.json();

            if (res.status === 200) {
                alert("登录成功！");
                window.location.href = "http://127.0.0.1:5000/";
                return;
            }

            const username = email.split("@")[0];

            let regRes = await fetch("http://127.0.0.1:5000/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password })
            });

            let regData = await regRes.json();

            if (regRes.status === 201) {
                alert("注册成功，正在登录...");

                let retry = await fetch("http://127.0.0.1:5000/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                if (retry.status === 200) {
                    window.location.href = "主页.html";
                }

            } else {
                alert(regData.message || "注册失败");
            }

        } catch (err) {
            alert("服务器连接失败");
        }
    });

});
