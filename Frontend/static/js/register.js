(function() {
    let socket;

    function connectWebSocket() {
        socket = new WebSocket('ws://127.0.0.1:8000/ws');

        socket.onopen = function(e) {
            console.log("WebSocket connection established");
        };

        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log("Received WebSocket message:", data);
            handleWebSocketMessage(data);
        };

        socket.onclose = function(event) {
            console.log("WebSocket connection closed");
            setTimeout(connectWebSocket, 5000);
        };

        socket.onerror = function(error) {
            console.error("WebSocket error:", error);
        };
    }

    function sendWebSocketMessage(command, payload) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const message = {
                command: command,
                payload: payload
            };

            console.log("Sending WebSocket message:", message);
            socket.send(JSON.stringify(message));
        } else {
            console.error("WebSocket is not open. Message not sent.");
            alert("Connection to server lost. Please refresh the page and try again.");
        }
    }

    function handleWebSocketMessage(data) {
        console.log("Handling WebSocket message:", data);
        if (data.status === 'success') {
            handleRegister(data);
        } else if (data.status === 'error') {
            alert('Registration failed: ' + data.detail);
        } else {
            console.log("Unrecognized message format:", data);
        }
    }

    function handleRegister(data) {
        if (data.status === 'success') {
            alert('Registration successful. Please log in.');
            window.location.href = '/login';
        } else {
            alert('Registration failed: ' + data.detail);
        }
    }

    function setupRegisterForm() {
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            console.log("Register form found");
            registerForm.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log("Register form submitted");
                const username = document.getElementById('username').value;
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                sendWebSocketMessage('register', { username, email, password });
            });
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        console.log("DOM fully loaded and parsed");
        connectWebSocket();
        setupRegisterForm();
    });

    // Expose necessary functions to the global scope
    window.sendWebSocketMessage = sendWebSocketMessage;
    window.handleRegister = handleRegister;
})();