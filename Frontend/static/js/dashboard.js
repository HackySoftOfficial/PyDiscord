let socket;
let token = localStorage.getItem('token');
let currentGuildId = null;
let currentChannelId = null;
let currentMessagePage = 1;
let isLoadingMessages = false;
let messageQueue = [];
let isWebSocketReady = false;

let initialDataLoaded = false;

function connectWebSocket() {
    console.log("Attempting to connect WebSocket...");
    const wsUrl = token ? `ws://127.0.0.1:8000/ws?token=${encodeURIComponent(token)}` : 'ws://127.0.0.1:8000/ws';
    
    socket = new WebSocket(wsUrl);

    socket.onopen = function(e) {
        console.log("WebSocket connection established");
        isWebSocketReady = true;
        sendQueuedMessages();
        if (!token) {
            console.log("No token found, user is unauthenticated");
            showLoginRegisterOptions();
        } else if (!initialDataLoaded) {
            setupInitialData();
        }
    };

    socket.onmessage = function(event) {
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
        setTimeout(connectWebSocket, 5000);
    };

    socket.onerror = function(error) {
        console.error("WebSocket error:", error);
    };
}

function sendWebSocketMessage(command, payload) {
    if (isWebSocketReady) {
        socket.send(JSON.stringify({command, payload}));
    } else {
        messageQueue.push({command, payload});
    }
}

function sendQueuedMessages() {
    while (messageQueue.length > 0) {
        const message = messageQueue.shift();
        socket.send(JSON.stringify(message));
    }
}

function handleWebSocketMessage(data) {
    console.log("Handling WebSocket message:", data);
    if (data.status === "error" && data.detail === "Invalid token") {
        localStorage.removeItem('token');
        token = null;
        window.location.replace("/login");
        return;
    }
    if (data.status === "error") {
        console.error("Error:", data.detail);
        return;
    }

    switch (data.type) {
        case "new_message":
            console.log("Received new message:", data.data);
            addNewMessage(data.data);
            break;
        case "user_info":
            updateUserInfo(data.data);
            break;
        case "guilds_list":
            updateGuilds(data.data);
            break;
        case "guild_channels":
            updateChannels(data.data, data.guild_id);
            break;
        case "guild_created":
            handleGuildCreated(data.data);
            break;
        case "guild_deleted":
            removeGuild(data.guild_id);
            break;
        case "channel_created":
            addNewChannel(data.data);
            break;
        case "channel_deleted":
            removeChannel(data.channel_id);
            break;
        case "guild_member_added":
            updateGuildMembers(data.guild_id, data.user);
            break;
        case "guild_member_removed":
            removeGuildMember(data.guild_id, data.user_id);
            break;
        case "status_updated":
            updateUserStatus(data.user_id, data.new_status);
            break;
        case "invite_created":
            alert(`Invite created! Code: ${data.invite_code}`);
            break;
        case "guild_joined":
            handleGuildJoined(data.guild);
            break;
        case "guild_deleted":
            removeGuild(data.guild_id);
            break;
        case "friend_added":
            handleFriendAdded(data.friend);
            break;
        case "guild_joined":
            handleGuildJoined(data.guild);
            break;
        case "guild_data":
            handleGuildData(data);
            break;
        default:
            if (data.status === "success") {
                handleSuccessMessage(data);
            } else {
                console.log("Unhandled message type:", data);
            }
    }
}

function handleSuccessMessage(data) {
    if (data.user) {
        updateUserInfo(data.user);
    }
    if (data.guilds) {
        updateGuilds(data.guilds);
    }
    if (data.guild) {
        updateGuildInfo(data.guild);
    }
    if (data.channels) {
        updateChannels(data.channels, data.guild_id);
    }
    if (data.messages) {
        updateMessages(data.messages, data.page > 1);
    }
    if (data.message) {
        addNewMessage(data.message);
    }
    if (data.channel) {
        updateChannelInfo(data.channel);
    }
    if (data.users) {
        updateChannelUsers(data.users);
    }
}

function updateUserInfo(user) {
    console.log("Updating user info:", user);
    currentUserId = user.id;
    const userNameElement = document.querySelector('.user-name');
    const userTagElement = document.querySelector('.user-tag');
    const userAvatarElement = document.querySelector('.user-avatar');
    
    if (userNameElement && userTagElement && userAvatarElement) {
        userNameElement.textContent = user.username;
        userTagElement.textContent = '#' + user.id;
        userAvatarElement.src = user.avatar_url || '/static/images/default_avatar.png';
        userAvatarElement.onerror = function() {
            this.src = 'https://via.placeholder.com/32'; // Fallback to a placeholder image
        };
    }
}

