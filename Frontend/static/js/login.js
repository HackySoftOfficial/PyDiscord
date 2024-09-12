console.log("login.js loaded");

let socket;
let messageQueue = [];
let accessToken = null;

function connectWebSocket() {
    console.log("Attempting to connect WebSocket...");
    socket = new WebSocket('ws://127.0.0.1:8000/ws');
    
    socket.onopen = function(e) {
        console.log("WebSocket connection established successfully");
        sendQueuedMessages();
    };

    socket.onmessage = function(event) {
        console.log("WebSocket message received:", event.data);
        const data = JSON.parse(event.data);
        if (data.access_token) {
            accessToken = data.access_token;
            localStorage.setItem("token", accessToken);
            console.log("Login successful, access token received");
            window.location.href = '/dashboard';
        } else if (data.status === "error") {
            console.log("Error received:", data.detail);
            showErrorMessage(data.detail);
        } else if (data.status === "success") {
            console.log("Operation successful:", data);
        } else {
            console.log("Unhandled message:", data);
        }
    };

    socket.onerror = function(error) {
        console.error(`WebSocket Error:`, error);
    };

    socket.onclose = function(event) {
        console.log("WebSocket connection closed:", event);
    };
}

function sendQueuedMessages() {
    while (messageQueue.length > 0) {
        const message = messageQueue.shift();
        sendMessage(message);
    }
}

function sendMessage(message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        if (accessToken && message.command !== 'login' && message.command !== 'register') {
            message.payload.Bearer = accessToken;
        }
        socket.send(JSON.stringify(message));
        console.log("Message sent:", message);
    } else {
        console.log("WebSocket not ready, queueing message:", message);
        messageQueue.push(message);
        if (!socket || socket.readyState === WebSocket.CLOSED) {
            console.log("WebSocket closed, attempting to reconnect...");
            connectWebSocket();
        }
    }
}

function showErrorMessage(message) {
    let errorElement = document.getElementById('error-message');
    if (!errorElement) {
        console.log("Error message element not found, creating one");
        errorElement = document.createElement('div');
        errorElement.id = 'error-message';
        errorElement.style.color = 'red';
        errorElement.style.marginBottom = '10px';
        
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            // Insert the error message before the submit button
            const submitButton = loginForm.querySelector('button[type="submit"]');
            if (submitButton) {
                loginForm.insertBefore(errorElement, submitButton);
            } else {
                loginForm.appendChild(errorElement);
            }
        } else {
            console.error("Login form not found, appending error message to body");
            document.body.appendChild(errorElement);
        }
    }

    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

function setupLoginForm() {
    console.log("Setting up login form");
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        console.log('Login form found and setup');

        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Login form submitted');

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const loginData = {
                command: "login",
                payload: {
                    username: username,
                    password: password
                }
            };
            sendMessage(loginData);
        });
    } else {
        console.error("Login form not found. HTML elements present:", document.body.innerHTML);
    }
}

// Call connectWebSocket when the page loads
console.log("Current path:", window.location.pathname);
if (window.location.pathname !== '/login') {
    window.location.replace("/login");
} else {
    console.log("On login page, setting up WebSocket and form");
    document.addEventListener('DOMContentLoaded', () => {
        console.log("DOMContentLoaded event fired");
        connectWebSocket();
        setupLoginForm();
    });
}