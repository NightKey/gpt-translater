send = function() {
    const input_field = document.getElementById("user_input");
    let input = input_field.value;
    input_field.value = "";
    document.getElementById("send").disabled = true
    createBouble("user", input);

    $.ajax({
        url: "/translate",
        type: "POST",
        contentType: "text/plain",
        data: input,
        success: function(response) {
            console.log(response);
            createBouble("remote", response);
        }
    })
}

copy = function(value) {
    try {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(element);
        } else {
            const textArea = document.createElement("textarea");
            textArea.innerHTML = value;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand("copy");
            document.body.removeChild(textArea);
        }
        return true;
    } catch {
        return false;
    }
}

createContainer = function(className, value) {
    const selector = document.getElementById("output");
    const newElement = document.createElement("div");
    newElement.id = "message";
    newElement.classList = [className];
    newElement.textContent = value;
    selector.appendChild(newElement);
    return newElement
}

createBouble = function(className, value) {
    if (className === "remote") {
        value.split("\n").forEach(element => {
            if (element.length === 0) return;
            const newElement = createContainer(className, element);
            newElement.onclick = () => {
                if (copy(element)) {
                    const tooltip = document.getElementById("tooltip");
                    tooltip.classList.add("visible");
                    setTimeout(() => {
                        tooltip.classList.remove("visible");
                    }, 500);
                }
            }
        });
    } else {
        createContainer(className, value);
    }
}

fetchStatistics = function() {
    $.ajax({
        url: "/stats",
        type: "GET",
        contentType: "text/plain",
        success: function(response) {
            console.log(response);
            const stats = document.getElementById("stats");
            stats.innerHTML = response;
        }
    })
}

$(document).ready(function() {
    document.getElementById("send").onclick = () => {
        console.log("Send clicked!");
        send();
    };
    
   document.getElementById("user_input").onkeyup = (event) => { 
        console.log(event.code);
        if (event.code == 'Enter' || event.code == "NumpadEnter") {
            send();
        }
        document.getElementById("send").disabled = document.getElementById("user_input").value == ""
    };

    document.getElementById("user_input").focus();
})