

const checkButton = document.getElementById("checkButton");
const checkImage = document.getElementById("checkImage");
const problemId = document.getElementById("problemId");
const message = document.getElementById("message");

checkButton.addEventListener("click", async () => {
    const data = {
        problem_id: problemId.value,
        solving: editor.getValue()
    };

    try {
        const response = await fetch("/check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error("HTTP error " + response.status);
        }

        // display check answer
        const check_mes = await response.json();           
        // let check_mes = data.message || data;
        let ok = check_mes.slice(0, 4).indexOf("OK") != -1;
        message.style.color = ok ? "green" : "red";
        message.innerHTML = check_mes;
        checkImage.style.display = ok ? "inline" : "none";

    } catch (err) {
        console.error("Request failed:", err);
        message.innerHTML = "Помилка: " + err.message;
    }
});
