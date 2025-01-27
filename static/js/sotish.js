function formatNumber(input) {
    let value = input.value.replace(/\D/g, '');
    value = value.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    input.value = value;
}

function parseFormattedNumber(value) {
    return parseInt(value.replace(/\s/g, '') || 0);
}

function calculateQarz() {
    const summasi = parseFormattedNumber(document.getElementById('id_summasi').value);
    const naqd = parseFormattedNumber(document.getElementById('naqd').value);
    const bank_schot = parseFormattedNumber(document.getElementById('bank_schot').value);
    const qarz = summasi - (naqd + bank_schot);
    
    if (qarz < 0 || isNaN(summasi) || summasi === 0) {
        document.getElementById('karta').value = '0';
        if (qarz < 0) {
            alert("To'lov summasi umumiy summadan oshib ketdi!");
            document.getElementById('naqd').value = '0';
            document.getElementById('bank_schot').value = '0';
        }
    } else {
        document.getElementById('karta').value = qarz.toLocaleString('en-US').replace(/,/g, ' ');
    }
}

