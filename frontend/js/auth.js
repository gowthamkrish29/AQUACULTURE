const API_BASE = 'http://localhost:5000/api';

// Login handling
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const alertBox = document.getElementById('login-alert');

        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.status === 'success') {
                localStorage.setItem('user', JSON.stringify(data.user));
                switch (data.user.role) {
                    case 'admin': window.location.href = 'admin.html'; break;
                    case 'labor': window.location.href = 'labor.html'; break;
                    case 'customer': window.location.href = 'shop.html'; break;
                    default:
                        alertBox.textContent = 'Role not recognized';
                        alertBox.style.display = 'block';
                }
            } else {
                alertBox.textContent = data.message || 'Login failed';
                alertBox.style.display = 'block';
            }
        } catch (err) {
            alertBox.textContent = 'Server connection error';
            alertBox.style.display = 'block';
        }
    });
}

// Registration handling
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('reg-username').value;
        const password = document.getElementById('reg-password').value;
        const alertBox = document.getElementById('register-alert');

        try {
            const response = await fetch(`${API_BASE}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role: 'customer' })
            });

            const data = await response.json();

            if (data.status === 'success') {
                alert('Registration successful! Please login.');
                toggleForms();
            } else {
                alertBox.textContent = data.message || 'Registration failed';
                alertBox.style.display = 'block';
            }
        } catch (err) {
            alertBox.textContent = 'Server connection error';
            alertBox.style.display = 'block';
        }
    });
}

function toggleForms() {
    const loginCard = document.getElementById('login-card');
    const registerCard = document.getElementById('register-card');
    if (loginCard.style.display === 'none') {
        loginCard.style.display = 'block';
        registerCard.style.display = 'none';
    } else {
        loginCard.style.display = 'none';
        registerCard.style.display = 'block';
    }
}
