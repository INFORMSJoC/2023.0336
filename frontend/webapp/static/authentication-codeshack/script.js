let ajax_form = document.querySelector(".ajax-form");
ajax_form.onsubmit = event => {
    event.preventDefault();
    if (document.querySelector(".g-recaptcha")) {
        grecaptcha.ready(() => {
            console.log(document.querySelector(".g-recaptcha").dataset.sitekey);
            grecaptcha.execute(document.querySelector(".g-recaptcha").dataset.sitekey, {action: 'submit'}).then(captcha_token => {
                process_form(ajax_form, captcha_token);
            });
        });
    } else {
        process_form(ajax_form)
    }
};
const process_form = (ajax_form, captcha_token) => {
    fetch(ajax_form.action, { method: 'POST', body: new FormData(ajax_form) }).then(response => response.text()).then(result => {
        if (result.toLowerCase().includes("success")) {
            window.location.href = "home";
        } else if (result.includes("tfa:")) {
            window.location.href = result.replace("tfa: ", "");
        } else if (result.toLowerCase().includes("autologin")) {
            window.location.href = "home";
        } else {
            document.querySelector(".msg").innerHTML = result.replace(/(?:\r\n|\r|\n)/g, '<br>');
        }
    });    
};