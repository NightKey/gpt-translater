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
            createBouble("remote", response);
            fetchStatistics();
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
    let newElement;
    if (className === "remote") {
        value.split("\n").forEach(element => {
            if (element.length === 0) return;
            newElement = createContainer(className, element);
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
        newElement = createContainer(className, value);
    }
    newElement.scrollIntoView();
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
    
    let userInput = document.getElementById("user_input");
    let sendButton = document.getElementById("send");
    userInput.onkeyup = (event) => { 
        if (event.code == 'Enter' || event.code == "NumpadEnter") {
            send();
        }
        sendButton.disabled = userInput.value == ""
    };
    
    userInput.onchange = (event) => {
        sendButton.disabled = userInput.value == ""
    }

    userInput.focus();
})