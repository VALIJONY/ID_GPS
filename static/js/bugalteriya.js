document.addEventListener('DOMContentLoaded', function() {
    const yearSelect = document.querySelector('select[name="yil"]');
    
    yearSelect.addEventListener('change', function() {
        window.location.href = `?yil=${yearSelect.value}`;
    });

    // To'lov tugmalarini boshqarish
    document.querySelectorAll('.tolov-btn').forEach(button => {
        button.addEventListener('click', async function() {
            try {
                const response = await fetch('/update_bugalteriya/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        tolov_id: this.dataset.tolovId || null,
                        sotish_id: this.dataset.sotishId,
                        gps_id: this.dataset.gpsId,
                        oy: this.dataset.oy,
                        yil: currentYear,  // Using the variable passed from the template
                        type: this.dataset.type
                    })
                });

                const data = await response.json();
                
                if (!data.status) {
                    alert(data.message || 'Xatolik yuz berdi');
                    return;
                }

                // To'lov ID ni yangilash
                if (data.tolov_id) {
                    this.dataset.tolovId = data.tolov_id;
                    // Qo'shni tugmaning tolov_id ni ham yangilash
                    const siblingButton = this.dataset.type === 'abonent' ? 
                        this.parentElement.nextElementSibling.querySelector('.tolov-btn') :
                        this.parentElement.previousElementSibling.querySelector('.tolov-btn');
                    if (siblingButton) {
                        siblingButton.dataset.tolovId = data.tolov_id;
                    }
                }

                // Tugma holatini yangilash
                if (this.dataset.type === 'abonent') {
                    if (data.abonent_status) {
                        this.classList.remove('bg-red-100', 'text-red-800', 'hover:bg-red-200');
                        this.classList.add('bg-green-100', 'text-green-800', 'hover:bg-green-200');
                        this.textContent = "To'langan";
                    } else {
                        this.classList.remove('bg-green-100', 'text-green-800', 'hover:bg-green-200');
                        this.classList.add('bg-red-100', 'text-red-800', 'hover:bg-red-200');
                        this.textContent = "To'lanmagan";
                    }
                } else {  // sim karta
                    if (data.sim_status) {
                        this.classList.remove('bg-red-100', 'text-red-800', 'hover:bg-red-200');
                        this.classList.add('bg-green-100', 'text-green-800', 'hover:bg-green-200');
                        this.textContent = "To'langan";
                    } else {
                        this.classList.remove('bg-green-100', 'text-green-800', 'hover:bg-green-200');
                        this.classList.add('bg-red-100', 'text-red-800', 'hover:bg-red-200');
                        this.textContent = "To'lanmagan";
                    }
                }
                
            } catch (error) {
                console.error('Xatolik:', error);
                alert('Xatolik yuz berdi');
            }
        });
    });
});

// CSRF token olish uchun funksiya
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
