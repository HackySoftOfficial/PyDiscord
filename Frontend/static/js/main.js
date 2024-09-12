let socket;
let token = localStorage.getItem('token');
let messageQueue = [];
let isConnected = false;

function connectWebSocket() {
    console.log("Attempting to connect WebSocket...");
    const wsUrl = token 
        ? `ws://127.0.0.1:8000/ws?token=${encodeURIComponent(token)}`
        : 'ws://127.0.0.1:8000/ws';
    
    console.log("WebSocket URL:", wsUrl);
    socket = new WebSocket(wsUrl);

    socket.onopen = function(e) {
        console.log("WebSocket connection established");
        isConnected = true;
        processMessageQueue();
        if (window.location.pathname === '/dashboard' && token) {
            console.log("On dashboard with token, requesting user info");
            sendWebSocketMessage('get_user', { user_id: 'me' });
        }
    };

    socket.onmessage = function(event) {
        if (event.data === undefined) {
            console.log("Received undefined WebSocket message");
            return;
        }

        console.log("Received WebSocket message:", event.data);
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error("Error parsing WebSocket message:", error);
        }
    };

    socket.onclose = function(event) {
        console.log("WebSocket connection closed. Code:", event.code, "Reason:", event.reason);
        isConnected = false;
        setTimeout(connectWebSocket, 5000);
    };

    socket.onerror = function(error) {
        console.error("WebSocket error:", error);
    };
}

function sendWebSocketMessage(command, payload) {
    const message = {
        command: command,
        payload: payload
    };

    if (isConnected) {
        console.log("Sending WebSocket message:", message);
        socket.send(JSON.stringify(message));
    } else {
        console.log("WebSocket not connected. Queueing message:", message);
        messageQueue.push(message); 
    }
}

function processMessageQueue() {
    console.log("Processing message queue. Queue length:", messageQueue.length);
    while (messageQueue.length > 0) {
        const message = messageQueue.shift();
        console.log("Sending queued message:", message);
        socket.send(JSON.stringify(message));
    }
}