function updateGuilds(guilds, isSingleAddition = false) {
    console.log("Updating guilds:", guilds);
    const serversSidebar = document.querySelector('.servers-sidebar');
    
    if (!isSingleAddition) {
        // Clear existing guild icons, but keep the home icon and create guild button
        const homeIcon = serversSidebar.querySelector('#home-icon');
        const createGuildBtn = serversSidebar.querySelector('#create-guild-btn');
        serversSidebar.innerHTML = '';
        serversSidebar.appendChild(homeIcon);
        
        guilds.forEach(guild => {
            const guildElement = createGuildElement(guild);
            serversSidebar.insertBefore(guildElement, createGuildBtn);
        });
    } else {
        // It's a single guild addition (e.g., from joining), so just add it
        const createGuildBtn = serversSidebar.querySelector('#create-guild-btn');
        const guildElement = createGuildElement(guilds[0]);
        serversSidebar.insertBefore(guildElement, createGuildBtn);
    }

    // If there are guilds and no current guild is selected, load the first one by default
    if (guilds.length > 0 && !currentGuildId) {
        loadGuild(guilds[0].id);
    }
}

function loadGuild(guildId) {
    if (currentGuildId !== guildId) {
        console.log("Loading guild:", guildId);
        sendWebSocketMessage('get_guild', { guild_id: guildId });
    }
}

function updateGuildInfo(guild) {
    console.log("Updating guild info:", guild);
    currentGuildId = guild.id;
    showGuildContent(guild.name);
    
    if (guild.channels) {
        updateChannels(guild.channels, guild.id);
    } else {
        // If channels are not included in the guild info, fetch them separately
        sendWebSocketMessage('get_guild_channels', { guild_id: guild.id });
    }
}

function updateChannels(channels, guildId) {
    if (!Array.isArray(channels)) {
        console.error("Channels is not an array:", channels);
        return;
    }

    const channelOrUserList = document.getElementById('channel-or-user-list');
    channelOrUserList.innerHTML = '';
    
    if (channels.length === 0) {
        const noChannelsMessage = document.createElement('div');
        noChannelsMessage.textContent = 'No channels available';
        noChannelsMessage.className = 'no-channels-message';
        channelOrUserList.appendChild(noChannelsMessage);
    } else {
        channels.forEach(channel => {
            const channelElement = createChannelElement(channel);
            channelOrUserList.appendChild(channelElement);
        });
    }

    // Add "Create Channel" button
    const createChannelButton = document.createElement('button');
    createChannelButton.textContent = 'Create Channel';
    createChannelButton.onclick = createNewChannel;
    channelOrUserList.appendChild(createChannelButton);

    // If there are channels, load the first one by default
    if (channels.length > 0) {
        loadChannel(channels[0].id);
    } else {
        // Clear message area if there are no channels
        clearMessageArea();
    }
}

function createNewChannel() {
    const channelName = prompt("Enter new channel name:");
    if (channelName) {
        sendWebSocketMessage('create_channel', { guild_id: currentGuildId, name: channelName });
    }
}

function deleteChannel(channelId) {
    if (confirm("Are you sure you want to delete this channel?")) {
        sendWebSocketMessage('delete_channel', { channel_id: channelId });
    }
}

function loadChannel(channelId) {
    console.log("Loading channel:", channelId);
    if (currentChannelId !== channelId) {
        currentChannelId = channelId;
        console.log("Current channel ID set to:", currentChannelId);
        currentMessagePage = 1;
        fetchMessages(currentMessagePage);
        fetchChannelUsers();
        
        // Update channel name in the header
        const channel = document.querySelector(`.channel-item[data-channel-id="${channelId}"]`);
        if (channel) {
            updateChannelInfo({ name: channel.textContent.trim() });
        }
    }
}

function updateChannelInfo(channel) {
    const channelNameElement = document.querySelector('.channel-name');
    if (channelNameElement) {
        channelNameElement.textContent = '# ' + channel.name;
    }
}

function updateMessages(messageData, append = false) {
    if (!Array.isArray(messageData)) {
        console.error("Invalid message data:", messageData);
        return;
    }

    const messages = messageData;
    const messageArea = document.querySelector('.message-area');
    
    if (!append) {
        messageArea.innerHTML = '';
    }
    
    // Create a document fragment to hold the new messages
    const fragment = document.createDocumentFragment();
    
    messages.forEach(message => {
        const messageElement = createMessageElement(message);
        fragment.appendChild(messageElement);
    });
    
    if (append) {
        // If appending (loading older messages), insert at the beginning
        messageArea.insertBefore(fragment, messageArea.firstChild);
    } else {
        // If not appending (initial load), add to the end
        messageArea.appendChild(fragment);
        messageArea.scrollTop = messageArea.scrollHeight;
    }
    
    isLoadingMessages = false;
}

