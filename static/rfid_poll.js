// Dieses Skript pollt regelmäßig eine lokale API, um eine gescannte Karten-ID automatisch ins Formular einzutragen.
setInterval(async function() {
    try {
        let resp = await fetch('/rfid_scan');
        if (resp.ok) {
            let data = await resp.json();
            if (data.card_id) {
                let input = document.querySelector('input[name="card_id"]');
                if (input) {
                    input.value = data.card_id;
                    document.querySelector('form').submit();
                }
            }
        }
    } catch (e) {}
}, 1000); // alle 1 Sekunde