function handleWebSocketMessage(data) {
    console.log("Handling WebSocket message:", data);
    if (data.status === 'success') {
        if (data.guilds) {
            console.log("Received guilds data");
            window.dispatchEvent(new CustomEvent('guilds-updated', { detail: data.guilds }));
        } else if (data.user) {
            console.log("Received user data");
            window.dispatchEvent(new CustomEvent('user-info-updated', { detail: data.user }));
        } else if (data.guild) {
            console.log("Received guild data");
            window.dispatchEvent(new CustomEvent('guild-info-updated', { detail: data.guild }));
        } else if (data.channels) {
            console.log("Received guild channels data");
            window.dispatchEvent(new CustomEvent('guild-channels-updated', { detail: data.channels }));
        } else if (data.channel) {
            console.log("Received channel data");
            window.dispatchEvent(new CustomEvent('channel-info-updated', { detail: data.channel }));
        } else if (data.messages) {
            console.log("Received messages data");
            window.dispatchEvent(new CustomEvent('messages-updated', { detail: data.messages }));
        } else if (data.users) {
            console.log("Received channel users data");
            window.dispatchEvent(new CustomEvent('channel-users-updated', { detail: data.users }));
        } else {
            console.log("Unhandled success message:", data);
        }
    } else if (data.status === 'error') {
        console.error("Received error message:", data);
        if (data.detail === "Invalid Token") {
            console.log("Invalid token detected, redirecting to login page");
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    } else {
        console.log("Unrecognized message format:", data);
    }
}

function handleLogin(data) {
    console.log("Handling login response:", data);
    if (data.access_token) {
        token = data.access_token;
        localStorage.setItem('token', token);
        console.log("Token stored in localStorage");
        console.log("Redirecting to dashboard");
        window.location.href = '/dashboard';
    } else {
        console.error("Login failed:", data.detail || 'Unknown error');
        alert('Login failed: ' + (data.detail || 'Unknown error'));
    }
}

function handleRegister(data) {
    console.log("Handling register response:", data);
    if (data.status === 'success') {
        console.log("Registration successful");
        alert('Registration successful. Please log in.');
        window.location.href = '/login';
    } else {
        console.error("Registration failed:", data.detail);
        alert('Registration failed: ' + data.detail);
    }
}

function handleError(data) {
    console.error("Error from server:", data.detail);
    if (data.detail === 'Unauthorized') {
        console.log("Unauthorized access, removing token and redirecting to login");
        localStorage.removeItem('token');
        window.location.href = '/login';
    } else {
        alert('Error: ' + data.detail);
    }
}

function updateUserInfo(user) {
    console.log("Updating user info:", user);
    const userNameElement = document.querySelector('.user-name');
    const userTagElement = document.querySelector('.user-tag');
    const userAvatarElement = document.querySelector('.user-avatar');
    const userArea = document.querySelector('.user-area');
    console.log(user);
    if (userNameElement) {
        userNameElement.textContent = user.username;
        console.log("Updated username:", user.username);
    } else {
        console.warn("User name element not found");
    }
    if (userTagElement) {
        userTagElement.textContent = '#' + user.id;
        console.log("Updated user tag:", '#' + user.id);
    } else {
        console.warn("User tag element not found");
    }
    if (userAvatarElement) {
        if (user.avatar_url) {
            userAvatarElement.src = user.avatar_url;
            userAvatarElement.style.display = 'block';
            console.log("Updated avatar URL:", user.avatar_url);
        } else {
            userAvatarElement.style.display = 'none';
            console.log("No avatar URL provided, hiding avatar element");
        }
        userAvatarElement.alt = `${user.username}'s avatar`;
    } else {
        console.warn("User avatar element not found");
    }
    
    console.log("User info updated in DOM");

    if (userArea) {
        userArea.onclick = function() {
            console.log("User area clicked, showing profile popup");
            showProfilePopup(user);
        };
        console.log("Click event listener added to user area");
    } else {
        console.warn("User area element not found");
    }
}

function showProfilePopup(user) {
    console.log("showProfilePopup called for user:", user);
    const existingPopup = document.querySelector('.profile-popup');
    if (existingPopup) {
        document.body.removeChild(existingPopup);
    }

    const popup = document.createElement('div');
    popup.className = 'profile-popup';
    popup.innerHTML = `
        <div class="card-container">
            <div class="card nitro-card">
                <div class="card-header">
                    <div class="banner-img" style="background: url(${user.banner_url || ''})"></div>
                </div>
                <div class="card-body">
                    <div class="profile-header">
                        <div class="profil-logo">
                            <img src="${user.avatar_url || ''}" />
                        </div>
                        <div class="badges-container">
                            <!-- Add badges here if needed -->
                        </div>
                    </div>
                    <div class="profile-body">
                        <div class="username">
                            ${user.username}<span>#${user.id}</span>
                            <div class="badge">Random guy</div>
                        </div>
                        <hr />
                        <div class="basic-infos">
                            <div class="category-title">About Me</div>
                            <p>${user.about_me || 'No bio yet.'}</p>
                        </div>
                        <div class="basic-infos">
                            <div class="category-title">Member Since</div>
                            <p>Jun 14, 2017</p>
                        </div>
                        <div class="roles">
                            <div class="category-title">Roles</div>
                            <div class="roles-list">
                                <!-- Add roles here if needed -->
                            </div>
                        </div>
                        <div class="note">
                            <div class="category-title">Note</div>
                            <textarea placeholder="Click to add a note"></textarea>
                        </div>
                        <div class="message">
                            <input type="text" placeholder="Message @${user.username}" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(popup);
    console.log("Profile popup added to DOM");

    const editButton = popup.querySelector('.edit-profile-button');
    if (editButton) {
        editButton.onclick = function(e) {
            console.log("Edit button clicked");
            e.stopPropagation();
            showEditProfileForm(user);
        };
    }

    document.addEventListener('click', function closePopup(e) {
        if (!popup.contains(e.target) && e.target !== document.querySelector('.user-area')) {
            console.log("Closing profile popup");
            document.body.removeChild(popup);
            document.removeEventListener('click', closePopup);
        }
    });
}

function showEditProfileForm(user) {
    const form = document.createElement('form');
    form.className = 'edit-profile-form';
    form.innerHTML = `
        <input type="text" id="edit-username" value="${user.username}" placeholder="Username">
        <input type="text" id="edit-avatar" value="${user.avatar_url || ''}" placeholder="Avatar URL">
        <input type="text" id="edit-banner" value="${user.banner_url || ''}" placeholder="Banner URL">
        <textarea id="edit-about" placeholder="About me">${user.about_me || ''}</textarea>
        <button type="submit">Save Changes</button>
    `;
    document.body.appendChild(form);

    form.onsubmit = function(e) {
        e.preventDefault();
        const updatedUser = {
            username: document.getElementById('edit-username').value,
            avatar_url: document.getElementById('edit-avatar').value,
            banner_url: document.getElementById('edit-banner').value,
            about_me: document.getElementById('edit-about').value
        };
        sendWebSocketMessage('update_user', updatedUser);
        document.body.removeChild(form);
    };
}

function updateGuildInfo(guild) {
    console.log("Updating guild info:", guild);
    const serverNameElement = document.querySelector('.server-header');
    if (serverNameElement) {
        serverNameElement.textContent = guild.name;
    }
    
    // Check if guild has channels, if not, request them separately
    if (guild.channels) {
        updateChannels(guild.channels);
    } else {
        console.log("Guild doesn't have channels, requesting them separately");
        sendWebSocketMessage('get_guild_channels', { guild_id: guild.id });
    }
}

function updateChannels(channels) {
    if (!Array.isArray(channels)) {
        console.error("Channels is not an array:", channels);
        return;
    }

    const channelList = document.querySelector('.channel-list');
    channelList.innerHTML = '';
    
    channels.forEach(channel => {
        const channelElement = document.createElement('div');
        channelElement.className = 'channel-item';
        channelElement.innerHTML = `<i class="fas fa-hashtag"></i> ${channel.name}`;
        channelElement.onclick = () => loadChannel(channel.id);
        channelList.appendChild(channelElement);
    });

    // If there are channels, load the first one by default
    if (channels.length > 0) {
        loadChannel(channels[0].id);
    }
}

function updateChannelInfo(channel) {
    console.log("Updating channel info:", channel);
    const channelNameElement = document.querySelector('.channel-name');
    if (channelNameElement) {
        channelNameElement.textContent = '#' + channel.name;
    }
}

function updateMessages(messages) {
    console.log("Updating messages:", messages);
    const messageArea = document.querySelector('.message-area');
    if (messageArea) {
        messageArea.innerHTML = '';
        messages.forEach(message => {
            const messageElement = createMessageElement(message);
            messageArea.appendChild(messageElement);
        });
    }
}

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.innerHTML = `
        <div class="message-avatar"></div>
        <div class="message-content">
            <div class="message-author">${message.author}</div>
            <div class="message-text">${message.content}</div>
        </div>
    `;
    return messageDiv;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed");
    console.log("Current page:", window.location.pathname);
    if (!isConnected) {
        connectWebSocket();
    }

    document.addEventListener('click', function(e) {
        console.log("Clicked element:", e.target);
    });
});

// Ensure these are available globally
window.sendWebSocketMessage = sendWebSocketMessage;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.updateUserInfo = updateUserInfo;
window.updateGuildInfo = updateGuildInfo;
window.updateChannelInfo = updateChannelInfo;
window.updateMessages = updateMessages;