function createMessageElement(message) {
    console.log("Creating message element:", message);
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.innerHTML = `
        <img class="message-avatar" src="${message.author.avatar_url || '/static/images/default_avatar.png'}" alt="${message.author.username}'s avatar">
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">${message.author.username}</span>
                <span class="message-timestamp">${new Date(message.timestamp).toLocaleString()}</span>
            </div>
            <div class="message-text">${message.content}</div>
        </div>
    `;
    return messageDiv;
}

function updateChannelUsers(users) {
    const membersList = document.querySelector('.members-list');
    membersList.innerHTML = '';
    
    const onlineUsers = users.filter(user => user.status === 'online');
    const offlineUsers = users.filter(user => user.status !== 'online');
    
    if (onlineUsers.length > 0) {
        const onlineCategory = document.createElement('div');
        onlineCategory.className = 'members-category';
        onlineCategory.textContent = 'Online - ' + onlineUsers.length;
        membersList.appendChild(onlineCategory);
        onlineUsers.forEach(user => addUserElement(user, membersList));
    }
    
    if (offlineUsers.length > 0) {
        const offlineCategory = document.createElement('div');
        offlineCategory.className = 'members-category';
        offlineCategory.textContent = 'Offline - ' + offlineUsers.length;
        membersList.appendChild(offlineCategory);
        offlineUsers.forEach(user => addUserElement(user, membersList));
    }
}

function addUserElement(user, container) {
    const userElement = document.createElement('div');
    userElement.className = 'member-item';
    userElement.setAttribute('data-user-id', user.id);
    userElement.innerHTML = `
        <div class="avatar-container">
            <img class="member-avatar" src="${user.avatar_url || '/static/images/default_avatar.png'}" alt="${user.username}'s avatar">
            <div class="status-indicator status-${user.status}"></div>
        </div>
        <div class="member-name">${user.nickname || user.username}#${user.id}</div>
    `;
    container.appendChild(userElement);
}

function fetchMessages(page = 1) {
    if (currentChannelId) {
        isLoadingMessages = true;
        sendWebSocketMessage('get_messages', { channel_id: currentChannelId, page: page });
    }
}

function fetchChannelUsers() {
    if (currentChannelId) {
        sendWebSocketMessage('get_channel_users', { channel_id: currentChannelId });
    }
}

function setupMessageAreaScroll() {
    const messageArea = document.querySelector('.message-area');
    messageArea.addEventListener('scroll', function() {
        if (messageArea.scrollTop === 0 && !isLoadingMessages) {
            currentMessagePage++;
            fetchMessages(currentMessagePage);
        }
    });
}

function setupInitialData() {
    if (!initialDataLoaded) {
        sendWebSocketMessage('get_user', { user_id: 'me' });
        sendWebSocketMessage('list_user_guilds', {});
        initialDataLoaded = true;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard DOM content loaded");
    if (token) {
        connectWebSocket();
    } else {
        console.log("No token found, redirecting to login page");
        window.location.href = '/login';
    }

    setupMessageInput();
    setupMessageAreaScroll();
    setupButtons();
    showHomePage(); // Show home page by default
});

function setupMessageInput() {
    const messageInput = document.querySelector('.message-input');
    
    if (messageInput) {
        messageInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    }
}

function sendMessage() {
    const messageInput = document.querySelector('.message-input');
    const content = messageInput.value.trim();
    if (content && currentChannelId && currentGuildId) {
        sendWebSocketMessage('send_message', { 
            channel_id: currentChannelId, 
            guild_id: currentGuildId,
            content 
        });
        messageInput.value = '';
    }
}

function createChannelElement(channel) {
    const channelElement = document.createElement('div');
    channelElement.className = 'channel-item';
    channelElement.setAttribute('data-channel-id', channel.id);
    channelElement.innerHTML = `
        <i class="fas fa-hashtag"></i> ${channel.name}
        <button class="delete-channel" data-channel-id="${channel.id}">X</button>
    `;
    channelElement.querySelector('.delete-channel').onclick = (e) => {
        e.stopPropagation();
        deleteChannel(channel.id);
    };
    channelElement.onclick = () => loadChannel(channel.id);
    return channelElement;
}

function createGuildElement(guild) {
    const guildElement = document.createElement('div');
    guildElement.className = 'server-icon';
    guildElement.textContent = guild.name[0].toUpperCase();
    guildElement.setAttribute('data-guild-id', guild.id);
    guildElement.onclick = () => loadGuild(guild.id);
    return guildElement;
}

function addNewMessage(message) {
    console.log("Adding new message:", message);
    if (message.channel_id === currentChannelId) {
        const messageElement = createMessageElement(message);
        const messageArea = document.querySelector('.message-area');
        // Append the new message at the end of the message area
        messageArea.appendChild(messageElement);
        // Scroll to the bottom of the message area
        messageArea.scrollTop = messageArea.scrollHeight;
    } else {
        // Optionally, update UI to show there's a new message in another channel
        console.log(`New message in channel ${message.channel_id}`);
    }
}

function addNewChannel(channel) {
    if (channel.guild_id === currentGuildId) {
        const channelElement = createChannelElement(channel);
        const channelList = document.querySelector('.channel-list');
        channelList.appendChild(channelElement);
    }
}

function removeChannel(channelId) {
    const channelElement = document.querySelector(`.channel-item[data-channel-id="${channelId}"]`);
    if (channelElement) {
        channelElement.remove();
    }
}

function addNewGuild(guild) {
    const guildElement = createGuildElement(guild);
    const serversSidebar = document.querySelector('.servers-sidebar');
    const createGuildBtn = document.getElementById('create-guild-btn');
    
    // Check if the guild already exists in the sidebar
    const existingGuild = serversSidebar.querySelector(`[data-guild-id="${guild.id}"]`);
    if (!existingGuild) {
        serversSidebar.insertBefore(guildElement, createGuildBtn);
    }
}

function removeGuild(guildId) {
    const guildElement = document.querySelector(`.server-icon[data-guild-id="${guildId}"]`);
    if (guildElement) {
        guildElement.remove();
    }
    if (currentGuildId === guildId) {
        currentGuildId = null;
        currentChannelId = null;
        updateChannels([]);
        updateMessages([]);
    }
}

function updateGuildMembers(guildId, user) {
    if (currentGuildId === guildId) {
        addUserElement(user, document.querySelector('.members-list'));
    }
}

function removeGuildMember(guildId, userId) {
    if (currentGuildId === guildId) {
        const memberElement = document.querySelector(`.member-item[data-user-id="${userId}"]`);
        if (memberElement) {
            memberElement.remove();
        }
    }
}

function showLoginRegisterOptions() {
    // Implement this function to show login/register UI to the user
    // For example, you could redirect to a login page or show a modal
    console.log("Showing login/register options");
    window.location.href = '/login';
}

function updateUserStatus(userId, newStatus) {
    const userElement = document.querySelector(`.member-item[data-user-id="${userId}"]`);
    if (userElement) {
        const statusIndicator = userElement.querySelector('.status-indicator');
        statusIndicator.className = `status-indicator status-${newStatus}`;
        
        // Move the user to the correct category (online/offline)
        const membersList = document.querySelector('.members-list');
        const onlineCategory = membersList.querySelector('.members-category:first-child');
        const offlineCategory = membersList.querySelector('.members-category:last-child');
        
        if (newStatus === 'online') {
            if (offlineCategory) {
                membersList.insertBefore(userElement, onlineCategory.nextSibling);
            }
        } else {
            if (onlineCategory) {
                membersList.appendChild(userElement);
            }
        }
        
        // Update category counts
        updateMembersCategoryCount();
    }
    
    // Update user's own status in the dropdown if it's the current user
    if (userId === currentUserId) {
        document.getElementById('status-select').value = newStatus;
    }
}

function updateMembersCategoryCount() {
    const membersList = document.querySelector('.members-list');
    const categories = membersList.querySelectorAll('.members-category');
    
    categories.forEach(category => {
        const status = category.textContent.split(' - ')[0].toLowerCase();
        const count = membersList.querySelectorAll(`.member-item .status-indicator.status-${status}`).length;
        category.textContent = `${status.charAt(0).toUpperCase() + status.slice(1)} - ${count}`;
    });
}

function setupButtons() {
    document.getElementById('create-guild-btn').addEventListener('click', showCreateGuildModal);
    document.getElementById('create-guild-submit').addEventListener('click', createGuild);
    document.getElementById('create-guild-cancel').addEventListener('click', hideCreateGuildModal);
    document.getElementById('home-icon').addEventListener('click', showHomePage);
    document.getElementById('add-friend-btn').addEventListener('click', addFriend);
    document.getElementById('join-invite-btn').addEventListener('click', joinGuild);
    document.getElementById('status-select').addEventListener('change', updateStatus);
}

function showCreateGuildModal() {
    document.getElementById('create-guild-modal').style.display = 'block';
}

function hideCreateGuildModal() {
    document.getElementById('create-guild-modal').style.display = 'none';
}

function createGuild() {
    const guildName = document.getElementById('guild-name').value;
    if (guildName) {
        sendWebSocketMessage('create_guild', { name: guildName });
        hideCreateGuildModal();
        document.getElementById('guild-name').value = ''; // Clear the input field
    }
}

function showHomePage() {
    currentGuildId = null;
    currentChannelId = null;
    document.getElementById('home-page').style.display = 'block';
    document.getElementById('guild-content').style.display = 'none';
    document.getElementById('server-header').textContent = 'Home';
    updateFriendsList();
}

function updateFriendsList() {
    const channelOrUserList = document.getElementById('channel-or-user-list');
    channelOrUserList.innerHTML = '<div class="friends-list-placeholder">Friends list will be implemented later</div>';
}

function showGuildContent(guildName) {
    document.getElementById('home-page').style.display = 'none';
    document.getElementById('guild-content').style.display = 'flex';
    document.getElementById('guild-content').style.flexDirection = 'column';
    document.getElementById('server-header').textContent = guildName;
    // The channels will be populated by the updateChannels function when a guild is loaded
}

function addFriend() {
    const username = document.getElementById('friend-username').value;
    if (username) {
        sendWebSocketMessage('add_friend', { username: username });
        document.getElementById('friend-username').value = '';
    }
}

function joinGuild() {
    const inviteCode = document.getElementById('invite-code').value;
    if (inviteCode) {
        sendWebSocketMessage('join_guild', { invite_code: inviteCode });
        document.getElementById('invite-code').value = '';
    }
}

function updateStatus() {
    const status = document.getElementById('status-select').value;
    sendWebSocketMessage('set_status', { status: status });
}

function handleGuildCreated(guild) {
    addNewGuild(guild);
    loadGuild(guild.id);
}

function handleFriendAdded(friend) {
    console.log("Friend added:", friend);
    // Implement UI update for added friend
    // This could involve updating the friends list on the home page
}

function handleGuildJoined(guild) {
    console.log("Joined guild:", guild);
    updateGuilds([guild], true); // Pass true to indicate it's a single guild addition
    loadGuild(guild.id);
}

function handleGuildData(data) {
    updateGuildInfo(data.guild);
    updateChannels(data.channels, data.guild.id);
    updateGuildMembers(data.members);
}

function updateGuildMembers(members) {
    console.log("Updating guild members:", members);
    const membersList = document.querySelector('.members-list');
    membersList.innerHTML = '';
    
    const onlineMembers = members.filter(member => member.status === 'online');
    const offlineMembers = members.filter(member => member.status !== 'online');
    
    if (onlineMembers.length > 0) {
        const onlineCategory = document.createElement('div');
        onlineCategory.className = 'members-category';
        onlineCategory.textContent = `Online - ${onlineMembers.length}`;
        membersList.appendChild(onlineCategory);
        onlineMembers.forEach(member => addUserElement(member, membersList));
    }
    
    if (offlineMembers.length > 0) {
        const offlineCategory = document.createElement('div');
        offlineCategory.className = 'members-category';
        offlineCategory.textContent = `Offline - ${offlineMembers.length}`;
        membersList.appendChild(offlineCategory);
        offlineMembers.forEach(member => addUserElement(member, membersList));
    }
}

function addUserElement(user, container) {
    const userElement = document.createElement('div');
    userElement.className = 'member-item';
    userElement.setAttribute('data-user-id', user.id);
    userElement.innerHTML = `
        <div class="avatar-container">
            <img class="member-avatar" src="${user.avatar_url || '/static/images/default_avatar.png'}" alt="${user.username}'s avatar">
            <div class="status-indicator status-${user.status}"></div>
        </div>
        <div class="member-name">${user.display_name || user.username}</div>
    `;
    container.appendChild(userElement);
}

function clearMessageArea() {
    const messageArea = document.querySelector('.message-area');
    messageArea.innerHTML = '';
    const channelNameElement = document.querySelector('.channel-name');
    if (channelNameElement) {
        channelNameElement.textContent = 'No channel selected';
    }
}

let currentUserId = null;